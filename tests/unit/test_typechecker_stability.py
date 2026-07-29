import pytest

from oriel.interpreter import analyze_source


def test_unknown_identifier_is_rejected_before_runtime():
    with pytest.raises(Exception) as exc:
        analyze_source('fn main() { print(missing) }')
    assert 'Undefined variable' in str(exc.value)


def test_function_arity_is_checked_statically():
    source = '''
fn add(a: Int, b: Int) -> Int { return a + b }
fn main() { print(add(1)) }
'''
    with pytest.raises(Exception) as exc:
        analyze_source(source)
    assert 'expects 2 arguments' in str(exc.value)
