from __future__ import annotations

import argparse
from pathlib import Path
import sys

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
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="Show the installed Oriel version.")

    run = sub.add_parser("run", help="Run an Oriel source file.")
    run.add_argument("file", type=Path)

    check = sub.add_parser("check", help="Check Oriel syntax without running.")
    check.add_argument("file", type=Path)

    new = sub.add_parser("new", help="Create a new Oriel project.")
    new.add_argument("name")
    new.add_argument("--path", type=Path, default=Path.cwd())

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

    project.mkdir(parents=True)
    (project / "main.orl").write_text(HELLO_TEMPLATE, encoding="utf-8")
    (project / "README.md").write_text(
        f"# {clean}\n\nRun with:\n\n```bash\noriel run main.orl\n```\n",
        encoding="utf-8",
    )
    return project


def main() -> int:
    args = build_parser().parse_args()

    try:
        if args.command == "version":
            print(f"Oriel {__version__}")
            return 0

        if args.command == "run":
            source = read_source(args.file)
            run_source(source, str(args.file))
            return 0

        if args.command == "check":
            source = read_source(args.file)
            check_source(source)
            print(f"Check successful: {args.file}")
            return 0

        if args.command == "new":
            project = create_project(args.name, args.path)
            print(f"Created Oriel project: {project}")
            print(f'Run: cd "{project}" && oriel run main.orl')
            return 0

    except Exception as error:
        print(error, file=sys.stderr)
        return 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
