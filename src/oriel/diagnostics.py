"""Unified ORIEL diagnostic public API."""
from .interpreter import OrielError

DIAGNOSTIC_GROUPS = {
    "E1": "lexer",
    "E2": "parser",
    "E3": "name resolution",
    "E4": "type checking",
    "E6": "runtime",
}

__all__ = ["DIAGNOSTIC_GROUPS", "OrielError"]
