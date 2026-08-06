from oriel.typesystem import *

def test_parse_nested_generic_nullable():
    assert str(parse_type("Map<String, List<Int?>>")) == "Map<String, List<Int?>>"

def test_numeric_widening():
    assert is_assignable(parse_type("Int"), parse_type("Float"))
    assert not is_assignable(parse_type("Float"), parse_type("Int"))

def test_nullable_rules():
    assert is_assignable(parse_type("None"), parse_type("String?"))
    assert not is_assignable(parse_type("None"), parse_type("String"))

def test_literal_inference():
    assert str(infer_literal([1,2,3])) == "List<Int>"
    assert str(infer_literal([1,2.5])) == "List<Float>"

def test_function_signature():
    fn=FunctionType((parse_type("Int"), parse_type("String")), parse_type("Bool"))
    assert fn.accepts((parse_type("Int"), parse_type("String")))
    assert not fn.accepts((parse_type("String"), parse_type("String")))
