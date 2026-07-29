"""ORIEL 0.7.3 deterministic module resolution."""
from dataclasses import dataclass
from pathlib import Path
import re
USE_RE=re.compile(r'^\s*use\s+([A-Za-z_][\w.]*)\s*$', re.MULTILINE)

@dataclass
class ModuleGraph:
    entry: Path
    files: dict[str, Path]
    edges: dict[str, tuple[str,...]]

class ModuleResolutionError(Exception): pass

def imports(source: str) -> tuple[str,...]: return tuple(USE_RE.findall(source))

def module_path(root: Path, name: str) -> Path: return root.joinpath(*name.split('.')).with_suffix('.orl')

def resolve_graph(entry: Path, root: Path|None=None) -> ModuleGraph:
    entry=entry.resolve(); root=(root or entry.parent).resolve(); files={}; edges={}; visiting=[]
    def visit(name: str, path: Path):
        if name in visiting: raise ModuleResolutionError("Circular import: " + " -> ".join(visiting+[name]))
        if name in files: return
        if not path.exists(): raise ModuleResolutionError(f"Module '{name}' not found at {path}")
        visiting.append(name); files[name]=path
        deps=tuple(i for i in imports(path.read_text(encoding='utf-8')) if not i.startswith('oriel.'))
        edges[name]=deps
        for dep in deps: visit(dep,module_path(root,dep))
        visiting.pop()
    visit('__main__',entry)
    return ModuleGraph(entry,files,edges)
