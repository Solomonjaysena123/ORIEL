from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class DiagnosticSeverity(IntEnum):
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


@dataclass(frozen=True, slots=True)
class SourcePosition:
    """Zero-based position used by compiler services and LSP clients."""

    line: int
    character: int


@dataclass(frozen=True, slots=True)
class SourceRange:
    start: SourcePosition
    end: SourcePosition


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    message: str
    range: SourceRange
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    source: str = "oriel"
    help_text: str | None = None

    def to_lsp(self) -> dict[str, object]:
        result: dict[str, object] = {
            "range": {
                "start": {"line": self.range.start.line, "character": self.range.start.character},
                "end": {"line": self.range.end.line, "character": self.range.end.character},
            },
            "severity": int(self.severity),
            "code": self.code,
            "source": self.source,
            "message": self.message,
        }
        if self.help_text:
            result["data"] = {"help": self.help_text}
        return result
