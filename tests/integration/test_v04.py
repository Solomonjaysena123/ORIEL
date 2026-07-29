from pathlib import Path
import json
from oriel.modules import load_module_graph, ModuleError
from oriel.api_framework import create_api_project, route_manifest
from oriel import package_manager


def test_module_graph(tmp_path: Path):
    (tmp_path/'src').mkdir()
    (tmp_path/'oriel.toml').write_text('[project]\nname="x"\nversion="0.1.0"\nentry="src/main.orl"\n[dependencies]\n',encoding='utf-8')
    (tmp_path/'src'/'util.orl').write_text('fn twice(x: Int) -> Int { return x * 2 }',encoding='utf-8')
    entry=tmp_path/'src'/'main.orl'; entry.write_text('use util\nfn main() { print(twice(3)) }',encoding='utf-8')
    source,files=load_module_graph(entry)
    assert 'fn twice' in source and len(files)==2


def test_api_project_and_routes(tmp_path: Path):
    root=create_api_project('demo-api',tmp_path)
    routes=route_manifest((root/'src/main.orl').read_text())
    assert routes[0]['method']=='GET'
    assert any(r['path']=='/health' for r in routes)


def test_transitive_packages(tmp_path: Path):
    (tmp_path/'oriel.toml').write_text('[project]\nname="x"\nversion="0.1.0"\nentry="src/main.orl"\n\n[dependencies]\n"oriel.api"="^0.1.0"\n',encoding='utf-8')
    assert package_manager.install(tmp_path) == 3
    lock=json.loads((tmp_path/'oriel.lock').read_text())
    assert lock['lock_version']==2
    assert {p['name'] for p in lock['packages']} == {'oriel.api','oriel.core','oriel.json'}
