from pathlib import Path
from oriel.cli import check_file
from oriel.interpreter import run_source
from oriel.modules import load_module_graph


def test_multimodule_stdlib_program(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "oriel.toml").write_text('[project]\nname="demo"\nversion="0.7.3"\nentry="src/main.orl"\n', encoding="utf-8")
    (tmp_path / "src" / "numbers.orl").write_text("public fn doubled(value: Int) -> Int { return value * 2 }", encoding="utf-8")
    entry = tmp_path / "src" / "main.orl"
    entry.write_text('use oriel.text\nuse numbers as nums\nfn main() { print(doubled(text_length("abc"))) }', encoding="utf-8")
    check_file(entry)
    source, _ = load_module_graph(entry)
    output: list[str] = []
    run_source(source, str(entry), output.append)
    assert output == ["6"]
