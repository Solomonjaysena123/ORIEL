from __future__ import annotations

from dataclasses import dataclass

from oriel.diagnostics import Diagnostic, SourcePosition, SourceRange
from oriel.interpreter import Lexer, OrielError, Parser, TypeChecker


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    diagnostics: tuple[Diagnostic, ...]

    @property
    def is_valid(self) -> bool:
        return not self.diagnostics


class CompilerService:
    """Single frontend entry point for editor, CLI and future build integrations."""

    def analyze(self, source: str, filename: str = "<memory>") -> AnalysisResult:
        del filename  # Reserved for multi-file and module-aware analysis.
        try:
            tokens = Lexer(source).scan_tokens()
            program = Parser(tokens).parse()
            TypeChecker().check(program)
            return AnalysisResult(())
        except OrielError as error:
            line = max(0, error.line - 1)
            character = max(0, error.column - 1)
            diagnostic = Diagnostic(
                code=error.code,
                message=error.message,
                range=SourceRange(
                    SourcePosition(line, character),
                    SourcePosition(line, character + 1),
                ),
                help_text=error.help_text,
            )
            return AnalysisResult((diagnostic,))
        except Exception as error:  # Defensive boundary for IDE stability.
            diagnostic = Diagnostic(
                code="E999",
                message=f"Internal compiler error: {error}",
                range=SourceRange(SourcePosition(0, 0), SourcePosition(0, 1)),
            )
            return AnalysisResult((diagnostic,))
