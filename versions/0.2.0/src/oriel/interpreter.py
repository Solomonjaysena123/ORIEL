from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable
from pathlib import Path
import json


class OrielError(Exception):
    """Base error with source location support."""

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
    # Single-character
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

    # One/two character
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    ARROW = auto()

    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Keywords
    LET = auto()
    VAR = auto()
    FN = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    NONE = auto()
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
    "none": TokenType.NONE,
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
        c = self.advance()
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
        if c in single:
            self.add_token(single[c])
        elif c == "-":
            self.add_token(TokenType.ARROW if self.match(">") else TokenType.MINUS)
        elif c == "!":
            self.add_token(TokenType.BANG_EQUAL if self.match("=") else TokenType.BANG)
        elif c == "=":
            self.add_token(TokenType.EQUAL_EQUAL if self.match("=") else TokenType.EQUAL)
        elif c == "<":
            self.add_token(TokenType.LESS_EQUAL if self.match("=") else TokenType.LESS)
        elif c == ">":
            self.add_token(TokenType.GREATER_EQUAL if self.match("=") else TokenType.GREATER)
        elif c == "/":
            if self.match("/"):
                while self.peek() not in ("\n", "\0"):
                    self.advance()
            else:
                self.add_token(TokenType.SLASH)
        elif c in (" ", "\r", "\t"):
            pass
        elif c == "\n":
            self.add_token(TokenType.NEWLINE)
            self.line += 1
            self.column = 1
        elif c == '"':
            self.string()
        elif c.isdigit():
            self.number()
        elif c.isalpha() or c == "_":
            self.identifier()
        else:
            raise OrielError(f"Unexpected character '{c}'.", self.line, self.start_column)

    def identifier(self) -> None:
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()
        text = self.source[self.start:self.current]
        self.add_token(KEYWORDS.get(text, TokenType.IDENTIFIER))

    def number(self) -> None:
        while self.peek().isdigit():
            self.advance()
        if self.peek() == "." and self.peek_next().isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()
        raw = self.source[self.start:self.current]
        value = float(raw) if "." in raw else int(raw)
        self.add_token(TokenType.NUMBER, value)

    def string(self) -> None:
        value_chars: list[str] = []
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == "\n":
                raise OrielError("Unterminated string.", self.line, self.start_column)
            ch = self.advance()
            if ch == "\\":
                esc = self.advance()
                value_chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(esc, esc))
            else:
                value_chars.append(ch)
        if self.is_at_end():
            raise OrielError("Unterminated string.", self.line, self.start_column)
        self.advance()
        self.add_token(TokenType.STRING, "".join(value_chars))

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        self.column += 1
        return c

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
        text = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, text, literal, self.line, self.start_column))


# AST
@dataclass
class Expr: pass

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
class ListLiteral(Expr):
    items: list[Expr]

@dataclass
class IndexExpr(Expr):
    target: Expr
    bracket: Token
    index: Expr

