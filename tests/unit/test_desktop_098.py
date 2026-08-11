import ctypes.util
import hashlib
import json
from pathlib import Path

import pytest

from oriel.desktop_framework import (
    DesktopBuildError, DesktopConfig, DesktopConfigurationError, DesktopPlatform,
    DesktopRenderer, DesktopWindow, MemoryFileDialogs, Menu, MenuItem, MockDesktopBackend, NativeLibrary, TrayIcon,
    UpdateInfo, UpdateService, WindowOptions, WindowState, build_desktop_project,
    create_desktop_project, package_desktop_project, validate_desktop_project,
)
from oriel.ui_engine import Layout, Semantics, UIContext, column, element


def config(**changes):
    values={"application_id":"org.oriel.desktop","name":"OrielDesktop","version":"1.2.3","description":"Desktop demo","publisher":"ORIEL Labs"}
    values.update(changes);return DesktopConfig(**values)


def test_window_lifecycle_and_events():
    window=DesktopWindow(WindowOptions("Demo",800,600,320,240)); events=[]
    remove=window.on("resize",lambda width,height:events.append((width,height)))
    window.show();window.resize(640,480);remove();window.resize(700,500)
    window.set_state(WindowState.MAXIMIZED);window.close()
    assert events==[(640,480)] and window.state==WindowState.CLOSED and not window.visible
    with pytest.raises(RuntimeError):window.show()
    with pytest.raises(ValueError):DesktopWindow(WindowOptions("Demo")).on("unknown",lambda:None)


def test_window_validation():
    with pytest.raises(DesktopConfigurationError):WindowOptions("")
    with pytest.raises(DesktopConfigurationError):WindowOptions("Demo",100,100,320,240)


def test_menu_activation_and_validation():
    selected=[];menu=Menu((MenuItem("file","File",children=(MenuItem("file.open","Open","Ctrl+O"),)),),selected.append)
    assert menu.activate("file.open") and selected==["file.open"]
    assert not menu.activate("file") and not menu.activate("missing")
    with pytest.raises(DesktopConfigurationError):Menu((MenuItem("same","One"),MenuItem("same","Two")))
    with pytest.raises(DesktopConfigurationError):MenuItem("bad id","Bad")


def test_tray_and_file_dialogs(tmp_path):
    icon=tmp_path/"icon.png";icon.write_bytes(b"png")
    assert TrayIcon(icon,"ORIEL").icon==icon
    dialogs=MemoryFileDialogs((tmp_path/"a.txt",None,tmp_path))
    assert dialogs.open_file(title="Open",filters=("*.txt",))==tmp_path/"a.txt"
    assert dialogs.save_file(title="Save",suggested_name="a.txt") is None
    assert dialogs.choose_directory(title="Folder")==tmp_path


def test_backend_external_links_notifications_and_renderer():
    backend=MockDesktopBackend();backend.clipboard_write("hello")
    assert backend.clipboard_read()=="hello"
    backend.show_notification("Ready","Desktop started");assert backend.notifications==[("Ready","Desktop started")]
    assert backend.open_external("https://oriel.example") and backend.open_external("mailto:team@oriel.example")
    assert not backend.open_external("file:///etc/passwd") and not backend.open_external("javascript:alert(1)")
    tree=column(element("heading","Title",semantics=Semantics(label="Title",heading_level=1)),element("button","Go"),gap=8)
    result=DesktopRenderer().render(tree,UIContext(platform="desktop"))
    assert result.root["view"]=="Panel" and result.root["children"][0]["props"]["automationName"]=="Title"
    assert DesktopRenderer().render(element("container",layout=Layout(display="grid",grid_columns=2)),UIContext()).root["view"]=="Grid"


def test_updates_are_https_versioned_and_verified(tmp_path):
    artifact=tmp_path/"update.bin";artifact.write_bytes(b"release")
    update=UpdateInfo("1.3.0","https://updates.oriel.example/app",hashlib.sha256(b"release").hexdigest())
    service=UpdateService("1.2.3")
    assert service.available(update) and service.verify(artifact,update)
    artifact.write_bytes(b"tampered");assert not service.verify(artifact,update)
    with pytest.raises(ValueError):UpdateInfo("1.3.0","http://unsafe.example/app","0"*64)


def test_native_library_allowlist():
    name=ctypes.util.find_library("c")
    if not name: pytest.skip("C runtime library unavailable")
    # Resolve an actual absolute library only where the runtime exposes one.
    candidates=[Path(name),Path("/lib/x86_64-linux-gnu")/name,Path("/usr/lib/x86_64-linux-gnu")/name]
    path=next((item for item in candidates if item.is_file()),None)
    if not path: pytest.skip("C runtime absolute path unavailable")
    library=NativeLibrary(path,("strlen",)).load()
    strlen=library.function("strlen",argtypes=(ctypes.c_char_p,),restype=ctypes.c_size_t)
    assert strlen(b"ORIEL")==5
    with pytest.raises(PermissionError):library.function("system")


def test_config_rejects_unsafe_values():
    for changes in ({"application_id":"bad"},{"name":"../bad"},{"version":"1.2"},{"platforms":()},{"update_feed":"http://unsafe.example/feed.json"}):
        with pytest.raises(DesktopConfigurationError):config(**changes)


def test_project_generation_and_validation(tmp_path):
    project=create_desktop_project(config(),tmp_path)
    assert validate_desktop_project(project)==[]
    metadata=json.loads((project/"desktop.json").read_text())
    assert metadata["orielVersion"]=="0.9.8" and metadata["platforms"]==["windows","macos","linux"]
    assert "<Wix" in (project/"packaging/windows/installer.wxs").read_text()
    assert "[Desktop Entry]" in (project/"packaging/linux/org.oriel.desktop.desktop").read_text()
    for target in DesktopPlatform:
        artifact=package_desktop_project(project,target=target)
        assert artifact.is_file() and artifact.with_name(artifact.name+".sha256").is_file()


def test_packaging_is_deterministic(tmp_path):
    project=create_desktop_project(config(),tmp_path)
    first=package_desktop_project(project,target=DesktopPlatform.WINDOWS).read_bytes()
    second=package_desktop_project(project,target=DesktopPlatform.WINDOWS).read_bytes()
    assert first==second


def test_project_target_and_release_validation(tmp_path):
    project=create_desktop_project(config(platforms=(DesktopPlatform.WINDOWS,)),tmp_path)
    assert any("not enabled" in item for item in validate_desktop_project(project,target=DesktopPlatform.LINUX))
    issues=validate_desktop_project(project,release=True,target=DesktopPlatform.WINDOWS,environment={})
    assert issues==["missing signing environment variable: ORIEL_WINDOWS_CERTIFICATE"]
    (project/"secret.pfx").write_bytes(b"secret")
    assert any("must not be stored" in item for item in validate_desktop_project(project))


def test_invalid_metadata_and_missing_toolchain(tmp_path,monkeypatch):
    project=create_desktop_project(config(),tmp_path)
    (project/"desktop.json").write_text("not json")
    assert any("invalid desktop metadata" in item for item in validate_desktop_project(project))
    project=create_desktop_project(config(name="Other"),tmp_path)
    monkeypatch.setattr("oriel.desktop_framework.shutil.which",lambda name:None)
    with pytest.raises(DesktopBuildError,match="PyInstaller"):build_desktop_project(project)
