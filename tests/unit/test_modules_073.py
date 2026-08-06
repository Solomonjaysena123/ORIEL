from pathlib import Path
import pytest
from oriel.standard_library import resolve_standard_module, list_modules
from oriel.module_resolver import imports, resolve_graph, ModuleResolutionError

def test_standard_library_registry():
    assert len(list_modules()) >= 10
    assert "encode" in resolve_standard_module("oriel.json").exports

def test_import_extraction():
    assert imports("use app.services\nuse oriel.json\n") == ("app.services","oriel.json")

def test_graph_resolution(tmp_path: Path):
    (tmp_path/'main.orl').write_text('use services.inventory\n')
    (tmp_path/'services').mkdir(); (tmp_path/'services/inventory.orl').write_text('fn all() {}')
    graph=resolve_graph(tmp_path/'main.orl',tmp_path)
    assert 'services.inventory' in graph.files

def test_cycle_detection(tmp_path: Path):
    (tmp_path/'a.orl').write_text('use b\n'); (tmp_path/'b.orl').write_text('use a\n')
    with pytest.raises(ModuleResolutionError): resolve_graph(tmp_path/'a.orl',tmp_path)
