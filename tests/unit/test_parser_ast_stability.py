import pytest

from oriel.ast import FunctionStmt, PrintStmt
from oriel.diagnostics import OrielError
from oriel.lexer import Lexer
from oriel.parser import Parser


def parse(source: str):
    return Parser(Lexer(source).scan_tokens()).parse()


def test_function_ast_shape_is_stable():
    statements = parse('fn main() {\n print("ok")\n}')
    assert len(statements) == 1
    assert isinstance(statements[0], FunctionStmt)
    assert isinstance(statements[0].body[0], PrintStmt)


def test_missing_closing_brace_has_parser_code():
    with pytest.raises(OrielError) as exc:
        parse('fn main() {\n print("ok")')
    assert exc.value.code == 'E2002'
