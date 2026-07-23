from __future__ import annotations
from pathlib import Path
import hashlib, json, shutil, tomllib

REGISTRY = {
    "oriel.core": {"version": "0.3.0", "description": "Core Oriel utilities"},
    "oriel.text": {"version": "0.1.0", "description": "Text helpers"},
    "oriel.math": {"version": "0.1.0", "description": "Math helpers"},
    "oriel.json": {"version": "0.1.0", "description": "JSON helpers"},
    "oriel.api": {"version": "0.1.0-alpha", "description": "Experimental API framework"},
}

def manifest_path(project: Path) -> Path:
    path = project / "oriel.toml"
    if not path.exists():
        raise FileNotFoundError("oriel.toml was not found. Run this command inside an Oriel project.")
    return path

def read_manifest(project: Path) -> dict:
    return tomllib.loads(manifest_path(project).read_text(encoding="utf-8"))

def _write_manifest(project: Path, data: dict) -> None:
    project_data = data.get("project", {})
    deps = data.get("dependencies", {})
    lines = ["[project]"]
    for key in ("name", "version", "entry"):
        if key in project_data: lines.append(f'{key} = "{project_data[key]}"')
    lines += ["", "[dependencies]"]
    for name in sorted(deps): lines.append(f'"{name}" = "{deps[name]}"')
    manifest_path(project).write_text("\n".join(lines)+"\n", encoding="utf-8")

def add(project: Path, package: str, version: str | None = None) -> str:
    if package not in REGISTRY:
        raise ValueError(f"Package '{package}' is not available in the Oriel preview registry.")
    data = read_manifest(project)
    data.setdefault("dependencies", {})[package] = version or REGISTRY[package]["version"]
    _write_manifest(project, data)
    install(project)
    return data["dependencies"][package]

def remove(project: Path, package: str) -> None:
    data = read_manifest(project)
    if package not in data.get("dependencies", {}): raise ValueError(f"Package '{package}' is not installed.")
    del data["dependencies"][package]
    _write_manifest(project, data)
    pkg_dir = project / ".oriel" / "packages" / package
    if pkg_dir.exists(): shutil.rmtree(pkg_dir)
    write_lock(project, data.get("dependencies", {}))

def install(project: Path) -> int:
    data = read_manifest(project)
    deps = data.get("dependencies", {})
    root = project / ".oriel" / "packages"
    root.mkdir(parents=True, exist_ok=True)
    for name, version in deps.items():
        if name not in REGISTRY: raise ValueError(f"Unknown package '{name}'.")
        package_dir = root / name
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "package.json").write_text(json.dumps({"name": name, "version": version, **REGISTRY[name]}, indent=2), encoding="utf-8")
        (package_dir / "README.md").write_text(f"# {name}\n\n{REGISTRY[name]['description']}\n", encoding="utf-8")
    write_lock(project, deps)
    return len(deps)

def write_lock(project: Path, deps: dict) -> None:
    packages=[]
    for name,version in sorted(deps.items()):
        digest=hashlib.sha256(f"{name}@{version}".encode()).hexdigest()
        packages.append({"name":name,"version":version,"checksum":digest})
    (project/"oriel.lock").write_text(json.dumps({"lock_version":1,"packages":packages}, indent=2)+"\n", encoding="utf-8")

def list_registry() -> list[tuple[str,str,str]]:
    return [(n,v["version"],v["description"]) for n,v in sorted(REGISTRY.items())]
