import json
from pathlib import Path

import pytest

from oriel.android_framework import (
    AndroidBuildError,
    AndroidConfig,
    AndroidConfigurationError,
    AndroidLifecycle,
    AndroidNotification,
    AndroidPermission,
    AndroidRenderer,
    AndroidToolchain,
    BackgroundWork,
    BackgroundWorkManager,
    DeviceInfo,
    LifecycleState,
    MemoryNotificationBackend,
    MockAndroidDevice,
    NetworkRequirement,
    NotificationChannel,
    NotificationManager,
    PermissionManager,
    PermissionStatus,
    RuntimeConditions,
    WorkConstraints,
    build_android_project,
    create_android_project,
    validate_android_project,
)
from oriel.cli import build_parser
from oriel.ui_engine import EdgeInsets, Layout, Semantics, UIContext, column, element, text


def test_lifecycle_valid_transitions_observers_and_removal():
    lifecycle=AndroidLifecycle();events=[]
    remove=lifecycle.observe(events.append)
    for state in (
        LifecycleState.CREATED,LifecycleState.STARTED,LifecycleState.RESUMED,
        LifecycleState.PAUSED,LifecycleState.STOPPED,LifecycleState.DESTROYED,
    ):lifecycle.transition(state)
    remove()
    assert events[-1]==LifecycleState.DESTROYED
    with pytest.raises(RuntimeError,match="invalid"):
        lifecycle.transition(LifecycleState.STARTED)
    with pytest.raises(TypeError,match="callable"):
        AndroidLifecycle().observe(None)


def test_device_information_permissions_urls_and_vibration():
    backend=MockAndroidDevice(
        DeviceInfo(manufacturer="ORIEL",model="Pixel",features=frozenset({"camera"})),
        request_results={AndroidPermission.CAMERA:PermissionStatus.GRANTED},
    )
    permissions=PermissionManager(backend,[AndroidPermission.CAMERA])
    assert permissions.status(AndroidPermission.CAMERA)==PermissionStatus.NOT_DETERMINED
    assert permissions.request(AndroidPermission.CAMERA)==PermissionStatus.GRANTED
    permissions.require(AndroidPermission.CAMERA)
    with pytest.raises(PermissionError,match="not declared"):
        permissions.request(AndroidPermission.MICROPHONE)
    assert backend.open_url("https://oriel.example/path")
    assert not backend.open_url("javascript:alert(1)")
    backend.vibrate(250)
    assert backend.vibrations==[250]
    with pytest.raises(ValueError,match="vibration"):
        backend.vibrate(0)


def test_notification_channels_immediate_scheduled_delivery_and_cancel():
    backend=MemoryNotificationBackend();manager=NotificationManager(backend)
    manager.create_channel(NotificationChannel("updates","Updates",importance=4))
    manager.schedule(AndroidNotification("now","updates","Ready","Done"),now=10)
    manager.schedule(AndroidNotification("later","updates","Later","Wait",deliver_at=20),now=10)
    assert [item.notification_id for item in backend.published]==["now"]
    assert manager.deliver_due(now=19)==0
    assert manager.deliver_due(now=20)==1
    manager.schedule(AndroidNotification("cancel","updates","Cancel","Wait",deliver_at=30),now=20)
    manager.cancel("cancel")
    assert backend.cancelled==["cancel"]
    with pytest.raises(KeyError,match="unknown"):
        manager.schedule(AndroidNotification("bad","missing","Bad","Bad"))


def test_background_work_constraints_retries_completion_and_cancellation():
    calls=[];failures={"count":0}
    def sync(payload):
        calls.append(payload["value"])
        if failures["count"]<1:
            failures["count"]+=1
            raise RuntimeError("temporary")
    manager=BackgroundWorkManager({"sync":sync})
    work=BackgroundWork(
        "sync",{"value":7},WorkConstraints(network=NetworkRequirement.UNMETERED,requires_charging=True),
        delay_seconds=5,max_attempts=3,backoff_seconds=10,
    )
    work_id=manager.enqueue(work,now=100)
    assert manager.run_due(now=104)==0
    assert manager.run_due(now=105,conditions=RuntimeConditions(unmetered=False))==0
    assert manager.run_due(now=105)==1
    record=manager.records[work_id]
    assert record.run_at==115 and record.attempts==1 and not record.completed
    assert manager.run_due(now=114)==0
    assert manager.run_due(now=115)==1
    assert record.completed and record.last_error is None and calls==[7,7]
    cancelled=manager.enqueue(BackgroundWork("sync"),now=0)
    assert manager.cancel(cancelled)
    assert manager.run_due(now=10)==0


def test_background_work_rejects_invalid_payload_and_missing_handler():
    with pytest.raises(TypeError,match="JSON"):
        BackgroundWork("bad",{"set":{1}})
    manager=BackgroundWorkManager()
    manager.enqueue(BackgroundWork("missing"),now=0)
    with pytest.raises(KeyError,match="no background handler"):
        manager.run_due(now=0)


def test_android_config_validation():
    config=AndroidConfig("org.oriel.demo","Demo",version_name="1.2.3",version_code=12,min_sdk=24,target_sdk=35,compile_sdk=35)
    assert config.application_id=="org.oriel.demo"
    for kwargs in (
        {"application_id":"Demo"},{"app_name":"../bad"},{"version_name":"1.2"},
        {"version_code":0},{"min_sdk":36,"target_sdk":35},
    ):
        values={"application_id":"org.oriel.demo","app_name":"Demo",**kwargs}
        with pytest.raises(AndroidConfigurationError):
            AndroidConfig(**values)


