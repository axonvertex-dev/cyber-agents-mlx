#!/usr/bin/env python3

import json
import math
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "embeddinggemma:300m-qat-q8_0")
INDEX_PATH = Path(os.getenv("POLICY_INDEX_PATH", "/app/policy_docs/index/policy_vectors.jsonl"))

K1 = 1.5
B = 0.75


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_./:-]+", text.lower())


def cosine(a: List[float], b: List[float]) -> float:
    dot = 0.0
    na = 0.0
    nb = 0.0

    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y

    if na == 0 or nb == 0:
        return 0.0

    return dot / (math.sqrt(na) * math.sqrt(nb))


def embed_query(query: str) -> List[float]:
    payload = {
        "model": EMBED_MODEL,
        "input": query,
    }

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/embed",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        body = json.loads(response.read().decode("utf-8"))

    return body["embeddings"][0]


def load_rows() -> List[Dict[str, Any]]:
    if not INDEX_PATH.exists():
        print(f"ERROR: missing index: {INDEX_PATH}")
        sys.exit(1)

    rows = []
    with INDEX_PATH.open("r") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    return rows


def bm25_score(
    query_tokens: List[str],
    row: Dict[str, Any],
    avg_len: float,
    doc_count: int,
    df_map: Dict[str, int],
) -> float:
    freqs = row.get("bm25_tokens", {})
    doc_len = max(1, row.get("token_count", 1))

    score = 0.0

    for token in query_tokens:
        tf = freqs.get(token, 0)
        if tf == 0:
            continue

        df = df_map.get(token, 0)
        idf = math.log(1 + ((doc_count - df + 0.5) / (df + 0.5)))
        denom = tf + K1 * (1 - B + B * (doc_len / avg_len))
        score += idf * ((tf * (K1 + 1)) / denom)

    return score


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/search_policy_index.py 'your query' [top_k]")
        sys.exit(1)

    query = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    rows = load_rows()

    if not rows:
        print(f"ERROR: no rows in {INDEX_PATH}")
        sys.exit(1)

    print(f"Query: {query}")
    print(f"Rows: {len(rows)}")
    print(f"Embedding model: {EMBED_MODEL}")
    print()

    query_embedding = embed_query(query)
    query_tokens = tokenize(query)

    doc_count = len(rows)
    avg_len = sum(max(1, row.get("token_count", 1)) for row in rows) / doc_count

    df_map = {}
    for row in rows:
        for token in row.get("bm25_tokens", {}).keys():
            df_map[token] = df_map.get(token, 0) + 1

    raw = []

    for row in rows:
        emb_score = cosine(query_embedding, row["embedding"])
        key_score = bm25_score(query_tokens, row, avg_len, doc_count, df_map)
        raw.append((emb_score, key_score, row))

    max_key = max((x[1] for x in raw), default=0.0) or 1.0

    scored = []
    for emb_score, key_score, row in raw:
        norm_key = key_score / max_key
        hybrid = (0.72 * emb_score) + (0.28 * norm_key)

        scored.append({
            "hybrid_score": hybrid,
            "embedding_score": emb_score,
            "keyword_score": key_score,
            "row": row,
        })

    scored.sort(key=lambda x: x["hybrid_score"], reverse=True)

    for i, item in enumerate(scored[:top_k], start=1):
        row = item["row"]

        print("=" * 100)
        print(f"Rank: {i}")
        print(f"Hybrid: {item['hybrid_score']:.4f}")
        print(f"Embedding: {item['embedding_score']:.4f}")
        print(f"Keyword: {item['keyword_score']:.4f}")
        print(f"Family: {row.get('policy_family')}")
        print(f"Source: {row.get('source')}")
        print(f"Page: {row.get('page')}")
        print(f"Section: {row.get('section_title')}")
        print("-" * 100)
        print(row.get("text", "")[:1200])
        print()


if __name__ == "__main__":
    main()
