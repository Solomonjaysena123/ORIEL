"""ORIEL 0.9.8 cross-platform desktop framework."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.parse
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Mapping, Protocol


class DesktopConfigurationError(ValueError):
    pass


class DesktopBuildError(RuntimeError):
    pass


class DesktopPlatform(str, Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"

    @classmethod
    def current(cls) -> "DesktopPlatform":
        names = {"Windows": cls.WINDOWS, "Darwin": cls.MACOS, "Linux": cls.LINUX}
        try:
            return names[platform.system()]
        except KeyError as error:
            raise RuntimeError(f"unsupported desktop platform: {platform.system()}") from error


class WindowState(str, Enum):
    NORMAL = "normal"
    MINIMIZED = "minimized"
    MAXIMIZED = "maximized"
    FULLSCREEN = "fullscreen"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class WindowOptions:
    title: str
    width: int = 1024
    height: int = 720
    min_width: int = 320
    min_height: int = 240
    resizable: bool = True
    transparent: bool = False

    def __post_init__(self) -> None:
        if not self.title.strip() or "\n" in self.title or "\r" in self.title:
            raise DesktopConfigurationError("window title must be non-empty and single-line")
        if self.width < self.min_width or self.height < self.min_height or self.min_width < 1 or self.min_height < 1:
            raise DesktopConfigurationError("window dimensions must be positive and respect minimum dimensions")


class DesktopWindow:
    """Deterministic window contract suitable for native backends and tests."""

    def __init__(self, options: WindowOptions):
        self.options = options
        self.state = WindowState.NORMAL
        self.visible = False
        self._listeners: dict[str, list[Callable[..., None]]] = {}

    def on(self, event: str, callback: Callable[..., None]) -> Callable[[], None]:
        if event not in {"show", "hide", "focus", "resize", "state", "close"}:
            raise ValueError(f"unsupported window event: {event}")
        if not callable(callback):
            raise TypeError("window listener must be callable")
        self._listeners.setdefault(event, []).append(callback)
        return lambda: self._listeners[event].remove(callback) if callback in self._listeners.get(event, []) else None

    def _emit(self, event: str, *values: object) -> None:
        for callback in tuple(self._listeners.get(event, ())):
            callback(*values)

    def show(self) -> None:
        self._ensure_open(); self.visible = True; self._emit("show")

    def hide(self) -> None:
        self._ensure_open(); self.visible = False; self._emit("hide")

    def resize(self, width: int, height: int) -> None:
        self._ensure_open()
        if width < self.options.min_width or height < self.options.min_height:
            raise ValueError("window size is below its configured minimum")
        self._emit("resize", width, height)

    def set_state(self, state: WindowState) -> None:
        self._ensure_open()
        if state == WindowState.CLOSED:
            self.close(); return
        self.state = state; self._emit("state", state)

    def close(self) -> None:
        if self.state != WindowState.CLOSED:
            self.visible = False; self.state = WindowState.CLOSED; self._emit("close")

    def _ensure_open(self) -> None:
        if self.state == WindowState.CLOSED:
            raise RuntimeError("window is closed")


@dataclass(frozen=True, slots=True)
class MenuItem:
    identifier: str
    label: str
    shortcut: str | None = None
    enabled: bool = True
    separator: bool = False
    children: tuple["MenuItem", ...] = ()

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", self.identifier):
            raise DesktopConfigurationError("invalid menu item identifier")
        if not self.separator and not self.label.strip():
            raise DesktopConfigurationError("menu label must not be empty")
        if self.shortcut and not re.fullmatch(r"(?:Ctrl|Cmd|Alt|Shift)(?:\+(?:Ctrl|Cmd|Alt|Shift))*\+[A-Za-z0-9]", self.shortcut):
            raise DesktopConfigurationError("invalid keyboard shortcut")


class Menu:
    def __init__(self, items: Iterable[MenuItem], handler: Callable[[str], None] | None = None):
        self.items = tuple(items); self.handler = handler
        identifiers: list[str] = []
        def walk(values: Iterable[MenuItem]) -> None:
            for item in values:
                identifiers.append(item.identifier); walk(item.children)
        walk(self.items)
        if len(identifiers) != len(set(identifiers)):
            raise DesktopConfigurationError("menu item identifiers must be unique")

    def activate(self, identifier: str) -> bool:
        def find(values: Iterable[MenuItem]) -> MenuItem | None:
            for item in values:
                if item.identifier == identifier: return item
                match = find(item.children)
                if match: return match
            return None
        item = find(self.items)
        if not item or not item.enabled or item.separator or item.children: return False
        if self.handler: self.handler(identifier)
        return True


@dataclass(frozen=True, slots=True)
class TrayIcon:
    icon: Path
    tooltip: str
    menu: Menu | None = None

    def __post_init__(self) -> None:
        if not self.icon.is_file(): raise FileNotFoundError(self.icon)
        if not self.tooltip.strip() or "\n" in self.tooltip: raise DesktopConfigurationError("tray tooltip must be single-line")


class FileDialogBackend(Protocol):
    def open_file(self, *, title: str, filters: tuple[str, ...]) -> Path | None: ...
    def save_file(self, *, title: str, suggested_name: str) -> Path | None: ...
    def choose_directory(self, *, title: str) -> Path | None: ...


class MemoryFileDialogs:
    def __init__(self, responses: Iterable[Path | None] = ()): self.responses = list(responses); self.calls: list[tuple[str, object]] = []
    def _next(self) -> Path | None: return self.responses.pop(0) if self.responses else None
    def open_file(self, *, title: str, filters: tuple[str, ...] = ()) -> Path | None: self.calls.append(("open", filters)); return self._next()
    def save_file(self, *, title: str, suggested_name: str) -> Path | None: self.calls.append(("save", suggested_name)); return self._next()
    def choose_directory(self, *, title: str) -> Path | None: self.calls.append(("directory", title)); return self._next()


class DesktopBackend(Protocol):
    def clipboard_write(self, text: str) -> None: ...
    def clipboard_read(self) -> str: ...
    def show_notification(self, title: str, body: str) -> None: ...
    def open_external(self, uri: str) -> bool: ...


class MockDesktopBackend:
    """Safe deterministic backend for application tests and headless CI."""

    def __init__(self) -> None:
        self.clipboard = ""
        self.notifications: list[tuple[str, str]] = []
        self.external_uris: list[str] = []

    def clipboard_write(self, text: str) -> None:
        if not isinstance(text, str): raise TypeError("clipboard text must be a string")
        self.clipboard = text

    def clipboard_read(self) -> str: return self.clipboard

    def show_notification(self, title: str, body: str) -> None:
        if not title.strip() or any(char in title + body for char in "\r\x00"): raise ValueError("invalid notification content")
        self.notifications.append((title, body))

    def open_external(self, uri: str) -> bool:
        parsed = urllib.parse.urlparse(uri)
        if parsed.scheme not in {"https", "mailto"} or not parsed.netloc and parsed.scheme != "mailto": return False
        if any(char in uri for char in "\r\n\x00"): return False
        self.external_uris.append(uri); return True


class DesktopRenderer:
    """Maps shared ORIEL UI nodes to backend-neutral desktop controls."""

    platform = "desktop"
    _controls = {"container": "Panel", "text": "Text", "heading": "Text", "button": "Button", "image": "Image", "input": "TextField", "link": "Link"}

    def render(self, node, context):
        from .ui_engine import RenderTree, validate_tree
        diagnostics = tuple(validate_tree(node))
        def encode(current):
            layout = current.layout
            view = "Grid" if current.kind == "container" and layout and layout.display == "grid" else "Overlay" if current.kind == "container" and layout and layout.display == "stack" else self._controls.get(current.kind, "Control")
            props = dict(current.props)
            if current.kind in {"text", "heading"}: props["text"] = props.pop("value", "")
            if current.semantics:
                props.update(automationName=current.semantics.label, automationHelp=current.semantics.hint, enabled=current.semantics.enabled, accessibilityHidden=current.semantics.hidden)
                if current.semantics.heading_level: props["headingLevel"] = current.semantics.heading_level
            encoded_layout = None if not layout else {"display": layout.display, "direction": layout.direction, "gap": layout.gap, "width": layout.width, "height": layout.height, "align": layout.align, "justify": layout.justify, "grow": layout.grow}
            return {"view": view, "key": current.key, "props": props, "layout": encoded_layout, "children": [encode(child) for child in current.children]}
        return RenderTree(self.platform, encode(node), diagnostics)


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    version: str
    url: str
    sha256: str
    notes: str = ""

    def __post_init__(self) -> None:
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", self.version): raise ValueError("invalid update version")
        parsed = urllib.parse.urlparse(self.url)
        if parsed.scheme != "https" or not parsed.netloc: raise ValueError("update URL must use HTTPS")
        if not re.fullmatch(r"[a-fA-F0-9]{64}", self.sha256): raise ValueError("invalid SHA-256 checksum")


class UpdateService:
    def __init__(self, current_version: str):
        if not re.fullmatch(r"\d+\.\d+\.\d+", current_version): raise ValueError("invalid current version")
        self.current_version = current_version

    @staticmethod
    def _parts(version: str) -> tuple[int, int, int]: return tuple(int(part) for part in version.split("-", 1)[0].split(".", 2))  # type: ignore[return-value]
    def available(self, update: UpdateInfo) -> bool: return self._parts(update.version) > self._parts(self.current_version)
    def verify(self, artifact: Path, update: UpdateInfo) -> bool:
        digest = hashlib.sha256()
        with artifact.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""): digest.update(block)
        return digest.hexdigest().lower() == update.sha256.lower()


class NativeLibrary:
    """Explicit, allow-listed native interoperability boundary."""

    def __init__(self, path: Path, allowed_symbols: Iterable[str]):
        resolved = path.expanduser().resolve(strict=True)
        if resolved.suffix.lower() not in {".dll", ".dylib", ".so"} and ".so." not in resolved.name:
            raise ValueError("native library must be a DLL, dylib, or shared object")
        self.path = resolved; self.allowed_symbols = frozenset(allowed_symbols); self._library: object | None = None
        if not self.allowed_symbols or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol) for symbol in self.allowed_symbols):
            raise ValueError("native symbols must be explicitly allow-listed")

    def load(self) -> "NativeLibrary": self._library = ctypes.CDLL(str(self.path)); return self
    def function(self, symbol: str, *, argtypes: tuple[object, ...] = (), restype: object = ctypes.c_int):
        if symbol not in self.allowed_symbols: raise PermissionError(f"native symbol is not allow-listed: {symbol}")
        if self._library is None: raise RuntimeError("native library is not loaded")
        function = getattr(self._library, symbol); function.argtypes = list(argtypes); function.restype = restype
        return function


@dataclass(frozen=True, slots=True)
class DesktopConfig:
    application_id: str
    name: str
    version: str = "0.1.0"
    description: str = "ORIEL desktop application"
    publisher: str = "ORIEL"
    platforms: tuple[DesktopPlatform, ...] = tuple(DesktopPlatform)
    minimum_windows: str = "10"
    minimum_macos: str = "12.0"
    update_feed: str | None = None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*(?:\.[A-Za-z0-9-]+)+", self.application_id): raise DesktopConfigurationError("invalid application identifier")
        if not self.name.strip() or self.name in {".", ".."} or any(char in self.name for char in '\\/:*?"<>|\r\n\x00'): raise DesktopConfigurationError("unsafe application name")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", self.version): raise DesktopConfigurationError("version must use semantic versioning")
        if not self.platforms or len(set(self.platforms)) != len(self.platforms): raise DesktopConfigurationError("at least one unique desktop platform is required")
        if any(char in self.description + self.publisher for char in "\r\n\x00"): raise DesktopConfigurationError("metadata must be single-line")
        if self.update_feed:
            parsed = urllib.parse.urlparse(self.update_feed)
            if parsed.scheme != "https" or not parsed.netloc: raise DesktopConfigurationError("update feed must use HTTPS")


def create_desktop_project(config: DesktopConfig, base: Path = Path.cwd()) -> Path:
    root = base / config.name
    if root.exists(): raise FileExistsError(f"Project already exists: {root}")
    for folder in (root / "src", root / "assets", root / "packaging" / "windows", root / "packaging" / "macos", root / "packaging" / "linux"):
        folder.mkdir(parents=True, exist_ok=True)
    metadata = {"orielVersion": "0.9.8", "applicationId": config.application_id, "name": config.name, "version": config.version, "description": config.description, "publisher": config.publisher, "platforms": [item.value for item in config.platforms], "entry": "src/main.py", "updateFeed": config.update_feed}
    (root / "desktop.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "src" / "main.py").write_text(f'"""{config.name} desktop entry point."""\n\ndef main():\n    print("{_python(config.name)}")\n\nif __name__ == "__main__":\n    main()\n', encoding="utf-8")
    (root / "packaging" / "windows" / "installer.wxs").write_text(_wix(config), encoding="utf-8")
    (root / "packaging" / "macos" / "Info.plist").write_text(_mac_plist(config), encoding="utf-8")
    (root / "packaging" / "linux" / f"{config.application_id}.desktop").write_text(f"[Desktop Entry]\nType=Application\nName={config.name}\nComment={config.description}\nExec={config.name}\nIcon={config.application_id}\nCategories=Utility;\nTerminal=false\n", encoding="utf-8")
    (root / "packaging" / "linux" / "appimage.yml").write_text(f"app: {config.name}\nversion: {config.version}\narch: x86_64\n", encoding="utf-8")
    (root / ".gitignore").write_text("build/\ndist/\n*.pfx\n*.p12\n*.key\n*.pem\n*.crt\n*.cer\n*.mobileprovision\n", encoding="utf-8")
    (root / "README.md").write_text(f"# {config.name}\n\nGenerated with ORIEL 0.9.8 Desktop Framework.\n\nValidate: `oriel desktop validate .`\nBuild: `oriel desktop build .`\n", encoding="utf-8")
    return root


def _python(value: str) -> str: return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _wix(config: DesktopConfig) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs"><Package Name="{config.name}" Manufacturer="{config.publisher}" Version="{config.version}" UpgradeCode="*"><MajorUpgrade DowngradeErrorMessage="A newer version is installed."/><MediaTemplate EmbedCab="yes"/></Package></Wix>
'''


def _mac_plist(config: DesktopConfig) -> str:
    import plistlib
    return plistlib.dumps({"CFBundleIdentifier": config.application_id, "CFBundleName": config.name, "CFBundleDisplayName": config.name, "CFBundleShortVersionString": config.version, "CFBundleVersion": config.version, "LSMinimumSystemVersion": config.minimum_macos, "NSHighResolutionCapable": True}, sort_keys=True).decode("utf-8")


def validate_desktop_project(project: Path, *, release: bool = False, target: DesktopPlatform | None = None, environment: Mapping[str, str] | None = None) -> list[str]:
    env = os.environ if environment is None else environment; issues: list[str] = []
    required = ("desktop.json", "src/main.py", "packaging/windows/installer.wxs", "packaging/macos/Info.plist")
    for relative in required:
        if not (project / relative).is_file(): issues.append(f"missing required desktop project file: {relative}")
    try:
        metadata = json.loads((project / "desktop.json").read_text(encoding="utf-8"))
        DesktopConfig(metadata["applicationId"], metadata["name"], metadata["version"], metadata["description"], metadata["publisher"], tuple(DesktopPlatform(item) for item in metadata["platforms"]))
        if not (project / metadata.get("entry", "")).is_file(): issues.append("desktop entry point is missing")
        if target and target.value not in metadata["platforms"]: issues.append(f"target platform is not enabled: {target.value}")
    except Exception as error: issues.append(f"invalid desktop metadata: {error}")
    secret_suffixes = {".pfx", ".p12", ".key", ".pem", ".crt", ".cer"}
    for item in project.rglob("*"):
        if item.is_file() and item.suffix.lower() in secret_suffixes: issues.append(f"signing material must not be stored in project: {item.relative_to(project)}")
    if release:
        selected = target or DesktopPlatform.current()
        requirements = {DesktopPlatform.WINDOWS: ("ORIEL_WINDOWS_CERTIFICATE",), DesktopPlatform.MACOS: ("ORIEL_APPLE_SIGNING_IDENTITY", "ORIEL_APPLE_NOTARY_PROFILE"), DesktopPlatform.LINUX: ("ORIEL_LINUX_GPG_KEY",)}[selected]
        for name in requirements:
            if not env.get(name): issues.append(f"missing signing environment variable: {name}")
    return issues


@dataclass(frozen=True, slots=True)
class DesktopToolchain:
    python: str | None
    pyinstaller: str | None

    @classmethod
    def detect(cls) -> "DesktopToolchain": return cls(sys.executable or shutil.which("python"), shutil.which("pyinstaller"))


def build_desktop_project(project: Path, *, target: DesktopPlatform | None = None, release: bool = False, timeout: int = 1800) -> Path:
    project = project.resolve()
    selected = target or DesktopPlatform.current()
    if selected != DesktopPlatform.current(): raise DesktopBuildError(f"{selected.value} desktop builds must run on {selected.value}")
    issues = validate_desktop_project(project, release=release, target=selected)
    if issues: raise DesktopBuildError("; ".join(issues))
    toolchain = DesktopToolchain.detect()
    if not toolchain.pyinstaller: raise DesktopBuildError("desktop build requires PyInstaller")
    metadata = json.loads((project / "desktop.json").read_text(encoding="utf-8")); dist = project / "dist"
    command = [toolchain.pyinstaller, "--noconfirm", "--clean", "--name", metadata["name"], "--distpath", str(dist), "--workpath", str(project / "build"), str(project / metadata["entry"])]
    result = subprocess.run(command, cwd=project, text=True, capture_output=True, timeout=timeout)
    if result.returncode: raise DesktopBuildError((result.stderr or result.stdout)[-5000:])
    artifact = dist / metadata["name"] / (metadata["name"] + ".exe" if selected == DesktopPlatform.WINDOWS else metadata["name"])
    if not artifact.exists(): raise DesktopBuildError(f"build completed but expected artifact is missing: {artifact}")
    return artifact


def package_desktop_project(project: Path, *, target: DesktopPlatform | None = None, release: bool = False) -> Path:
    """Create a deterministic portable staging archive for an installer pipeline."""
    selected = target or DesktopPlatform.current()
    issues = validate_desktop_project(project, release=release, target=selected)
    if issues: raise DesktopBuildError("; ".join(issues))
    metadata = json.loads((project / "desktop.json").read_text(encoding="utf-8"))
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", metadata["name"]).strip("-.")
    output = project / "dist"; output.mkdir(exist_ok=True)
    files = sorted(item for folder in (project / "src", project / "assets", project / "packaging" / selected.value) for item in folder.rglob("*") if item.is_file())
    files.insert(0, project / "desktop.json")
    stem = f"{safe_name}-{metadata['version']}-{selected.value}"
    if selected == DesktopPlatform.LINUX:
        artifact = output / f"{stem}.tar.gz"
        with artifact.open("wb") as raw:
            import gzip
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w") as archive:
                    for item in files:
                        info = archive.gettarinfo(str(item), arcname=f"{stem}/{item.relative_to(project).as_posix()}")
                        info.uid = info.gid = 0; info.uname = info.gname = ""; info.mtime = 0
                        with item.open("rb") as stream: archive.addfile(info, stream)
    else:
        artifact = output / f"{stem}.zip"
        with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as archive:
            for item in files:
                info = zipfile.ZipInfo(f"{stem}/{item.relative_to(project).as_posix()}", (1980, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o644 << 16
                archive.writestr(info, item.read_bytes())
    checksum = hashlib.sha256(artifact.read_bytes()).hexdigest()
    artifact.with_name(artifact.name + ".sha256").write_text(f"{checksum}  {artifact.name}\n", encoding="ascii")
    return artifact


def native_toolchain_status() -> dict[str, bool]:
    return {"pyinstaller": bool(shutil.which("pyinstaller")), "wix": bool(shutil.which("wix")), "codesign": bool(shutil.which("codesign")), "appimagetool": bool(shutil.which("appimagetool"))}
