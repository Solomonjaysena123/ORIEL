from pathlib import Path
from oriel.interpreter import run_source
from oriel.cli import create_project, format_source


def capture(source: str):
    out=[]
    run_source(source, output=out.append)
    return out


def test_lists_for_and_index():
    source='''fn main() {
 let values = [10, 20, 30]
 for value in values {
  print(value)
 }
 print(values[1])
}'''
    assert capture(source) == ['10','20','30','20']


def test_json_and_push():
    source='''fn main() {
 let values = [1]
 push(values, 2)
 print(len(values))
 print(json_encode(values))
}'''
    assert capture(source) == ['2','[1, 2]']


def test_project_creation(tmp_path: Path):
    project=create_project('sample', tmp_path)
    assert (project/'src/main.orl').exists()
    assert (project/'tests/core_test.orl').exists()
    assert (project/'oriel.toml').exists()


def test_formatter():
    assert format_source('fn main() {\nprint("x")\n}\n') == 'fn main() {\n    print("x")\n}\n'
