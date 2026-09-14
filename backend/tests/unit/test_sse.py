from app.schemas.sse import (
    SseCitationItem,
    make_citation,
    make_done,
    make_error,
    make_start,
    make_text,
)


def test_sse_seq_helpers() -> None:
    start = make_start(
        request_id="req_1",
        conversation_id="conv_1",
        message_id="msg_1",
        seq=1,
    )
    assert start.event == "start"
    assert start.seq == 1
    assert "data:" in start.to_sse_line()

    text = make_text(
        request_id="req_1",
        conversation_id="conv_1",
        message_id="msg_1",
        seq=2,
        content="你好",
    )
    assert text.data["content"] == "你好"

    cite = make_citation(
        request_id="req_1",
        conversation_id="conv_1",
        message_id="msg_1",
        seq=3,
        citations=[
            SseCitationItem(document_id="d1", chunk_id="c1", page=1, snippet="..."),
        ],
    )
    assert len(cite.data["citations"]) == 1

    done = make_done(
        request_id="req_1",
        conversation_id="conv_1",
        message_id="msg_1",
        seq=4,
    )
    assert done.data["status"] == "COMPLETED"

    err = make_error(
        request_id="req_1",
        conversation_id="conv_1",
        message_id="msg_1",
        seq=5,
        code="LLM_TIMEOUT",
        message="timeout",
    )
    assert err.event == "error"
    assert err.data["code"] == "LLM_TIMEOUT"
