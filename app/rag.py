import json
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "embeddinggemma:300m-qat-q8_0")
POLICY_INDEX_PATH = os.getenv("POLICY_INDEX_PATH", "/app/policy_docs/index/policy_vectors.jsonl")
POLICY_TOP_K = int(os.getenv("POLICY_TOP_K", "6"))

K1 = 1.5
B = 0.75

_POLICY_CACHE: List[Dict[str, Any]] = []
_POLICY_CACHE_MTIME: Optional[float] = None


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_./:-]+", text.lower())


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def load_policy_vectors() -> List[Dict[str, Any]]:
    global _POLICY_CACHE, _POLICY_CACHE_MTIME

    path = Path(POLICY_INDEX_PATH)

    if not path.exists():
        return []

    mtime = path.stat().st_mtime

    if _POLICY_CACHE and _POLICY_CACHE_MTIME == mtime:
        return _POLICY_CACHE

    rows = []
    with path.open("r") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    _POLICY_CACHE = rows
    _POLICY_CACHE_MTIME = mtime
    return rows


async def embed_query(text: str) -> List[float]:
    payload = {
        "model": EMBED_MODEL,
        "input": text,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(f"{OLLAMA_BASE_URL}/api/embed", json=payload)
        response.raise_for_status()
        data = response.json()

    embeddings = data.get("embeddings") or []

    if not embeddings:
        return []

    return embeddings[0]


def build_df_map(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    df_map: Dict[str, int] = {}

    for row in rows:
        for token in row.get("bm25_tokens", {}).keys():
            df_map[token] = df_map.get(token, 0) + 1

    return df_map


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


def diversify_by_family(results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    """
    Keep retrieval balanced so internal policy does not dominate.
    """
    preferred_order = [
        "INTERNAL_POLICY",
        "GDPR",
        "EU_AI_ACT",
        "EU_AI_ACT_GPAI_GUIDANCE",
        "UNKNOWN",
    ]

    by_family: Dict[str, List[Dict[str, Any]]] = {}

    for item in results:
        family = item.get("policy_family") or "UNKNOWN"
        by_family.setdefault(family, []).append(item)

    selected: List[Dict[str, Any]] = []

    for family in preferred_order:
        if family in by_family and by_family[family]:
            selected.append(by_family[family].pop(0))

    i = 0
    while len(selected) < top_k and i < len(results):
        item = results[i]
        if item not in selected:
            selected.append(item)
        i += 1

    return selected[:top_k]


async def search_policy(query: str, top_k: int = None, balanced: bool = True) -> List[Dict[str, Any]]:
    top_k = top_k or POLICY_TOP_K

    rows = load_policy_vectors()
    if not rows:
        return []

    query_embedding = await embed_query(query)
    if not query_embedding:
        return []

    query_tokens = tokenize(query)
    doc_count = len(rows)
    avg_len = sum(max(1, row.get("token_count", 1)) for row in rows) / max(1, doc_count)
    df_map = build_df_map(rows)

    raw_scores = []

    for row in rows:
        emb_score = cosine_similarity(query_embedding, row.get("embedding", []))
        key_score = bm25_score(query_tokens, row, avg_len, doc_count, df_map)
        raw_scores.append((emb_score, key_score, row))

    max_key = max((x[1] for x in raw_scores), default=0.0) or 1.0

    scored = []

    for emb_score, key_score, row in raw_scores:
        normalized_keyword = key_score / max_key
        hybrid_score = (0.72 * emb_score) + (0.28 * normalized_keyword)

        text = row.get("text", "")

        scored.append({
            "chunk_id": row.get("chunk_id"),
            "source": row.get("source"),
            "source_type": row.get("source_type"),
            "policy_family": row.get("policy_family"),
            "page": row.get("page"),
            "section_title": row.get("section_title"),
            "hybrid_score": round(float(hybrid_score), 4),
            "embedding_score": round(float(emb_score), 4),
            "keyword_score": round(float(key_score), 4),
            "excerpt": text[:1200],
        })

    scored.sort(key=lambda x: x["hybrid_score"], reverse=True)

    if balanced:
        return diversify_by_family(scored, top_k)

    return scored[:top_k]


def policy_index_status() -> Dict[str, Any]:
    path = Path(POLICY_INDEX_PATH)
    rows = load_policy_vectors()

    families: Dict[str, int] = {}
    sources: Dict[str, int] = {}

    for row in rows:
        family = row.get("policy_family", "UNKNOWN")
        source = row.get("source", "UNKNOWN")
        families[family] = families.get(family, 0) + 1
        sources[source] = sources.get(source, 0) + 1

    return {
        "index_path": str(path),
        "exists": path.exists(),
        "chunk_count": len(rows),
        "embedding_model": EMBED_MODEL,
        "top_k": POLICY_TOP_K,
        "hybrid_retrieval": {
            "embedding": True,
            "bm25_style_keyword_score": True,
            "family_balancing": True,
        },
        "policy_families": families,
        "sources": sources,
    }
