from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest
import zipfile

from . import __version__
from .interpreter import Lexer, Parser, run_source


HELLO_TEMPLATE = """// main.orl

fn main() {
    print("Hello from Oriel!")
}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oriel",
        description="Oriel Software Language command-line interface.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("version", help="Show the installed Oriel version.")

    run = subparsers.add_parser("run", help="Run an Oriel source file.")
    run.add_argument("file", type=Path)

    check = subparsers.add_parser("check", help="Check Oriel syntax without running.")
    check.add_argument("file", type=Path)

    new = subparsers.add_parser("new", help="Create a new Oriel project.")
    new.add_argument("name")
    new.add_argument("--path", type=Path, default=Path.cwd())

    format_command = subparsers.add_parser("format", help="Format Oriel source files.")
    format_command.add_argument("paths", nargs="+", type=Path)

    test = subparsers.add_parser("test", help="Run project tests.")
    test.add_argument("--path", type=Path, default=Path.cwd())

    build = subparsers.add_parser("build", help="Build a distributable project ZIP.")
    build.add_argument("--path", type=Path, default=Path.cwd())
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
    if not clean or any(char in clean for char in '\\/:*?"<>|'):
        raise ValueError("Project name contains invalid characters.")
    project = base / clean
    if project.exists():
        raise FileExistsError(f"Project already exists: {project}")
    project.mkdir(parents=True)
    (project / "main.orl").write_text(HELLO_TEMPLATE, encoding="utf-8")
    (project / "tests").mkdir()
    (project / "README.md").write_text(
        f"# {clean}\n\nRun with:\n\n```bash\noriel run main.orl\n```\n",
        encoding="utf-8",
    )
    return project


def format_source(source: str) -> str:
    lines = [line.rstrip().replace("\t", "    ") for line in source.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def format_paths(paths: list[Path]) -> int:
    files: list[Path] = []
    for path in paths:
        files.extend(sorted(path.rglob("*.orl")) if path.is_dir() else [path])
    for path in files:
        path.write_text(format_source(read_source(path)), encoding="utf-8")
        print(f"Formatted: {path}")
    return len(files)


def run_project_tests(project: Path) -> bool:
    success = True
    python_tests = project / "tests"
    if python_tests.exists():
        suite = unittest.defaultTestLoader.discover(str(python_tests), pattern="test_*.py")
        if suite.countTestCases():
            success = unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
        for path in sorted(python_tests.glob("*.orl")):
            run_source(read_source(path), str(path))
            print(f"Passed: {path}")
    return success


def build_project(project: Path) -> Path:
    main_file = project / "main.orl"
    if not main_file.exists():
        raise FileNotFoundError(f"Project entry point not found: {main_file}")
    check_source(read_source(main_file))
    output_dir = project / "dist"
    output_dir.mkdir(exist_ok=True)
    archive = output_dir / f"{project.name}-0.2.0.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
        for path in sorted(project.rglob("*")):
            if path.is_file() and output_dir not in path.parents:
                package.write(path, path.relative_to(project))
    return archive


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "version":
            print(f"Oriel {__version__}")
        elif args.command == "run":
            run_source(read_source(args.file), str(args.file))
        elif args.command == "check":
            check_source(read_source(args.file))
            print(f"Check successful: {args.file}")
        elif args.command == "new":
            project = create_project(args.name, args.path)
            print(f"Created Oriel project: {project}")
        elif args.command == "format":
            print(f"Formatted {format_paths(args.paths)} Oriel file(s).")
        elif args.command == "test":
            return 0 if run_project_tests(args.path) else 1
        elif args.command == "build":
            print(f"Built: {build_project(args.path)}")
        return 0
    except Exception as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
