import pytest

from oriel.interpreter import OrielError, analyze_source


def assert_error(source: str, code: str):
    with pytest.raises(OrielError) as exc:
        analyze_source(source)
    assert exc.value.code == code
    return exc.value


def test_nullable_type_accepts_none():
    analyze_source("let value: Int? = none\
")


def test_non_nullable_type_rejects_none():
    assert_error("let value: Int = none\
", "E202")


def test_typed_list_and_index_inference():
    analyze_source("let values: List[Int] = [1, 2, 3]\
let first: Int = values[0]\
")


def test_list_item_type_mismatch():
    assert_error('let values: List[Int] = [1, "two"]\
', "E202")


def test_assignment_checks_mutability_and_type():
    assert_error("let value: Int = 1\
value = 2\
", "E207")
    assert_error('var value: Int = 1\
value = "bad"\
', "E202")


def test_undefined_symbol_is_rejected():
    assert_error("print(missing)\
", "E212")


def test_function_arity_and_argument_types():
    source = "fn add(a: Int, b: Int) -> Int {\
 return a + b\
}\
add(1)\
"
    assert_error(source, "E213")
    source = 'fn add(a: Int, b: Int) -> Int {\
 return a + b\
}\
add(1, "two")\
'
    assert_error(source, "E202")


def test_return_path_analysis():
    source = "fn choose(flag: Bool) -> Int {\
 if flag {\
  return 1\
 }\
}\
"
    assert_error(source, "E206")


def test_all_if_paths_return():
    analyze_source("fn choose(flag: Bool) -> Int {\
 if flag {\
  return 1\
 } else {\
  return 2\
 }\
}\
")
