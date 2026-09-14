"""Minimal golden-dataset smoke (offline / fake — no paid API).

M3/M6: parse + chunk shape for known samples, plus lightweight keyword
retrieval ranking (no Qdrant / embedding required).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.ai.parser import parse_document_bytes
from app.modules.job.pipeline import chunk_parse_result

GOLDEN_PATH = Path(__file__).with_name("golden_samples.json")
_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]{2,}|[a-zA-Z0-9_]{2,}")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text))


def _keyword_rank(chunks: list[str], question: str) -> list[str]:
    q_tokens = _tokens(question)
    if not q_tokens:
        return chunks
    scored = [
        (sum(1 for t in q_tokens if t in chunk), idx, chunk)
        for idx, chunk in enumerate(chunks)
    ]
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [chunk for _score, _idx, chunk in scored]


def test_golden_samples_parse_and_chunk() -> None:
    samples = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert samples, "golden_samples.json must not be empty"

    for item in samples:
        raw = item["content"].encode("utf-8")
        parsed = parse_document_bytes(raw, file_type=item["file_type"])
        assert parsed.has_text, item["id"]
        chunk_size = int(item.get("chunk_size", 200))
        chunk_overlap = int(item.get("chunk_overlap", 40))
        rows = chunk_parse_result(
            parsed, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        assert rows, item["id"]
        min_chunks = int(item.get("min_chunks", 1))
        assert len(rows) >= min_chunks, f"{item['id']}: expected >= {min_chunks} chunks"

        chunk_texts = [content for content, _page, _section in rows]
        joined = "\n".join(chunk_texts)
        for needle in item["must_contain"]:
            assert needle in joined, f"{item['id']}: missing {needle!r}"

        question = (item.get("question") or "").strip()
        if question:
            ranked = _keyword_rank(chunk_texts, question)
            top = ranked[0]
            hits = [n for n in item["must_contain"] if n in top]
            assert hits, (
                f"{item['id']}: top keyword chunk missed all must_contain; top={top!r}"
            )
