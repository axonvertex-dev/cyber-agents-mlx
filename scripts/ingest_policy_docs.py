#!/usr/bin/env python3

import json
import math
import os
import re
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from pypdf import PdfReader


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "embeddinggemma:300m-qat-q8_0")

RAW_DIR = Path("/app/policy_docs/raw")
INDEX_DIR = Path("/app/policy_docs/index")
CHUNKS_PATH = INDEX_DIR / "policy_chunks.jsonl"
VECTORS_PATH = INDEX_DIR / "policy_vectors.jsonl"
MANIFEST_PATH = INDEX_DIR / "policy_manifest.json"


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = text.replace("\u00ad", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_./:-]+", text.lower())


def should_ingest_policy_file(path: Path) -> bool:
    """
    Only ingest actual policy source documents.

    README.md files in policy_docs/raw are human instructions for the repo and
    must not become retrieval context.
    """
    if not path.is_file():
        return False

    if path.stat().st_size == 0:
        return False

    ignored_names = {
        "README.md",
        ".gitkeep",
    }

    if path.name in ignored_names:
        return False

    return path.suffix.lower() in {".pdf", ".md", ".txt"}


def source_policy_family(name: str) -> str:
    s = name.lower()

    if "gdpr" in s or "2016-679" in s or "32016r0679" in s:
        return "GDPR"

    if "gpai" in s or "generalpurpose" in s or "general-purpose" in s:
        return "EU_AI_ACT_GPAI_GUIDANCE"

    if "ai-act" in s or "2024-1689" in s or "202401689" in s:
        return "EU_AI_ACT"

    if "internal" in s:
        return "INTERNAL_POLICY"

    return "UNKNOWN"


def detect_section_title(text: str) -> str:
    lines = [x.strip() for x in text.splitlines() if x.strip()]

    for line in lines[:10]:
        if re.match(r"^(Article|CHAPTER|SECTION|ANNEX|Recital|\([0-9]+\))", line, re.I):
            return line[:180]
        if line.startswith("#"):
            return line.strip("# ").strip()[:180]

    return lines[0][:180] if lines else ""


def read_pdf(path: Path) -> List[Dict[str, Any]]:
    pages = []

    if path.stat().st_size == 0:
        print(f"WARNING: skipping empty PDF {path.name}")
        return []

    reader = PdfReader(str(path))

    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        text = clean_text(text)

        if text:
            pages.append({
                "source": path.name,
                "source_type": "pdf",
                "policy_family": source_policy_family(path.name),
                "page": i,
                "text": text,
            })

    return pages


def read_text(path: Path) -> List[Dict[str, Any]]:
    if path.stat().st_size == 0:
        print(f"WARNING: skipping empty text file {path.name}")
        return []

    text = clean_text(path.read_text(errors="replace"))

    if not text:
        return []

    return [{
        "source": path.name,
        "source_type": path.suffix.lower().lstrip(".") or "text",
        "policy_family": source_policy_family(path.name),
        "page": None,
        "text": text,
    }]


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 180) -> List[str]:
    text = clean_text(text)

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]

        if end < len(text):
            boundary = max(
                chunk.rfind("\nArticle "),
                chunk.rfind("\nCHAPTER "),
                chunk.rfind("\nSECTION "),
                chunk.rfind("\nANNEX "),
                chunk.rfind(". "),
                chunk.rfind("\n"),
            )

            if boundary > int(chunk_size * 0.50):
                chunk = chunk[:boundary + 1]
                end = start + boundary + 1

        chunk = clean_text(chunk)

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(0, end - overlap)

    return chunks


def embed_batch(texts: List[str]) -> List[List[float]]:
    payload = {
        "model": EMBED_MODEL,
        "input": texts,
    }

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/embed",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))

    embeddings = body.get("embeddings")

    if not embeddings:
        raise RuntimeError(f"No embeddings returned: {body}")

    return embeddings


def main():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(
        f for f in RAW_DIR.iterdir()
        if should_ingest_policy_file(f)
    )

    if not files:
        print(f"ERROR: no non-empty policy files found in {RAW_DIR}")
        sys.exit(1)

    print("Policy embedding ingestion")
    print("=" * 80)
    print(f"Ollama base URL: {OLLAMA_BASE_URL}")
    print(f"Embedding model: {EMBED_MODEL}")
    print(f"Raw dir: {RAW_DIR}")
    print(f"Files: {len(files)}")

    all_chunks = []

    for path in files:
        print(f"\nReading: {path.name}")

        if path.suffix.lower() == ".pdf":
            pages = read_pdf(path)
        else:
            pages = read_text(path)

        print(f"Pages/sections extracted: {len(pages)}")

        for page in pages:
            chunks = chunk_text(page["text"])
            print(f"  source={page['source']} page={page['page']} chunks={len(chunks)}")

            safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", path.stem)

            for idx, chunk in enumerate(chunks):
                chunk_id = f"{safe_stem}_p{page['page'] or 0}_c{idx}"
                tokens = tokenize(chunk)

                all_chunks.append({
                    "chunk_id": chunk_id,
                    "source": page["source"],
                    "source_type": page["source_type"],
                    "policy_family": page["policy_family"],
                    "page": page["page"],
                    "chunk_index": idx,
                    "section_title": detect_section_title(chunk),
                    "char_count": len(chunk),
                    "token_count": len(tokens),
                    "text": chunk,
                })

    if not all_chunks:
        print("ERROR: no chunks extracted")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(f"Total chunks: {len(all_chunks)}")

    batch_size = 16
    vector_rows = []
    started = time.time()

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        texts = [row["text"] for row in batch]

        print(f"Embedding chunks {i + 1}-{i + len(batch)} / {len(all_chunks)}")
        embeddings = embed_batch(texts)

        for row, embedding in zip(batch, embeddings):
            vector_rows.append({
                **row,
                "embedding_model": EMBED_MODEL,
                "embedding_dim": len(embedding),
                "embedding": embedding,
                "bm25_tokens": dict(Counter(tokenize(row["text"]))),
            })

    with CHUNKS_PATH.open("w") as f:
        for row in all_chunks:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with VECTORS_PATH.open("w") as f:
        for row in vector_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    families = Counter(row["policy_family"] for row in all_chunks)
    sources = Counter(row["source"] for row in all_chunks)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ollama_base_url": OLLAMA_BASE_URL,
        "embedding_model": EMBED_MODEL,
        "embedding_dimension": vector_rows[0]["embedding_dim"] if vector_rows else 0,
        "raw_dir": str(RAW_DIR),
        "chunks_path": str(CHUNKS_PATH),
        "vectors_path": str(VECTORS_PATH),
        "document_count": len(files),
        "chunk_count": len(all_chunks),
        "policy_families": dict(families),
        "sources": dict(sources),
        "hybrid_retrieval": {
            "embedding": True,
            "bm25_style_keyword_score": True
        },
        "elapsed_seconds": round(time.time() - started, 3),
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    print("\nPolicy ingestion complete")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
