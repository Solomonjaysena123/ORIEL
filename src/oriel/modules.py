from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
import re

IMPORT_RE = re.compile(
    r'^\s*(?P<public>public\s+)?use\s+(?:"(?P<quoted>[^"]+)"|(?P<name>[A-Za-z_][\w.]*))'
    r'(?:\s+as\s+(?P<alias>[A-Za-z_][\w]*))?\s*$',
    re.MULTILINE,
)


class ModuleError(Exception):
    """Raised when an ORIEL module graph cannot be resolved safely."""


@dataclass(frozen=True)
class ImportSpec:
    name: str
    alias: str | None = None
    public: bool = False
    line: int = 1


@dataclass
class ModuleNode:
    path: Path
    imports: list[ImportSpec] = field(default_factory=list)


@dataclass
class ModuleGraph:
    root: Path
    entry: Path
    ordered_files: list[Path]
    nodes: dict[Path, ModuleNode]

    def relative_files(self) -> list[str]:
        result: list[str] = []
        for path in self.ordered_files:
            try:
                result.append(path.relative_to(self.root).as_posix())
            except ValueError:
                result.append(path.as_posix())
        return result


def project_root(path: Path) -> Path:
    current = path.resolve().parent if path.is_file() else path.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "oriel.toml").exists():
            return candidate
    return current


def parse_imports(source: str) -> list[ImportSpec]:
    imports: list[ImportSpec] = []
    aliases: set[str] = set()
    for match in IMPORT_RE.finditer(source):
        name = match.group("quoted") or match.group("name")
        alias = match.group("alias")
        if alias:
            if alias in aliases:
                line = source.count("\n", 0, match.start()) + 1
                raise ModuleError(f"Duplicate module alias '{alias}' on line {line}.")
            aliases.add(alias)
        imports.append(
            ImportSpec(
                name=name,
                alias=alias,
                public=bool(match.group("public")),
                line=source.count("\n", 0, match.start()) + 1,
            )
        )
    return imports


def _safe_resolve(candidate: Path, allowed_root: Path, name: str) -> Path:
    resolved = candidate.resolve()
    allowed = allowed_root.resolve()
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise ModuleError(f"Module '{name}' resolves outside the allowed project root.") from exc
    return resolved


def _packaged_stdlib(name: str) -> Path | None:
    module_name = name.removeprefix("oriel.").replace(".", "/") + ".orl"
    try:
        resource = resources.files("oriel").joinpath("stdlib", module_name)
        if resource.is_file():
            # The editable/source installation used by ORIEL exposes a concrete path.
            return Path(str(resource)).resolve()
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        return None
    return None


def resolve_import(name: str, current_file: Path, root: Path) -> Path:
    if name.startswith("oriel."):
        relative = Path(*name.removeprefix("oriel.").split(".")).with_suffix(".orl")
        project_candidate = root / "stdlib" / relative
        if project_candidate.exists():
            return project_candidate.resolve()
        packaged = _packaged_stdlib(name)
        if packaged and packaged.exists():
            return packaged
        raise ModuleError(f"Standard-library module '{name}' was not found.")

    if name.endswith(".orl") or "/" in name or "\\" in name:
        candidate = _safe_resolve(current_file.parent / name, root, name)
    else:
        relative = Path(*name.split(".")).with_suffix(".orl")
        candidates = [root / "src" / relative, root / relative]
        existing = next((p for p in candidates if p.exists()), None)
        candidate = (existing or candidates[0]).resolve()

    if not candidate.exists():
        raise ModuleError(f"Module '{name}' was not found (looked for {candidate}).")
    if candidate.suffix.lower() != ".orl":
        raise ModuleError(f"Module '{name}' must resolve to an .orl source file.")
    return candidate


def build_module_graph(entry: Path) -> ModuleGraph:
    entry = entry.resolve()
    if not entry.exists():
        raise ModuleError(f"Entry module was not found: {entry}")
    root = project_root(entry)
    visited: set[Path] = set()
    active: list[Path] = []
    ordered: list[Path] = []
    nodes: dict[Path, ModuleNode] = {}

    def visit(file: Path) -> None:
        file = file.resolve()
        if file in active:
            cycle_start = active.index(file)
            cycle_paths = active[cycle_start:] + [file]
            cycle = " -> ".join(path.name for path in cycle_paths)
            raise ModuleError(f"Circular module import detected: {cycle}")
        if file in visited:
            return

        active.append(file)
        source = file.read_text(encoding="utf-8")
        imports = parse_imports(source)
        nodes[file] = ModuleNode(path=file, imports=imports)
        # Source order is deterministic; dependencies are visited before importers.
        for spec in imports:
            visit(resolve_import(spec.name, file, root))
        active.pop()
        visited.add(file)
        ordered.append(file)

    visit(entry)
    return ModuleGraph(root=root, entry=entry, ordered_files=ordered, nodes=nodes)


def _strip_imports(source: str) -> str:
    return IMPORT_RE.sub("", source)


def load_module_graph(entry: Path) -> tuple[str, list[Path]]:
    graph = build_module_graph(entry)
    chunks: list[str] = []
    for file in graph.ordered_files:
        source = _strip_imports(file.read_text(encoding="utf-8"))
        # `public` is accepted as an API marker in 0.7.3 while the bootstrap
        # interpreter continues to execute a flattened module graph.
        source = re.sub(r"(?m)^\s*public\s+(?=fn\s+)", "", source)
        try:
            label = file.relative_to(graph.root).as_posix()
        except ValueError:
            label = file.name
        chunks.append(f"// module: {label}\n{source.strip()}\n")
    return "\n".join(chunks), graph.ordered_files
