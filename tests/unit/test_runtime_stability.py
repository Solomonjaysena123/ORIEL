import pytest

from oriel.runtime import run_source


def capture(source: str):
    output = []
    run_source(source, 'test.orl', output.append)
    return output


def test_main_executes_once():
    assert capture('fn main() { print("ok") }') == ['ok']


def test_duplicate_declaration_is_rejected():
    with pytest.raises(RuntimeError) as exc:
        capture('fn main() {\n let x = 1\n let x = 2\n}')
    assert 'E3003' in str(exc.value)


def test_top_level_return_is_rejected_cleanly():
    with pytest.raises(RuntimeError) as exc:
        capture('return 1')
    assert 'E3004' in str(exc.value)


def test_division_by_zero_has_runtime_code():
    with pytest.raises(RuntimeError) as exc:
        capture('fn main() { print(10 / 0) }')
    assert 'E6002' in str(exc.value)
