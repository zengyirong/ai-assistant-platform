"""Document parsers — dispatch by file type."""

from __future__ import annotations

from app.ai.parser.base import ParseResult, ParsedSegment
from app.ai.parser.docx_file import parse_docx_bytes
from app.ai.parser.errors import DocumentParseError
from app.ai.parser.pdf import parse_pdf_bytes
from app.ai.parser.text import parse_text_bytes

__all__ = [
    "DocumentParseError",
    "ParseResult",
    "ParsedSegment",
    "parse_document_bytes",
]


def parse_document_bytes(raw: bytes, *, file_type: str) -> ParseResult:
    ft = (file_type or "").strip().lower()
    if ft in {"txt", "md", "markdown"}:
        return parse_text_bytes(raw, file_type=ft)
    if ft == "pdf":
        return parse_pdf_bytes(raw)
    if ft == "docx":
        return parse_docx_bytes(raw)
    raise DocumentParseError(
        "DOCUMENT_PARSE_FAILED",
        f"不支持解析 .{ft or 'unknown'}。"
        "支持：PDF / DOCX / TXT / MD（扫描版 PDF 需 OCR，一期不支持）",
    )
