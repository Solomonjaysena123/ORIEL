"""ORIEL lexer public API.

The bootstrap implementation remains compatible with ``oriel.interpreter`` while
exposing a stable import path for compiler tooling and tests.
"""
from .interpreter import KEYWORDS, Lexer, Token, TokenType

__all__ = ["KEYWORDS", "Lexer", "Token", "TokenType"]
