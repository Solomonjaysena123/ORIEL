from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import json
from pathlib import Path
from typing import Any, Callable


class OrielError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def format(self, filename: str, source: str) -> str:
        lines = source.splitlines()
        if 1 <= self.line <= len(lines):
            code_line = lines[self.line - 1]
            caret = " " * max(self.column - 1, 0) + "^"
            return (
                f"{filename}:{self.line}:{self.column}: {self.message}\n\n"
                f"{self.line:>4} | {code_line}\n"
                f"     | {caret}"
            )
        return f"{filename}: {self.message}"


class TokenType(Enum):
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COMMA = auto()
    COLON = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    ARROW = auto()
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    LET = auto()
    VAR = auto()
    FN = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    TRUE = auto()
    FALSE = auto()
    PRINT = auto()
    AND = auto()
    OR = auto()
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    "let": TokenType.LET,
    "var": TokenType.VAR,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "print": TokenType.PRINT,
    "and": TokenType.AND,
    "or": TokenType.OR,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    literal: Any
    line: int
    column: int


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: list[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_column = 1

    def scan_tokens(self) -> list[Token]:
        while not self.is_at_end():
            self.start = self.current
            self.start_column = self.column
            self.scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))
        return self.tokens

    def scan_token(self) -> None:
        char = self.advance()
        single = {
            "(": TokenType.LEFT_PAREN,
            ")": TokenType.RIGHT_PAREN,
            "{": TokenType.LEFT_BRACE,
            "}": TokenType.RIGHT_BRACE,
            "[": TokenType.LEFT_BRACKET,
            "]": TokenType.RIGHT_BRACKET,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
            "+": TokenType.PLUS,
            "*": TokenType.STAR,
            "%": TokenType.PERCENT,
        }
        if char in single:
            self.add_token(single[char])
        elif char == "-":
            self.add_token(TokenType.ARROW if self.match(">") else TokenType.MINUS)
        elif char == "!":
            self.add_token(TokenType.BANG_EQUAL if self.match("=") else TokenType.BANG)
        elif char == "=":
            self.add_token(TokenType.EQUAL_EQUAL if self.match("=") else TokenType.EQUAL)
        elif char == "<":
            self.add_token(TokenType.LESS_EQUAL if self.match("=") else TokenType.LESS)
        elif char == ">":
            self.add_token(TokenType.GREATER_EQUAL if self.match("=") else TokenType.GREATER)
        elif char == "/":
            if self.match("/"):
                while self.peek() not in ("\n", "\0"):
                    self.advance()
            else:
                self.add_token(TokenType.SLASH)
        elif char in (" ", "\r", "\t"):
            return
        elif char == "\n":
            self.add_token(TokenType.NEWLINE)
            self.line += 1
            self.column = 1
        elif char == '"':
            self.string()
        elif char.isdigit():
            self.number()
        elif char.isalpha() or char == "_":
            self.identifier()
        else:
            raise OrielError(f"Unexpected character '{char}'.", self.line, self.start_column)

    def identifier(self) -> None:
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()
        text = self.source[self.start : self.current]
        self.add_token(KEYWORDS.get(text, TokenType.IDENTIFIER))

    def number(self) -> None:
        while self.peek().isdigit():
            self.advance()
        if self.peek() == "." and self.peek_next().isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()
        raw = self.source[self.start : self.current]
        self.add_token(TokenType.NUMBER, float(raw) if "." in raw else int(raw))

    def string(self) -> None:
        chars: list[str] = []
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == "\n":
                raise OrielError("Unterminated string.", self.line, self.start_column)
            char = self.advance()
            if char == "\\":
                escaped = self.advance()
                chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(escaped, escaped))
            else:
                chars.append(char)
        if self.is_at_end():
            raise OrielError("Unterminated string.", self.line, self.start_column)
        self.advance()
        self.add_token(TokenType.STRING, "".join(chars))

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def match(self, expected: str) -> bool:
        if self.is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def peek(self) -> str:
        return "\0" if self.is_at_end() else self.source[self.current]

    def peek_next(self) -> str:
        return "\0" if self.current + 1 >= len(self.source) else self.source[self.current + 1]

    def add_token(self, token_type: TokenType, literal: Any = None) -> None:
        self.tokens.append(
            Token(
                token_type,
                self.source[self.start : self.current],
                literal,
                self.line,
                self.start_column,
            )
        )


