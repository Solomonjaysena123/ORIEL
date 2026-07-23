
from pathlib import Path
import json
import pytest
from oriel.interpreter import Lexer, Parser, TypeChecker, OrielError, run_source
from oriel import package_manager


def check(src):
    statements=Parser(Lexer(src).scan_tokens()).parse(); TypeChecker().check(statements)


def test_typed_program_runs():
    out=[]
    run_source('fn add(a: Int, b: Int) -> Int { return a + b }\nfn main() { let total: Int = add(2, 3)\nprint(total) }', output=out.append)
    assert out == ['5']


def test_type_mismatch_has_code():
    with pytest.raises(OrielError) as exc:
        check('fn main() { let quantity: Int = "ten" }')
    assert exc.value.code == 'E202'


def test_package_lock(tmp_path: Path):
    (tmp_path/'oriel.toml').write_text('[project]\nname="x"\nversion="0.1.0"\nentry="src/main.orl"\n\n[dependencies]\n', encoding='utf-8')
    package_manager.add(tmp_path, 'oriel.text')
    lock=json.loads((tmp_path/'oriel.lock').read_text())
    assert lock['packages'][0]['name'] == 'oriel.text'
    package_manager.remove(tmp_path, 'oriel.text')