@dataclass
class Stmt: pass

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
    body: Stmt

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
                # Optional type annotation: : Type
                if self.match(TokenType.COLON):
                    self.consume(TokenType.IDENTIFIER, "Expected type name.")
                params.append(param)
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters.")
        # Optional return type
        if self.match(TokenType.ARROW):
            self.consume(TokenType.IDENTIFIER, "Expected return type.")
        self.skip_newlines()
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before function body.")
        body = self.block()
        return FunctionStmt(name, params, body)

    def variable_declaration(self, mutable: bool) -> VarStmt:
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name.")
        if self.match(TokenType.COLON):
            self.consume(TokenType.IDENTIFIER, "Expected type name.")
        self.consume(TokenType.EQUAL, "Expected '=' after variable name.")
        initializer = self.expression()
        return VarStmt(name, initializer, mutable)

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
        if self.match(TokenType.RETURN):
            keyword = self.previous()
            value = None if self.check(TokenType.NEWLINE) or self.check(TokenType.RIGHT_BRACE) else self.expression()
            return ReturnStmt(keyword, value)
        if self.match(TokenType.LEFT_BRACE):
            return BlockStmt(self.block())
        return ExpressionStmt(self.expression())

    def if_statement(self) -> IfStmt:
        condition = self.expression()
        self.skip_newlines()
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after if condition.")
        then_branch = BlockStmt(self.block())
        self.skip_newlines()
        else_branch = None
        if self.match(TokenType.ELSE):
            self.skip_newlines()
            if self.match(TokenType.IF):
                else_branch = self.if_statement()
            else:
                self.consume(TokenType.LEFT_BRACE, "Expected '{' after else.")
                else_branch = BlockStmt(self.block())
        return IfStmt(condition, then_branch, else_branch)

    def while_statement(self) -> WhileStmt:
        condition = self.expression()
        self.skip_newlines()
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after while condition.")
        return WhileStmt(condition, BlockStmt(self.block()))

    def for_statement(self) -> ForStmt:
        name = self.consume(TokenType.IDENTIFIER, "Expected loop variable after 'for'.")
        self.consume(TokenType.IN, "Expected 'in' after loop variable.")
        iterable = self.expression()
        self.skip_newlines()
        self.consume(TokenType.LEFT_BRACE, "Expected '{' after for expression.")
        return ForStmt(name, iterable, BlockStmt(self.block()))

    def block(self) -> list[Stmt]:
        statements: list[Stmt] = []
        self.skip_newlines()
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())
            self.skip_newlines()
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after block.")
        return statements

    def expression(self) -> Expr:
        return self.assignment()

    def assignment(self) -> Expr:
        expr = self.or_expr()
        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()
            if isinstance(expr, Variable):
                return Assign(expr.name, value)
            raise OrielError("Invalid assignment target.", equals.line, equals.column)
        return expr

    def or_expr(self) -> Expr:
        expr = self.and_expr()
        while self.match(TokenType.OR):
            op = self.previous()
            expr = Binary(expr, op, self.and_expr())
        return expr

    def and_expr(self) -> Expr:
        expr = self.equality()
        while self.match(TokenType.AND):
            op = self.previous()
            expr = Binary(expr, op, self.equality())
        return expr

    def equality(self) -> Expr:
        expr = self.comparison()
        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            op = self.previous()
            expr = Binary(expr, op, self.comparison())
        return expr

    def comparison(self) -> Expr:
        expr = self.term()
        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            op = self.previous()
            expr = Binary(expr, op, self.term())
        return expr

    def term(self) -> Expr:
        expr = self.factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.previous()
            expr = Binary(expr, op, self.factor())
        return expr

    def factor(self) -> Expr:
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.previous()
            expr = Binary(expr, op, self.unary())
        return expr

    def unary(self) -> Expr:
        if self.match(TokenType.BANG, TokenType.MINUS):
            op = self.previous()
            return Unary(op, self.unary())
        return self.call()

    def call(self) -> Expr:
        expr = self.primary()
        while True:
            if self.match(TokenType.LEFT_PAREN):
                args: list[Expr] = []
                if not self.check(TokenType.RIGHT_PAREN):
                    while True:
                        args.append(self.expression())
                        if not self.match(TokenType.COMMA):
                            break
                paren = self.consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments.")
                expr = Call(expr, paren, args)
            elif self.match(TokenType.LEFT_BRACKET):
                bracket = self.previous()
                index = self.expression()
                self.consume(TokenType.RIGHT_BRACKET, "Expected ']' after index.")
                expr = IndexExpr(expr, bracket, index)
            else:
                break
        return expr

    def primary(self) -> Expr:
        if self.match(TokenType.FALSE):
            return Literal(False)
        if self.match(TokenType.TRUE):
            return Literal(True)
        if self.match(TokenType.NONE):
            return Literal(None)
        if self.match(TokenType.LEFT_BRACKET):
            items: list[Expr] = []
            if not self.check(TokenType.RIGHT_BRACKET):
                while True:
                    items.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RIGHT_BRACKET, "Expected ']' after list items.")
            return ListLiteral(items)
        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)
        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous())
        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expected ')' after expression.")
            return Grouping(expr)
        token = self.peek()
        raise OrielError("Expected an expression.", token.line, token.column)

    def skip_newlines(self) -> None:
        while self.match(TokenType.NEWLINE):
            pass

    def match(self, *types: TokenType) -> bool:
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()
        token = self.peek()
        raise OrielError(message, token.line, token.column)

    def check(self, token_type: TokenType) -> bool:
        if self.is_at_end():
            return token_type == TokenType.EOF
        return self.peek().type == token_type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]


@dataclass
class Binding:
    value: Any
    mutable: bool


class Environment:
    def __init__(self, enclosing: "Environment | None" = None):
        self.values: dict[str, Binding] = {}
        self.enclosing = enclosing

    def define(self, name: str, value: Any, mutable: bool = False) -> None:
        self.values[name] = Binding(value, mutable)

    def get(self, token: Token) -> Any:
        if token.lexeme in self.values:
            return self.values[token.lexeme].value
        if self.enclosing:
            return self.enclosing.get(token)
        raise OrielError(f"Undefined variable '{token.lexeme}'.", token.line, token.column)

    def assign(self, token: Token, value: Any) -> None:
        if token.lexeme in self.values:
            binding = self.values[token.lexeme]
            if not binding.mutable:
                raise OrielError(
                    f"Cannot assign to immutable variable '{token.lexeme}'. Use 'var' for mutable values.",
                    token.line,
                    token.column,
                )
            binding.value = value
            return
        if self.enclosing:
            self.enclosing.assign(token, value)
            return
        raise OrielError(f"Undefined variable '{token.lexeme}'.", token.line, token.column)


