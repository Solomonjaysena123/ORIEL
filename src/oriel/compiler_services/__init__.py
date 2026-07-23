"""Stable compiler-service API shared by CLI, LSP, DAP and IDE adapters."""

from .service import AnalysisResult, CompilerService

__all__ = ["AnalysisResult", "CompilerService"]