@dataclass
class Expr:
    pass


@dataclass
class Literal(Expr):
    value: Any


@dataclass
class Variable(Expr):
    name: Token


@dataclass
class Assign(Expr):
    name: Token
    value: Expr


@dataclass
class Unary(Expr):
    operator: Token
    right: Expr


@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass
class Grouping(Expr):
    expression: Expr


@dataclass
class Call(Expr):
    callee: Expr
    paren: Token
    arguments: list[Expr]


@dataclass
class ListExpr(Expr):
    items: list[Expr]


@dataclass
class IndexExpr(Expr):
    collection: Expr
    bracket: Token
    index: Expr


@dataclass
class IndexAssign(Expr):
    collection: Expr
    bracket: Token
    index: Expr
    value: Expr


@dataclass
class Stmt:
    pass


@dataclass
class ExpressionStmt(Stmt):
    expression: Expr


@dataclass
class PrintStmt(Stmt):
    expression: Expr


@dataclass
class VarStmt(Stmt):
    name: Token
    initializer: Expr
    mutable: bool


@dataclass
class BlockStmt(Stmt):
    statements: list[Stmt]


@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt | None


@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: Stmt


@dataclass
class ForStmt(Stmt):
    name: Token
    iterable: Expr
    body: BlockStmt


@dataclass
class FunctionStmt(Stmt):
    name: Token
    params: list[Token]
    body: list[Stmt]