def test_android_renderer_maps_ui_layout_and_accessibility():
    tree=column(
        element("heading","Title",semantics=Semantics(role="heading",label="Title",heading_level=1)),
        element("button","Continue",semantics=Semantics(role="button",label="Continue")),
        gap=16,
    )
    rendered=AndroidRenderer().render(tree,UIContext(platform="android",density=2))
    assert rendered.platform=="android"
    assert rendered.root["view"]=="LinearLayout"
    assert rendered.root["layout"]["gapDp"]==16
    assert rendered.root["children"][0]["view"]=="TextView"
    assert rendered.root["children"][0]["props"]["accessibilityHeading"] is True
    assert rendered.root["children"][1]["props"]["contentDescription"]=="Continue"


def test_android_renderer_grid_stack_spacing_and_diagnostics():
    node=element(
        "container",
        element("image",src="photo.png"),
        layout=Layout(display="grid",grid_columns=2,padding=EdgeInsets.all(8)),
    )
    result=AndroidRenderer().render(node,UIContext())
    assert result.root["view"]=="GridLayout"
    assert result.root["layout"]["gridColumns"]==2
    assert result.root["layout"]["paddingDp"]==[8,8,8,8]
    assert any("alternative text" in issue for issue in result.diagnostics)
    stacked=AndroidRenderer().render(element("container",text("x"),layout=Layout(display="stack")),UIContext())
    assert stacked.root["view"]=="FrameLayout"


def _config(**overrides):
    values={
        "application_id":"org.oriel.sample","app_name":"SampleAndroid","version_name":"1.0.0",
        "version_code":1,"permissions":(AndroidPermission.CAMERA,AndroidPermission.NOTIFICATIONS),
    }
    values.update(overrides)
    return AndroidConfig(**values)


def test_project_generator_writes_gradle_manifest_resources_and_no_secrets(tmp_path:Path):
    project=create_android_project(_config(),tmp_path)
    manifest=(project/"app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
    gradle=(project/"app/build.gradle.kts").read_text(encoding="utf-8")
    activity=next((project/"app/src/main/java").rglob("MainActivity.kt")).read_text(encoding="utf-8")
    metadata=json.loads((project/"app/src/main/assets/oriel-android.json").read_text(encoding="utf-8"))
    assert "android.permission.CAMERA" in manifest
    assert 'android:usesCleartextTraffic="false"' in manifest
    assert 'applicationId = "org.oriel.sample"' in gradle
    assert "sourceCompatibility = JavaVersion.VERSION_17" in gradle
    assert 'jvmTarget = "17"' in gradle
    assert "ORIEL_ANDROID_KEYSTORE" in gradle
    assert "storePassword =" in gradle and "password123" not in gradle
    assert "package org.oriel.sample" in activity
    assert metadata["orielVersion"]=="0.9.6"
    assert validate_android_project(project)==[]
    with pytest.raises(FileExistsError):
        create_android_project(_config(),tmp_path)


def test_project_generator_escapes_display_name(tmp_path:Path):
    project=create_android_project(_config(app_name="Rock & Roll"),tmp_path)
    assert "Rock &amp; Roll" in (project/"app/src/main/res/values/strings.xml").read_text(encoding="utf-8")
    assert 'Rock & Roll' in next((project/"app/src/main/java").rglob("MainActivity.kt")).read_text(encoding="utf-8")


def test_store_readiness_requires_signing_and_rejects_keys(tmp_path:Path):
    project=create_android_project(_config(),tmp_path)
    issues=validate_android_project(project,store_ready=True,environment={})
    assert len([issue for issue in issues if "signing environment" in issue])==4
    env={
        "ORIEL_ANDROID_KEYSTORE":"outside-project.jks","ORIEL_ANDROID_STORE_PASSWORD":"secret",
        "ORIEL_ANDROID_KEY_ALIAS":"release","ORIEL_ANDROID_KEY_PASSWORD":"secret",
    }
    assert validate_android_project(project,store_ready=True,environment=env)==[]
    (project/"release.jks").write_bytes(b"secret")
    assert any("must not be stored" in issue for issue in validate_android_project(project,environment=env))


def test_project_validation_detects_missing_and_malformed_files(tmp_path:Path):
    project=tmp_path/"broken";project.mkdir()
    issues=validate_android_project(project)
    assert any("settings.gradle.kts" in issue for issue in issues)
    manifest=project/"app/src/main";manifest.mkdir(parents=True)
    (manifest/"AndroidManifest.xml").write_text("<manifest>",encoding="utf-8")
    assert any("invalid AndroidManifest" in issue for issue in validate_android_project(project))


def test_toolchain_detection_and_build_gap(tmp_path:Path,monkeypatch):
    monkeypatch.setattr("oriel.android_framework.shutil.which",lambda name:None)
    assert not AndroidToolchain.detect(environment={}).available
    project=create_android_project(_config(),tmp_path)
    with pytest.raises(AndroidBuildError,match="requires Java"):
        build_android_project(project)


def test_android_cli_contract(tmp_path:Path):
    parser=build_parser()
    args=parser.parse_args([
        "android","new","Demo","--path",str(tmp_path),"--application-id","org.oriel.demo",
        "--version-name","1.2.0","--version-code","12","--permission","camera",
    ])
    assert args.android_command=="new"
    assert args.application_id=="org.oriel.demo"
    assert args.permission==["camera"]
