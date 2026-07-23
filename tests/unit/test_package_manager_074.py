from pathlib import Path
import json
from oriel import package_manager as pm

def project(root,name='app',version='1.0.0'):
    root.mkdir(parents=True)
    (root/'oriel.toml').write_text(f'[project]\nname="{name}"\nversion="{version}"\nentry="src/main.orl"\n\n[dependencies]\n')
    (root/'src').mkdir();(root/'src/main.orl').write_text('fn main() { print("ok") }')
    return root

def test_path_dependency_and_lock(tmp_path):
    dep=project(tmp_path/'dep','dep','1.2.0');app=project(tmp_path/'app')
    pm.add(app,'dep',path='../dep')
    lock=json.loads((app/'oriel.lock').read_text())
    assert lock['lock_version']==2 and lock['packages'][0]['version']=='1.2.0'
    assert (app/'.oriel/packages/dep/src/main.orl').exists()

def test_publish_to_local_registry(tmp_path):
    app=project(tmp_path/'pkg','sample','1.0.0');registry=tmp_path/'registry'
    archive=pm.publish(app,registry)
    assert archive.exists() and (registry/'index.json').exists()
