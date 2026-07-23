from __future__ import annotations
from pathlib import Path
import re

USE_RE = re.compile(r'^\s*use\s+(?:"([^"]+)"|([A-Za-z_][\w.]*))\s*$', re.MULTILINE)

class ModuleError(Exception):
    pass

def project_root(path: Path) -> Path:
    current = path.resolve().parent if path.is_file() else path.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "oriel.toml").exists():
            return candidate
    return current

def resolve_import(name: str, current_file: Path, root: Path) -> Path:
    if name.endswith('.orl') or '/' in name or '\\' in name:
        candidate = (current_file.parent / name).resolve()
    else:
        relative = Path(*name.split('.')).with_suffix('.orl')
        candidates = [root / 'src' / relative, root / relative]
        candidate = next((p.resolve() for p in candidates if p.exists()), candidates[0].resolve())
    if not candidate.exists():
        raise ModuleError(f"Module '{name}' was not found (looked for {candidate}).")
    return candidate

def load_module_graph(entry: Path) -> tuple[str, list[Path]]:
    root = project_root(entry)
    visited: set[Path] = set()
    stack: list[Path] = []
    ordered: list[Path] = []

    def visit(file: Path):
        file = file.resolve()
        if file in stack:
            cycle = ' -> '.join(p.name for p in stack + [file])
            raise ModuleError(f"Circular module import detected: {cycle}")
        if file in visited:
            return
        stack.append(file)
        text = file.read_text(encoding='utf-8')
        for match in USE_RE.finditer(text):
            name = match.group(1) or match.group(2)
            if name.startswith('oriel.'):
                continue
            visit(resolve_import(name, file, root))
        stack.pop(); visited.add(file); ordered.append(file)

    visit(entry)
    chunks=[]
    for file in ordered:
        text=file.read_text(encoding='utf-8')
        text=USE_RE.sub(lambda m: '' if (m.group(1) or m.group(2)).startswith('oriel.') else '', text)
        chunks.append(f"// module: {file.relative_to(root) if file.is_relative_to(root) else file.name}\n{text}")
    return '\n\n'.join(chunks), ordered
