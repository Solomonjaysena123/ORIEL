import json, plistlib
from pathlib import Path
import pytest
from oriel.mobile_framework import *
from oriel.ui_engine import Layout,Semantics,UIContext,column,element

def config(**changes):
    values={"bundle_id":"org.oriel.demo","app_name":"OrielMobile","version":"1.2.0","build_number":12,"permissions":{IOSPermission.CAMERA:"Camera access"}}
    values.update(changes);return IOSConfig(**values)

def test_ios_lifecycle_and_device():
    lifecycle=IOSLifecycle();seen=[];lifecycle.observe(seen.append)
    for state in (IOSLifecycleState.INACTIVE,IOSLifecycleState.ACTIVE,IOSLifecycleState.BACKGROUND,IOSLifecycleState.TERMINATED):lifecycle.transition(state)
    assert seen[-1]==IOSLifecycleState.TERMINATED
    with pytest.raises(RuntimeError):lifecycle.transition(IOSLifecycleState.ACTIVE)
    device=MockIOSDevice();assert device.open_url("https://oriel.example");assert not device.open_url("javascript:x")
    device.haptic("success");assert device.haptics==["success"]

def test_ios_config_validation():
    assert config().bundle_id=="org.oriel.demo"
    for values in ({"bundle_id":"bad"},{"app_name":"../bad"},{"version":"1.2"},{"build_number":0},{"team_id":"bad"},{"permissions":{IOSPermission.CAMERA:""}}):
        with pytest.raises(MobileConfigurationError):config(**values)

def test_ios_renderer():
    tree=column(element("heading","Title",semantics=Semantics(label="Title",heading_level=1)),element("button","Go",semantics=Semantics(label="Go")),gap=8)
    result=IOSRenderer().render(tree,UIContext(platform="ios"))
    assert result.root["view"]=="UIStackView";assert result.root["children"][0]["props"]["accessibilityTraits"]==["header"]
    grid=IOSRenderer().render(element("container",layout=Layout(display="grid",grid_columns=2)),UIContext())
    assert grid.root["view"]=="UICollectionView"

def test_ios_project_generation_and_validation(tmp_path):
    project=create_ios_project(config(background_modes=("fetch","remote-notification")),tmp_path)
    assert validate_ios_project(project)==[]
    with (project/"Resources/Info.plist").open("rb") as stream:info=plistlib.load(stream)
    assert info["NSCameraUsageDescription"]=="Camera access";assert info["UIBackgroundModes"]==["fetch","remote-notification"]
    assert "PRODUCT_BUNDLE_IDENTIFIER: org.oriel.demo" in (project/"project.yml").read_text()
    assert json.loads((project/"oriel-mobile.json").read_text())["orielVersion"]=="0.9.7"

def test_ios_store_validation(tmp_path):
    project=create_ios_project(config(),tmp_path)
    assert len([x for x in validate_ios_project(project,store_ready=True,environment={}) if "signing environment" in x])==3
    env={"ORIEL_APPLE_TEAM_ID":"ABCDEFGHIJ","ORIEL_APPLE_SIGNING_IDENTITY":"Apple Distribution","ORIEL_APPLE_PROVISIONING_PROFILE":"profile"}
    assert validate_ios_project(project,store_ready=True,environment=env)==[]
    (project/"secret.p12").write_bytes(b"x")
    assert any("must not be stored" in x for x in validate_ios_project(project))

def test_unified_mobile_project(tmp_path):
    root=create_mobile_project(UnifiedMobileConfig("Unified","org.oriel.unified","1.0.0",1),tmp_path)
    assert validate_mobile_project(root)==[]
    meta=json.loads((root/"mobile.json").read_text())
    assert (root/meta["android"]).is_dir() and (root/meta["ios"]).is_dir()

def test_invalid_mobile_metadata(tmp_path):
    root=tmp_path/"bad";root.mkdir()
    assert "invalid unified" in validate_mobile_project(root)[0]

def test_missing_toolchain(tmp_path,monkeypatch):
    project=create_ios_project(config(),tmp_path)
    monkeypatch.setattr("oriel.mobile_framework.shutil.which",lambda name:None)
    with pytest.raises(MobileBuildError,match="macOS"):build_ios_project(project)

def test_device_info_validation():
    assert IOSDeviceInfo(idiom="pad").idiom=="pad"
    with pytest.raises(ValueError):IOSDeviceInfo(idiom="watch")
