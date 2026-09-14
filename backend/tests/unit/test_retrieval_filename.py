"""Filename mention matching for retrieval preference."""

from app.ai.retrieval.filename import mentioned_document_ids


def test_mentioned_document_ids_prefers_exact_filename() -> None:
    docs = [
        ("id-plan", "AI智能助手产品规划_V2.md"),
        ("id-ui", "AI智能助手平台_Phase0.5_UIUX设计_V1.md"),
    ]
    q = "AI智能助手平台_Phase0.5_UIUX设计_V1.md 这里面有啥?"
    assert mentioned_document_ids(q, docs) == ["id-ui"]


def test_mentioned_document_ids_empty_when_no_match() -> None:
    docs = [("id-plan", "AI智能助手产品规划_V2.md")]
    assert mentioned_document_ids("随便问问年假", docs) == []
