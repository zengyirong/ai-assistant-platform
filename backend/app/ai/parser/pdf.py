"""PDF parser via PyMuPDF (text-extractable PDFs only; no OCR)."""

from __future__ import annotations

import pymupdf as fitz

from app.ai.parser.base import ParseResult, ParsedSegment
from app.ai.parser.errors import DocumentParseError


def parse_pdf_bytes(raw: bytes) -> ParseResult:
    try:
        doc = fitz.open(stream=raw, filetype="pdf")
    except Exception as exc:
        raise DocumentParseError(
            "DOCUMENT_PARSE_FAILED",
            f"无法打开 PDF：{exc}",
        ) from exc

    try:
        if doc.is_encrypted:
            # try empty password; still encrypted → fail clearly
            if not doc.authenticate(""):
                raise DocumentParseError(
                    "DOCUMENT_PARSE_FAILED",
                    "PDF 已加密，请先解除密码保护后再上传",
                )

        segments: list[ParsedSegment] = []
        for index, page in enumerate(doc, start=1):
            text = (page.get_text("text") or "").replace("\r\n", "\n").strip()
            if text:
                segments.append(ParsedSegment(text=text, page=index))

        page_count = doc.page_count
    finally:
        doc.close()

    if not segments:
        raise DocumentParseError(
            "DOCUMENT_PARSE_FAILED",
            "未能从 PDF 提取文本（可能是扫描件）。一期不支持 OCR，请上传可选中文本的 PDF，或改用 TXT/MD",
        )

    return ParseResult(segments=segments, page_count=page_count)
