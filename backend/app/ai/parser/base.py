"""Document parse result types."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ParsedSegment:
    """A contiguous text block with optional page/section metadata."""

    text: str
    page: int | None = None
    section: str | None = None


@dataclass(slots=True)
class ParseResult:
    segments: list[ParsedSegment] = field(default_factory=list)
    page_count: int | None = None

    @property
    def has_text(self) -> bool:
        return any(seg.text.strip() for seg in self.segments)
