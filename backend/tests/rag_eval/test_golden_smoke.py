"""Minimal golden-dataset smoke (offline / fake — no paid API).

M3 Should: start a small RAG eval fixture set that asserts parse + chunk
shape for known sample questions. Full retrieval scoring comes later.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.ai.parser import parse_document_bytes
from app.modules.job.pipeline import chunk_parse_result

GOLDEN_PATH = Path(__file__).with_name("golden_samples.json")


def test_golden_samples_parse_and_chunk() -> None:
    samples = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert samples, "golden_samples.json must not be empty"

    for item in samples:
        raw = item["content"].encode("utf-8")
        parsed = parse_document_bytes(raw, file_type=item["file_type"])
        assert parsed.has_text, item["id"]
        chunks = chunk_parse_result(parsed, chunk_size=200, chunk_overlap=40)
        assert chunks, item["id"]
        joined = "\n".join(content for content, _page, _section in chunks)
        for needle in item["must_contain"]:
            assert needle in joined, f"{item['id']}: missing {needle!r}"
