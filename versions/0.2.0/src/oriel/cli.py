from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
import tomllib

from . import __version__
from .interpreter import Lexer, Parser, run_source

HELLO_TEMPLATE = '''// src/main.orl

fn main() {
    let technologies = ["Console", "Web", "Mobile", "AI"]

    for technology in technologies {
        print("ORIEL builds " + technology)
    }
}
'''

TEST_TEMPLATE = '''fn main() {
    let result = 2 + 2
    if result != 4 {
        print("FAIL: mathematics")
    } else {
        print("PASS: mathematics")
    }
}
'''


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oriel", description="Oriel Software Language CLI.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version", help="Show the installed Oriel version.")
    run = sub.add_parser("run", help="Run an Oriel source file.")
    run.add_argument("file", type=Path)
    check = sub.add_parser("check", help="Check Oriel syntax without running.")
    check.add_argument("file", type=Path)
    new = sub.add_parser("new", help="Create a structured Oriel project.")
    new.add_argument("name")
    new.add_argument("--path", type=Path, default=Path.cwd())
    fmt = sub.add_parser("format", help="Apply basic formatting to an Oriel file or project.")
    fmt.add_argument("path", type=Path, nargs="?", default=Path.cwd())
    test = sub.add_parser("test", help="Run all .orl tests in the tests directory.")
    test.add_argument("path", type=Path, nargs="?", default=Path.cwd())
    build = sub.add_parser("build", help="Validate and create a distributable build directory.")
    build.add_argument("path", type=Path, nargs="?", default=Path.cwd())
    return parser


def read_source(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix.lower() != ".orl":
        raise ValueError("Oriel source files must use the .orl extension.")
    return path.read_text(encoding="utf-8")


def check_source(source: str) -> None:
    Parser(Lexer(source).scan_tokens()).parse()


def create_project(name: str, base: Path) -> Path:
    clean = name.strip()
    if not clean or any(ch in clean for ch in '\\/:*?"<>|'):
        raise ValueError("Project name contains invalid characters.")
    project = base / clean
    if project.exists():
        raise FileExistsError(f"Project already exists: {project}")
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "src" / "main.orl").write_text(HELLO_TEMPLATE, encoding="utf-8")
    (project / "main.orl").write_text(HELLO_TEMPLATE.replace("// src/main.orl", "// main.orl"), encoding="utf-8")
    (project / "tests" / "core_test.orl").write_text(TEST_TEMPLATE, encoding="utf-8")
    (project / "oriel.toml").write_text(
        f'[project]\nname = "{clean}"\nversion = "0.1.0"\nentry = "src/main.orl"\n', encoding="utf-8"
    )
    (project / "README.md").write_text(
        f"# {clean}\n\nRun: `oriel run src/main.orl`\n\nTest: `oriel test`\n\nBuild: `oriel build`\n",
        encoding="utf-8",
    )
    return project


def format_source(source: str) -> str:
    lines = []
    indent = 0
    for raw in source.splitlines():
        text = raw.strip()
        if not text:
            lines.append("")
            continue
        if text.startswith("}"):
            indent = max(0, indent - 1)
        lines.append("    " * indent + text)
        if text.endswith("{"):
            indent += 1
    return "\n".join(lines).rstrip() + "\n"


def find_oriel_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*.orl") if "build" not in p.parts)


def run_tests(project: Path) -> int:
    test_dir = project / "tests" if project.is_dir() else project.parent
    files = sorted(test_dir.glob("*.orl"))
    if not files:
        print("No Oriel tests found.")
        return 0
    failures = 0
    for file in files:
        try:
            run_source(read_source(file), str(file))
            print(f"✓ {file.name}")
        except Exception as error:
            failures += 1
            print(f"✗ {file.name}\n{error}", file=sys.stderr)
    print(f"Tests: {len(files) - failures} passed, {failures} failed")
    return 1 if failures else 0


def build_project(project: Path) -> Path:
    config_path = project / "oriel.toml"
    entry = Path("src/main.orl")
    if config_path.exists():
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        entry = Path(config.get("project", {}).get("entry", str(entry)))
    source_path = project / entry
    source = read_source(source_path)
    check_source(source)
    build_dir = project / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    shutil.copy2(source_path, build_dir / "main.orl")
    if config_path.exists():
        shutil.copy2(config_path, build_dir / "oriel.toml")
    (build_dir / "RUN.txt").write_text("Run with: oriel run main.orl\n", encoding="utf-8")
    return build_dir


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "version":
            print(f"Oriel {__version__}")
            return 0
        if args.command == "run":
            run_source(read_source(args.file), str(args.file))
            return 0
        if args.command == "check":
            check_source(read_source(args.file))
            print(f"Check successful: {args.file}")
            return 0
        if args.command == "new":
            project = create_project(args.name, args.path)
            print(f"Created Oriel project: {project}")
            print(f'Run: cd "{project}" && oriel run src/main.orl')
            return 0
        if args.command == "format":
            files = find_oriel_files(args.path)
            for file in files:
                file.write_text(format_source(read_source(file)), encoding="utf-8")
                print(f"Formatted: {file}")
            return 0
        if args.command == "test":
            return run_tests(args.path)
        if args.command == "build":
            output = build_project(args.path)
            print(f"Build successful: {output}")
            return 0
    except Exception as error:
        print(error, file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
