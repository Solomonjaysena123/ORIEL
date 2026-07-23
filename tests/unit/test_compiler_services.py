from oriel.compiler_services import CompilerService


def test_valid_program_has_no_diagnostics():
    result = CompilerService().analyze('let answer = 42\nprint(answer)\n')
    assert result.is_valid
    assert result.diagnostics == ()


def test_invalid_program_returns_structured_diagnostic():
    result = CompilerService().analyze('let = 1\n')
    assert not result.is_valid
    diagnostic = result.diagnostics[0]
    assert diagnostic.code.startswith('E')
    assert diagnostic.message
    assert diagnostic.range.start.line >= 0
