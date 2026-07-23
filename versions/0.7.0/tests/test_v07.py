from pathlib import Path
import tempfile
from oriel.console_tools import write_bytecode, run_bytecode, generate_docs, doctor

SOURCE='fn main() { print("hello") }'

def test_bytecode(capsys):
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); src=root/'main.orl'; src.write_text(SOURCE)
        bytecode=write_bytecode(src)
        assert bytecode.exists()
        run_bytecode(bytecode)
        assert 'hello' in capsys.readouterr().out

def test_docs():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); src=root/'main.orl'; out=root/'API.md'
        src.write_text('fn add(a: Int, b: Int) -> Int { return a + b }')
        generate_docs(src, out)
        assert '`add(a: Int, b: Int)`' in out.read_text()

def test_doctor():
    assert doctor()['oriel'] == 'ok'
