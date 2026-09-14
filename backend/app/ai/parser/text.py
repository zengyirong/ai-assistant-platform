"""Plain text / Markdown parser."""

from __future__ import annotations

from app.ai.parser.base import ParsedSegment, ParseResult
from app.ai.parser.errors import DocumentParseError


def parse_text_bytes(raw: bytes, *, file_type: str) -> ParseResult:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentParseError(
            "DOCUMENT_PARSE_FAILED",
            f".{file_type} 不是有效 UTF-8 文本",
        ) from exc

    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        raise DocumentParseError("DOCUMENT_PARSE_FAILED", "文档内容为空，无法解析")

    return ParseResult(
        segments=[ParsedSegment(text=cleaned, page=1)],
        page_count=1,
    )