class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class OrielCallable:
    @property
    def arity(self) -> int:
        raise NotImplementedError

    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        raise NotImplementedError


class UserFunction(OrielCallable):
    def __init__(self, declaration: FunctionStmt, closure: Environment):
        self.declaration = declaration
        self.closure = closure

    @property
    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        env = Environment(self.closure)
        for param, arg in zip(self.declaration.params, arguments):
            env.define(param.lexeme, arg, mutable=False)
        try:
            interpreter.execute_block(self.declaration.body, env)
        except ReturnSignal as signal:
            return signal.value
        return None

    def __repr__(self) -> str:
        return f"<fn {self.declaration.name.lexeme}>"


class NativeFunction(OrielCallable):
    def __init__(self, name: str, arity: int, function: Callable[..., Any]):
        self.name = name
        self._arity = arity
        self.function = function

    @property
    def arity(self) -> int:
        return self._arity

    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        try:
            return self.function(*arguments)
        except OrielError:
            raise
        except Exception as error:
            raise OrielError(f"{self.name} failed: {error}") from error

    def __repr__(self) -> str:
        return f"<native {self.name}>"


class Interpreter:
    def __init__(self, output: Callable[[str], None] | None = None):
        self.globals = Environment()
        self.environment = self.globals
        self.output = output or print
        natives = {
            "input": NativeFunction("input", 1, lambda prompt: input(str(prompt))),
            "len": NativeFunction("len", 1, len),
            "range": NativeFunction("range", 2, lambda start, end: list(range(int(start), int(end)))),
            "push": NativeFunction("push", 2, self._push),
            "read_file": NativeFunction("read_file", 1, lambda path: Path(str(path)).read_text(encoding="utf-8")),
            "write_file": NativeFunction("write_file", 2, self._write_file),
            "json_encode": NativeFunction("json_encode", 1, lambda value: json.dumps(value, ensure_ascii=False)),
            "json_decode": NativeFunction("json_decode", 1, json.loads),
            "type_of": NativeFunction("type_of", 1, self._type_of),
        }
        for name, native in natives.items():
            self.globals.define(name, native, mutable=False)

    def interpret(self, statements: list[Stmt]) -> None:
        for statement in statements:
            self.execute(statement)

        # Oriel convention: automatically call main() when it exists.
        if "main" in self.globals.values:
            main_value = self.globals.values["main"].value
            if isinstance(main_value, OrielCallable):
                if main_value.arity != 0:
                    raise OrielError("main() must not accept parameters.")
                main_value.call(self, [])

    def execute(self, stmt: Stmt) -> None:
        if isinstance(stmt, ExpressionStmt):
            self.evaluate(stmt.expression)
        elif isinstance(stmt, PrintStmt):
            self.output(self.stringify(self.evaluate(stmt.expression)))
        elif isinstance(stmt, VarStmt):
            self.environment.define(stmt.name.lexeme, self.evaluate(stmt.initializer), stmt.mutable)
        elif isinstance(stmt, BlockStmt):
            self.execute_block(stmt.statements, Environment(self.environment))
        elif isinstance(stmt, IfStmt):
            if self.is_truthy(self.evaluate(stmt.condition)):
                self.execute(stmt.then_branch)
            elif stmt.else_branch:
                self.execute(stmt.else_branch)
        elif isinstance(stmt, WhileStmt):
            while self.is_truthy(self.evaluate(stmt.condition)):
                self.execute(stmt.body)
        elif isinstance(stmt, ForStmt):
            iterable = self.evaluate(stmt.iterable)
            if not isinstance(iterable, (list, str)):
                raise OrielError("For loop requires a list or string.", stmt.name.line, stmt.name.column)
            for item in iterable:
                loop_env = Environment(self.environment)
                loop_env.define(stmt.name.lexeme, item, mutable=False)
                if isinstance(stmt.body, BlockStmt):
                    self.execute_block(stmt.body.statements, loop_env)
                else:
                    previous = self.environment
                    try:
                        self.environment = loop_env
                        self.execute(stmt.body)
                    finally:
                        self.environment = previous
        elif isinstance(stmt, FunctionStmt):
            self.environment.define(stmt.name.lexeme, UserFunction(stmt, self.environment), mutable=False)
        elif isinstance(stmt, ReturnStmt):
            raise ReturnSignal(None if stmt.value is None else self.evaluate(stmt.value))
        else:
            raise OrielError(f"Unknown statement type: {type(stmt).__name__}")

    def execute_block(self, statements: list[Stmt], environment: Environment) -> None:
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def evaluate(self, expr: Expr) -> Any:
        if isinstance(expr, Literal):
            return expr.value
        if isinstance(expr, Grouping):
            return self.evaluate(expr.expression)
        if isinstance(expr, Variable):
            return self.environment.get(expr.name)
        if isinstance(expr, Assign):
            value = self.evaluate(expr.value)
            self.environment.assign(expr.name, value)
            return value
        if isinstance(expr, Unary):
            right = self.evaluate(expr.right)
            if expr.operator.type == TokenType.MINUS:
                self.require_number(expr.operator, right)
                return -right
            if expr.operator.type == TokenType.BANG:
                return not self.is_truthy(right)
        if isinstance(expr, Binary):
            left = self.evaluate(expr.left)
            if expr.operator.type == TokenType.OR:
                return left if self.is_truthy(left) else self.evaluate(expr.right)
            if expr.operator.type == TokenType.AND:
                return self.evaluate(expr.right) if self.is_truthy(left) else left
            right = self.evaluate(expr.right)
            return self.binary(expr.operator, left, right)
        if isinstance(expr, ListLiteral):
            return [self.evaluate(item) for item in expr.items]
        if isinstance(expr, IndexExpr):
            target = self.evaluate(expr.target)
            index = self.evaluate(expr.index)
            if not isinstance(index, int) or isinstance(index, bool):
                raise OrielError("List and string indexes must be integers.", expr.bracket.line, expr.bracket.column)
            try:
                return target[index]
            except (TypeError, IndexError):
                raise OrielError("Index is invalid or out of range.", expr.bracket.line, expr.bracket.column)
        if isinstance(expr, Call):
            callee = self.evaluate(expr.callee)
            args = [self.evaluate(arg) for arg in expr.arguments]
            if not isinstance(callee, OrielCallable):
                raise OrielError("Can only call functions.", expr.paren.line, expr.paren.column)
            if len(args) != callee.arity:
                raise OrielError(
                    f"Expected {callee.arity} arguments but received {len(args)}.",
                    expr.paren.line,
                    expr.paren.column,
                )
            return callee.call(self, args)
        raise OrielError(f"Unknown expression type: {type(expr).__name__}")

    def binary(self, op: Token, left: Any, right: Any) -> Any:
        t = op.type
        if t == TokenType.PLUS:
            if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
                return left + right
            if isinstance(left, str) or isinstance(right, str):
                return self.stringify(left) + self.stringify(right)
            raise OrielError("Operator '+' requires numbers or strings.", op.line, op.column)
        if t in (TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            self.require_numbers(op, left, right)
            if t == TokenType.MINUS:
                return left - right
            if t == TokenType.STAR:
                return left * right
            if t == TokenType.SLASH:
                if right == 0:
                    raise OrielError("Division by zero.", op.line, op.column)
                return left / right
            if t == TokenType.PERCENT:
                if right == 0:
                    raise OrielError("Modulo by zero.", op.line, op.column)
                return left % right
        if t == TokenType.EQUAL_EQUAL:
            return left == right
        if t == TokenType.BANG_EQUAL:
            return left != right
        if t in (TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            self.require_numbers(op, left, right)
            return {
                TokenType.GREATER: left > right,
                TokenType.GREATER_EQUAL: left >= right,
                TokenType.LESS: left < right,
                TokenType.LESS_EQUAL: left <= right,
            }[t]
        raise OrielError("Unsupported operator.", op.line, op.column)

    @staticmethod
    def _push(values: Any, value: Any) -> Any:
        if not isinstance(values, list):
            raise ValueError("first argument must be a list")
        values.append(value)
        return values

    @staticmethod
    def _write_file(path: Any, content: Any) -> bool:
        Path(str(path)).write_text(str(content), encoding="utf-8")
        return True

    @staticmethod
    def _type_of(value: Any) -> str:
        if value is None:
            return "None"
        if isinstance(value, bool):
            return "Bool"
        if isinstance(value, int):
            return "Int"
        if isinstance(value, float):
            return "Float"
        if isinstance(value, str):
            return "Text"
        if isinstance(value, list):
            return "List"
        return type(value).__name__

    @staticmethod
    def is_truthy(value: Any) -> bool:
        return False if value is None else bool(value)

    @staticmethod
    def require_number(token: Token, value: Any) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise OrielError("Operand must be a number.", token.line, token.column)

    @classmethod
    def require_numbers(cls, token: Token, left: Any, right: Any) -> None:
        cls.require_number(token, left)
        cls.require_number(token, right)

    @staticmethod
    def stringify(value: Any) -> str:
        if value is None:
            return "none"
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)


def run_source(source: str, filename: str = "<source>", output: Callable[[str], None] | None = None) -> None:
    try:
        tokens = Lexer(source).scan_tokens()
        statements = Parser(tokens).parse()
        Interpreter(output=output).interpret(statements)
    except OrielError as error:
        raise RuntimeError(error.format(filename, source)) from error
