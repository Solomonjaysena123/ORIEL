import pytest

from oriel.diagnostics import OrielError
from oriel.lexer import Lexer, TokenType


def test_tokens_track_line_and_column():
    tokens = Lexer('let name = "ORIEL"\nprint(name)').scan_tokens()
    let_token = tokens[0]
    print_token = next(t for t in tokens if t.type is TokenType.PRINT)
    assert (let_token.line, let_token.column) == (1, 1)
    assert (print_token.line, print_token.column) == (2, 1)


def test_unexpected_character_has_lexer_code():
    with pytest.raises(OrielError) as exc:
        Lexer('@').scan_tokens()
    assert exc.value.code == 'E1001'
    assert exc.value.line == 1
    assert exc.value.column == 1


def test_unterminated_string_has_actionable_help():
    with pytest.raises(OrielError) as exc:
        Lexer('print("broken)').scan_tokens()
    assert exc.value.code == 'E1002'
    assert 'closing double quote' in (exc.value.help_text or '')
