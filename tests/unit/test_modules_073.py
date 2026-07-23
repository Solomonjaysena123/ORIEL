from pathlib import Path
import pytest

from oriel.modules import ModuleError, build_module_graph, load_module_graph, parse_imports


def make_project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "oriel.toml").write_text('[project]\nname="demo"\nversion="0.7.3"\nentry="src/main.orl"\n', encoding="utf-8")
    return tmp_path / "src"


def test_import_metadata_supports_alias_and_public():
    imports = parse_imports('public use tools.math as maths\nuse "local.orl"\n')
    assert imports[0].name == "tools.math"
    assert imports[0].alias == "maths"
    assert imports[0].public is True
    assert imports[1].name == "local.orl"


def test_duplicate_alias_is_rejected():
    with pytest.raises(ModuleError, match="Duplicate module alias"):
        parse_imports("use alpha as shared\nuse beta as shared\n")


def test_deterministic_dependency_order(tmp_path: Path):
    src = make_project(tmp_path)
    (src / "a.orl").write_text("fn a() -> Int { return 1 }", encoding="utf-8")
    (src / "b.orl").write_text("use a\nfn b() -> Int { return a() }", encoding="utf-8")
    entry = src / "main.orl"
    entry.write_text("use b\nfn main() { print(b()) }", encoding="utf-8")
    graph = build_module_graph(entry)
    assert [p.name for p in graph.ordered_files] == ["a.orl", "b.orl", "main.orl"]
    assert graph.relative_files() == ["src/a.orl", "src/b.orl", "src/main.orl"]


def test_path_import_cannot_escape_project(tmp_path: Path):
    src = make_project(tmp_path)
    outside = tmp_path.parent / "outside.orl"
    outside.write_text("fn outside() {}", encoding="utf-8")
    entry = src / "main.orl"
    entry.write_text('use "../../outside.orl"\nfn main() {}', encoding="utf-8")
    with pytest.raises(ModuleError, match="outside the allowed project root"):
        build_module_graph(entry)


def test_stdlib_module_is_loaded(tmp_path: Path):
    src = make_project(tmp_path)
    entry = src / "main.orl"
    entry.write_text('use oriel.text\nfn main() { print(text_length("ORIEL")) }', encoding="utf-8")
    source, files = load_module_graph(entry)
    assert "fn text_length" in source
    assert files[-1] == entry.resolve()