@dataclass
class ReturnStmt(Stmt):
    keyword: Token
    value: Expr | None


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> list[Stmt]:
        statements: list[Stmt] = []
        self.skip_newlines()
        while not self.is_at_end():
            statements.append(self.declaration())
            self.skip_newlines()
        return statements

    def declaration(self) -> Stmt:
        if self.match(TokenType.FN):
            return self.function_declaration()
        if self.match(TokenType.LET):
            return self.variable_declaration(False)
        if self.match(TokenType.VAR):
            return self.variable_declaration(True)
        return self.statement()

    def function_declaration(self) -> FunctionStmt:
        name = self.consume(TokenType.IDENTIFIER, "Expected function name.")
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after function name.")
        params: list[Token] = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                param = self.consume(TokenType.IDENTIFIER, "Expected parameter name.")
                if self.match(TokenType.COLON):
                    self.consume(TokenType.IDENTIFIER, "Expected type name.")
                params.append(param)
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters.")
        if self.match(TokenType.ARROW):
            self.consume(TokenType.IDENTIFIER, "Expected return type.")
        self.skip_newlines()
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before function body.")
        return FunctionStmt(name, params, self.block())

    def variable_declaration(self, mutable: bool) -> VarStmt:
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name.")
        if self.match(TokenType.COLON):
            self.consume(TokenType.IDENTIFIER, "Expected type name.")
        self.consume(TokenType.EQUAL, "Expected '=' after variable name.")
        return VarStmt(name, self.expression(), mutable)

    def statement(self) -> Stmt:
        if self.match(TokenType.PRINT):
            self.consume(TokenType.LEFT_PAREN, "Expected '(' after print.")
            value = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after value.")
            return PrintStmt(value)
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.WHILE):
            return self.while_statement()
        if self.match(TokenType.FOR):
            return self.for_statement()
      8ß­­¢G§²ÚîÆ­yØ¡˜‰U¹­¹½Ý¸ÍÑ…Ñ•µ•¹ÐÑåÁ”èíÑåÁ”¡ÍÑ…Ñ•µ•¹Ð¤¹}}¹…µ•}}ôˆ¤((€€€‘•˜•á•ÕÑ•}‰±½¬¡Í•±˜°ÍÑ…Ñ•µ•¹ÑÌè±¥ÍÑmMÑµÑt°•¹Ù¥É½¹µ•¹Ðè¹Ù¥É½¹µ•¹Ð¤€´ø9½¹”è(€€€€€€€ÁÉ•Ù¥½ÕÌ€ôÍ•±˜¹•¹Ù¥É½¹µ•¹Ð(€€€€€€€ÑÉäè(€€€€€€€€€€€Í•±˜¹•¹Ù¥É½¹µ•¹Ð€ô•¹Ù¥É½¹µ•¹Ð(€€€€€€€€€€€™½ÈÍÑ…Ñ•µ•¹Ð¥¸ÍÑ…Ñ•µ•¹ÑÌè(€€€€€€€€€€€€€€€Í•±˜¹•á•ÕÑ”¡ÍÑ…Ñ•µ•¹Ð¤(€€€€€€€™¥¹…±±äè(€€€€€€€€€€€Í•±˜¹•¹Ù¥É½¹µ•¹Ð€ôÁÉ•Ù¥½ÕÌ((€€€‘•˜•Ù…±Õ…Ñ”¡Í•±˜°•áÁÉ•ÍÍ¥½¸èáÁÈ¤€´ø¹äè(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•áÁÉ•ÍÍ¥½¸°1¥Ñ•É…°¤è(€€€€€€€€€€€É•ÑÕÉ¸•áÁÉ•ÍÍ¥½¸¹Ù…±Õ”(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•áÁÉ•ÍÍ¥½¸°1¥ÍÑáÁÈ¤è(€€€€€€€€€€€É•ÑÕÉ¸mÍ•±˜¹•Ù…±Õ…Ñ”¡¥Ñ•´¤™½È¥Ñ•´¥¸•áÁÉ•ÍÍ¥½¸¹¥Ñ•µÍt(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•áÁÉ•ÍÍ¥½¸°É½ÕÁ¥¹œ¤è(€€€€€€€€€€€É•ÑÕÉ¸Í•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹•áÁÉ•ÍÍ¥½¸¤(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•áÁÉ•ÍÍ¥½¸°Y…É¥…‰±”¤è(€€€€€€€€€€€É•ÑÕÉ¸Í•±˜¹•¹Ù¥É½¹µ•¹Ð¹•Ð¡•áÁÉ•ÍÍ¥½¸¹¹…µ”¤(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•áÁÉ•ÍÍ¥½¸°ÍÍ¥¸¤è(€€€€€€€€€€€Ù…±Õ”€ôÍ•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹Ù…±Õ”¤(€€€€€€€€€€€Í•±˜¹•¹Ù¥É½¹µ•¹Ð¹…ÍÍ¥¸¡•áÁÉ•ÍÍ¥½¸¹¹…µ”°Ù…±Õ”¤(€€€€€€€€€€€É•ÑÕÉ¸Ù…±Õ”(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•áÁÉ•ÍÍ¥½¸°%¹‘•ááÁÈ¤è(€€€€€€€€€€€½±±•Ñ¥½¸€ôÍ•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹½±±•Ñ¥½¸¤(€€€€€€€€€€€¥¹‘•à€ôÍ•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹¥¹‘•à¤(€€€€€€€€€€€É•ÑÕÉ¸Í•±˜¹•Ñ}¥¹‘•à¡½±±•Ñ¥½¸°¥¹‘•à°•áÁÉ•ÍÍ¥½¸¹‰É…­•Ð¤(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•áÁÉ•ÍÍ¥½¸°%¹‘•áÍÍ¥¸¤è(€€€€€€€€€€€½±±•Ñ¥½¸€ôÍ•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹½±±•Ñ¥½¸¤(€€€€€€€€€€€¥¹‘•à€ôÍ•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹¥¹‘•à¤(€€€€€€€€€€€Ù…±Õ”€ôÍ•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹Ù…±Õ”¤(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡½±±•Ñ¥½¸°±¥ÍÐ¤è(€€€€€€€€€€€€€€€É…¥Í”=É¥•±ÉÉ½È (€€€€€€€€€€€€€€€€€€€€‰%¹‘•á•…ÍÍ¥¹µ•¹ÐÉ•ÅÕ¥É•Ì„±¥ÍÐ¸ˆ°(€€€€€€€€€€€€€€€€€€€•áÁÉ•ÍÍ¥½¸¹‰É…­•Ð¹±¥¹”°(€€€€€€€€€€€€€€€€€€€•áÁÉ•ÍÍ¥½¸¹‰É…­•Ð¹½±Õµ¸°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€½±±•Ñ¥½¹mÍ•±˜¹¡•­•‘}¥¹‘•à¡¥¹‘•à°±•¸¡½±±•Ñ¥½¸¤°•áÁÉ•ÍÍ¥½¸¹‰É…­•Ð¥t€ôÙ…±Õ”(€€€€€€€€€€€É•ÑÕÉ¸Ù…±Õ”(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•áÁÉ•ÍÍ¥½¸°U¹…Éä¤è(€€€€€€€€€€€É¥¡Ð€ôÍ•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹É¥¡Ð¤(€€€€€€€€€€€¥˜•áÁÉ•ÍÍ¥½¸¹½Á•É…Ñ½È¹ÑåÁ”€ôôQ½­•¹QåÁ”¹5%9ULè(€€€€€€€€€€€€€€€Í•±˜¹É•ÅÕ¥É•}¹Õµ‰•È¡•áÁÉ•ÍÍ¥½¸¹½Á•É…Ñ½È°É¥¡Ð¤(€€€€€€€€€€€€€€€É•ÑÕÉ¸€µÉ¥¡Ð(€€€€€€€€€€€É•ÑÕÉ¸¹½ÐÍ•±˜¹¥Í}ÑÉÕÑ¡ä¡É¥¡Ð¤(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•áÁÉ•ÍÍ¥½¸°	¥¹…Éä¤è(€€€€€€€€€€€±•™Ð€ôÍ•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹±•™Ð¤(€€€€€€€€€€€¥˜•áÁÉ•ÍÍ¥½¸¹½Á•É…Ñ½È¹ÑåÁ”€ôôQ½­•¹QåÁ”¹=Hè(€€€€€€€€€€€€€€€É•ÑÕÉ¸±•™Ð¥˜Í•±˜¹¥Í}ÑÉÕÑ¡ä¡±•™Ð¤•±Í”Í•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹É¥¡Ð¤(€€€€€€€€€€€¥˜•áÁÉ•ÍÍ¥½¸¹½Á•É…Ñ½È¹ÑåÁ”€ôôQ½­•¹QåÁ”¹9è(€€€€€€€€€€€€€€€É•ÑÕÉ¸Í•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹É¥¡Ð¤¥˜Í•±˜¹¥Í}ÑÉÕÑ¡ä¡±•™Ð¤•±Í”±•™Ð(€€€€€€€€€€€É•ÑÕÉ¸Í•±˜¹‰¥¹…Éä¡•áÁÉ•ÍÍ¥½¸¹½Á•É…Ñ½È°±•™Ð°Í•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹É¥¡Ð¤¤(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•áÁÉ•ÍÍ¥½¸°…±°¤è(€€€€€€€€€€€…±±•”€ôÍ•±˜¹•Ù…±Õ…Ñ”¡•áÁÉ•ÍÍ¥½¸¹…±±•”¤(€€€€€€€€€€€…ÉÕµ•¹ÑÌ€ômÍ•±˜¹•Ù…±Õ…Ñ”¡…ÉÕµ•¹Ð¤™½È…ÉÕµ•¹Ð¥¸•áÁÉ•ÍÍ¥½¸¹…ÉÕµ•¹ÑÍt(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡…±±•”°=É¥•±…±±…‰±”¤è(€€€€€€€€€€€€€€€É…¥Í”=É¥•±ÉÉ½È ‰…¸½¹±ä…±°™Õ¹Ñ¥½¹Ì¸ˆ°•áÁÉ•ÍÍ¥½¸¹Á…É•¸¹±¥¹”°•áÁÉ•ÍÍ¥½¸¹Á…É•¸¹½±Õµ¸¤(€€€€€€€€€€€¥˜±•¸¡…ÉÕµ•¹ÑÌ¤€„ô…±±•”¹…É¥Ñäè(€€€€€€€€€€€€€€€É…¥Í”=É¥•±ÉÉ½È (€€€€€€€€€€€€€€€€€€€˜‰áÁ•Ñ•í…±±•”¹…É¥Ñåô…ÉÕµ•¹ÑÌ‰ÕÐÉ••¥Ù•í±•¸¡…ÉÕµ•¹ÑÌ¥ô¸ˆ°(€€€€€€€€€€€€€€€€€€€•áÁÉ•ÍÍ¥½¸¹Á…É•¸¹±¥¹”°(€€€€€€€€€€€€€€€€€€€•áÁÉ•ÍÍ¥½¸¹Á…É•¸¹½±Õµ¸°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€É•ÑÕÉ¸…±±•”¹…±°¡Í•±˜°…ÉÕµ•¹ÑÌ¤(€€€€€€€É…¥Í”=É¥•±ÉÉ½È¡˜‰U¹­¹½Ý¸•áÁÉ•ÍÍ¥½¸ÑåÁ”èíÑåÁ”¡•áÁÉ•ÍÍ¥½¸¤¹}}¹…µ•}}ôˆ¤((€€€‘•˜‰¥¹…Éä¡Í•±˜°½Á•É…Ñ½ÈèQ½­•¸°±•™Ðè¹ä°É¥¡Ðè¹ä¤€´ø¹äè(€€€€€€€Ñ½­•¹}ÑåÁ”€ô½Á•É…Ñ½È¹ÑåÁ”(€€€€€€€¥˜Ñ½­•¹}ÑåÁ”€ôôQ½­•¹QåÁ”¹A1ULè(€€€€€€€€€€€¥˜Í•±˜¹¥Í}¹Õµ‰•È¡±•™Ð¤…¹Í•±˜¹¥Í}¹Õµ‰•È¡É¥¡Ð¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸±•™Ð€¬É¥¡Ð(€€€€€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡±•™Ð°ÍÑÈ¤½È¥Í¥¹ÍÑ…¹”¡É¥¡Ð°ÍÑÈ¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸Í•±˜¹ÍÑÉ¥¹¥™ä¡±•™Ð¤€¬Í•±˜¹ÍÑÉ¥¹¥™ä¡É¥¡Ð¤(€€€€€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡±•™Ð°±¥ÍÐ¤…¹¥Í¥¹ÍÑ…¹”¡É¥¡Ð°±¥ÍÐ¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸±•™Ð€¬É¥¡Ð(€€€€€€€€€€€É…¥Í”=É¥•±ÉÉ½È ‰=Á•É…Ñ½È€œ¬œÉ•ÅÕ¥É•Ì¹Õµ‰•ÉÌ°ÍÑÉ¥¹Ì°½È±¥ÍÑÌ¸ˆ°½Á•É…Ñ½È¹±¥¹”°½Á•É…Ñ½È¹½±Õµ¸¤(€€€€€€€¥˜Ñ½­•¹}ÑåÁ”¥¸€¡Q½­•¹QåÁ”¹5%9UL°Q½­•¹QåÁ”¹MQH°Q½­•¹QåÁ”¹M1M °Q½­•¹QåÁ”¹AI9P¤è(€€€€€€€€€€€Í•±˜¹É•ÅÕ¥É•}¹Õµ‰•ÉÌ¡½Á•É…Ñ½È°±•™Ð°É¥¡Ð¤(€€€€€€€€€€€¥˜Ñ½­•¹}ÑåÁ”€ôôQ½­•¹QåÁ”¹5%9ULè(€€€€€€€€€€€€€€€É•ÑÕÉ¸±•™Ð€´É¥¡Ð(€€€€€€€€€€€¥˜Ñ½­•¹}ÑåÁ”€ôôQ½­•¹QåÁ”¹MQHè(€€€€€€€€€€€€€€€É•ÑÕÉ¸±•™Ð€¨É¥¡Ð(€€€€€€€€€€€¥˜É¥¡Ð€ôô€Àè(€€€€€€€€€€€€€€€É…¥Í”=É¥•±ÉÉ½È ‰¥Ù¥Í¥½¸‰äé•É¼¸ˆ°½Á•É…Ñ½È¹±¥¹”°½Á•É…Ñ½È¹½±Õµ¸¤(€€€€€€€€€€€É•ÑÕÉ¸±•™Ð€¼É¥¡Ð¥˜Ñ½­•¹}ÑåÁ”€ôôQ½­•¹QåÁ”¹M1M •±Í”±•™Ð€”É¥¡Ð(€€€€€€€¥˜Ñ½­•¹}ÑåÁ”€ôôQ½­•¹QåÁ”¹EU1}EU0è(€€€€€€€€€€€É•ÑÕÉ¸±•™Ð€ôôÉ¥¡Ð(€€€€€€€¥˜Ñ½­•¹}ÑåÁ”€ôôQ½­•¹QåÁ”¹	9}EU0è(€€€€€€€€€€€É•ÑÕÉ¸±•™Ð€„ôÉ¥¡Ð(€€€€€€€¥˜Ñ½­•¹}ÑåÁ”¥¸€ (€€€€€€€€€€€Q½­•¹QåÁ”¹IQH°(€€€€€€€€€€€Q½­•¹QåÁ”¹IQI}EU0°(€€€€€€€€€€€Q½­•¹QåÁ”¹1ML°(€€€€€€€€€€€Q½­•¹QåÁ”¹1MM}EU0°(€€€€€€€€¤è(€€€€€€€€€€€Í•±˜¹É•ÅÕ¥É•}¹Õµ‰•ÉÌ¡½Á•É…Ñ½È°±•™Ð°É¥¡Ð¤(€€€€€€€€€€€É•ÑÕÉ¸ì(€€€€€€€€€€€€€€€Q½­•¹QåÁ”¹IQHè±•™Ð€øÉ¥¡Ð°(€€€€€€€€€€€€€€€Q½­•¹QåÁ”¹IQI}EU0è±•™Ð€øôÉ¥¡Ð°(€€€€€€€€€€€€€€€Q½­•¹QåÁ”¹1MLè±•™Ð€ðÉ¥¡Ð°(€€€€€€€€€€€€€€€Q½­•¹QåÁ”¹1MM}EU0è±•™Ð€ðôÉ¥¡Ð°(€€€€€€€€€€€õmÑ½­•¹}ÑåÁ•t(€€€€€€€É…¥Í”=É¥•±ÉÉ½È ‰U¹ÍÕÁÁ½ÉÑ•½Á•É…Ñ½È¸ˆ°½Á•É…Ñ½È¹±¥¹”°½Á•É…Ñ½È¹½±Õµ¸¤((€€€ÍÑ…Ñ¥µ•Ñ¡½(€€€‘•˜¥Í}ÑÉÕÑ¡ä¡Ù…±Õ”è¹ä¤€´ø‰½½°è(€€€€€€€É•ÑÕÉ¸…±Í”¥˜Ù…±Õ”¥Ì9½¹”•±Í”‰½½°¡Ù…±Õ”¤((€€€ÍÑ…Ñ¥µ•Ñ¡½(€€€‘•˜¥Í}¹Õµ‰•È¡Ù…±Õ”è¹ä¤€´ø‰½½°è(€€€€€€€É•ÑÕÉ¸¥Í¥¹ÍÑ…¹”¡Ù…±Õ”°€¡¥¹Ð°™±½…Ð¤¤…¹¹½Ð¥Í¥¹ÍÑ…¹”¡Ù…±Õ”°‰½½°¤((€€€±…ÍÍµ•Ñ¡½(€€€‘•˜É•ÅÕ¥É•}¹Õµ‰•È¡±Ì°Ñ½­•¸èQ½­•¸°Ù…±Õ”è¹ä¤€´ø9½¹”è(€€€€€€€¥˜¹½Ð±Ì¹¥Í}¹Õµ‰•È¡Ù…±Õ”¤è(€€€€€€€€€€€É…¥Í”=É¥•±ÉÉ½È ‰=Á•É…¹µÕÍÐ‰”„¹Õµ‰•È¸ˆ°Ñ½­•¸¹±¥¹”°Ñ½­•¸¹½±Õµ¸¤((€€€±…ÍÍµ•Ñ¡½(€€€‘•˜É•ÅÕ¥É•}¹Õµ‰•ÉÌ¡±Ì°Ñ½­•¸èQ½­•¸°±•™Ðè¹ä°É¥¡Ðè¹ä¤€´ø9½¹”è(€€€€€€€±Ì¹É•ÅÕ¥É•}¹Õµ‰•È¡Ñ½­•¸°±•™Ð¤(€€€€€€€±Ì¹É•ÅÕ¥É•}¹Õµ‰•È¡Ñ½­•¸°É¥¡Ð¤((€€€ÍÑ…Ñ¥µ•Ñ¡½(€€€‘•˜¡•­•‘}¥¹‘•à¡¥¹‘•àè¹ä°Í¥é”è¥¹Ð°Ñ½­•¸èQ½­•¸¤€´ø¥¹Ðè(€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡¥¹‘•à°¥¹Ð¤½È¥Í¥¹ÍÑ…¹”¡¥¹‘•à°‰½½°¤è(€€€€€€€€€€€É…¥Í”=É¥•±ÉÉ½È ‰%¹‘¥•ÌµÕÍÐ‰”¥¹Ñ••ÉÌ¸ˆ°Ñ½­•¸¹±¥¹”°Ñ½­•¸¹½±Õµ¸¤(€€€€€€€¥˜¥¹‘•à€ð€µÍ¥é”½È¥¹‘•à€øôÍ¥é”è(€€€€€€€€€€€É…¥Í”=É¥•±ÉÉ½È ‰%¹‘•à½ÕÐ½˜É…¹”¸ˆ°Ñ½­•¸¹±¥¹”°Ñ½­•¸¹½±Õµ¸¤(€€€€€€€É•ÑÕÉ¸¥¹‘•à((€€€±…ÍÍµ•Ñ¡½(€€€‘•˜•Ñ}¥¹‘•à¡±Ì°½±±•Ñ¥½¸è¹ä°¥¹‘•àè¹ä°Ñ½­•¸èQ½­•¸¤€´ø¹äè(€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡½±±•Ñ¥½¸°€¡±¥ÍÐ°ÍÑÈ¤¤è(€€€€€€€€€€€É…¥Í”=É¥•±ÉÉ½È ‰=¹±ä±¥ÍÑÌ…¹ÍÑÉ¥¹Ì…¸‰”¥¹‘•á•¸ˆ°Ñ½­•¸¹±¥¹”°Ñ½­•¸¹½±Õµ¸¤(€€€€€€€É•ÑÕÉ¸½±±•Ñ¥½¹m±Ì¹¡•­•‘}¥¹‘•à¡¥¹‘•à°±•¸¡½±±•Ñ¥½¸¤°Ñ½­•¸¥t((€€€ÍÑ…Ñ¥µ•Ñ¡½(€€€‘•˜É•…‘}™¥±”¡Á…Ñ è¹ä¤€´øÍÑÈè(€€€€€€€É•ÑÕÉ¸A…Ñ ¡ÍÑÈ¡Á…Ñ ¤¤¹É•…‘}Ñ•áÐ¡•¹½‘¥¹œô‰ÕÑ˜´àˆ¤((€€€ÍÑ…Ñ¥µ•Ñ¡½(€€€‘•˜ÝÉ¥Ñ•}™¥±”¡Á…Ñ è¹ä°½¹Ñ•¹Ðè¹ä¤€´ø9½¹”è(€€€€€€€A…Ñ ¡ÍÑÈ¡Á…Ñ ¤¤¹ÝÉ¥Ñ•}Ñ•áÐ¡ÍÑÈ¡½¹Ñ•¹Ð¤°•¹½‘¥¹œô‰ÕÑ˜´àˆ¤(€€€€€€€É•ÑÕÉ¸9½¹”((€€€ÍÑ…Ñ¥µ•Ñ¡½(€€€‘•˜ÍÑÉ¥¹¥™ä¡Ù…±Õ”è¹ä¤€´øÍÑÈè(€€€€€€€¥˜Ù…±Õ”¥Ì9½¹”è(€€€€€€€€€€€É•ÑÕÉ¸€‰¹½¹”ˆ(€€€€€€€¥˜Ù…±Õ”¥ÌQÉÕ”è(€€€€€€€€€€€É•ÑÕÉ¸€‰ÑÉÕ”ˆ(€€€€€€€¥˜Ù…±Õ”¥Ì…±Í”è(€€€€€€€€€€€É•ÑÕÉ¸€‰™…±Í”ˆ(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡Ù…±Õ”°™±½…Ð¤…¹Ù…±Õ”¹¥Í}¥¹Ñ••È ¤è(€€€€€€€€€€€É•ÑÕÉ¸ÍÑÈ¡¥¹Ð¡Ù…±Õ”¤¤(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡Ù…±Õ”°±¥ÍÐ¤è(€€€€€€€€€€€É•ÑÕÉ¸€‰lˆ€¬€ˆ°€ˆ¹©½¥¸¡%¹Ñ•ÉÁÉ•Ñ•È¹ÍÑÉ¥¹¥™ä¡¥Ñ•´¤™½È¥Ñ•´¥¸Ù…±Õ”¤€¬€‰tˆ(€€€€€€€É•ÑÕÉ¸ÍÑÈ¡Ù…±Õ”¤(()‘•˜ÉÕ¹}Í½ÕÉ” (€€€Í½ÕÉ”èÍÑÈ°(€€€™¥±•¹…µ”èÍÑÈ€ô€ˆñÍ½ÕÉ”øˆ°(€€€½ÕÑÁÕÐè…±±…‰±•mmÍÑÉt°9½¹•tð9½¹”€ô9½¹”°(¤€´ø9½¹”è(€€€ÑÉäè(€€€€€€€Ñ½­•¹Ì€ô1•á•È¡Í½ÕÉ”¤¹Í…¹}Ñ½­•¹Ì ¤(€€€€€€€ÍÑ…Ñ•µ•¹ÑÌ€ôA…ÉÍ•È¡Ñ½­•¹Ì¤¹Á…ÉÍ” ¤(€€€€€€€%¹Ñ•ÉÁÉ•Ñ•È¡½ÕÑÁÕÐõ½ÕÑÁÕÐ¤¹¥¹Ñ•ÉÁÉ•Ð¡ÍÑ…Ñ•µ•¹ÑÌ¤(€€€•á•ÁÐ=É¥•±ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€É…¥Í”IÕ¹Ñ¥µ•ÉÉ½È¡•ÉÉ½È¹™½Éµ…Ð¡™¥±•¹…µ”°Í½ÕÉ”¤¤™É½´•ÉÉ½È