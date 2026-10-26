"""Data model for one extracted clinical entry."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Entry:
    kind: str                     # "medication" | "procedure"
    name: str
    dose_value: Optional[float] = None
    dose_unit: Optional[str] = None
    route: Optional[str] = None
    time: Optional[str] = None    # "HH:MM" (24h)
    details: dict = field(default_factory=dict)
    source_text: str = ""
    confidence: float = 0.0
    flags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def needs_review(self) -> bool:
        return bool(self.flags)


@dataclass
class ParseResult:
    entries: list
    normalized_text: str
    warnings: list

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries],
                "normalized_text": self.normalized_text, "warnings": self.warnings}
