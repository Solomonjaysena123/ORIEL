from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
import tomllib

from . import __version__
from .interpreter import Lexer, Parser, TypeChecker, run_source
from . import package_manager
from .lsp import run_lsp
from .modules import load_module_graph
from .api_framework import create_api_project, serve, route_manifest, openapi_manifest
from .db_framework import create_database_project, schema_manifest, migrate, inspect_database
from .application_services import generate_crud, hash_password, verify_password, create_token, verify_token, parse_validators, validate
from .console_tools import write_bytecode, run_bytecode, generate_docs, doctor, benchmark, repl

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
    add = sub.add_parser("add", help="Add a dependency to oriel.toml.")
    add.add_argument("package")
    add.add_argument("--version")
    add.add_argument("--path")
    remove = sub.add_parser("remove", help="Remove a project dependency.")
    remove.add_argument("package")
    sub.add_parser("install", help="Install dependencies from oriel.toml.")
    publish = sub.add_parser("publish", help="Publish the current project to a local ORIEL registry.")
    publish.add_argument("--registry", type=Path)
    sub.add_parser("packages", help="List packages in the preview registry.")
    sub.add_parser("lsp", help="Start the ORIEL language server over stdio.")
    graph = sub.add_parser("graph", help="Show the resolved module graph.")
    graph.add_argument("file", type=Path)
    api = sub.add_parser("api", help="ORIEL API framework commands.")
    api_sub = api.add_subparsers(dest="api_command", required=True)
    api_new = api_sub.add_parser("new", help="Create an ORIEL API project.")
    api_new.add_argument("name")
    api_new.add_argument("--path", type=Path, default=Path.cwd())
    api_routes = api_sub.add_parser("routes", help="List routes in an ORIEL API file.")
    api_routes.add_argument("file", type=Path)
    api_serve = api_sub.add_parser("serve", help="Serve an ORIEL API application.")
    api_serve.add_argument("file", type=Path, nargs="?", default=Path("src/main.orl"))
    api_serve.add_argument("--host", default="127.0.0.1")
    api_serve.add_argument("--port", type=int, default=8000)
    db = sub.add_parser("db", help="ORIEL database framework commands.")
    db_sub = db.add_subparsers(dest="db_command", required=True)
    db_new = db_sub.add_parser("new", help="Create an ORIEL database project.")
    db_new.add_argument("name")
    db_new.add_argument("--path", type=Path, default=Path.cwd())
    db_schema = db_sub.add_parser("schema", help="Display entities and generated SQL.")
    db_schema.add_argument("file", type=Path, nargs="?", default=Path("src/schema.orl"))
    db_migrate = db_sub.add_parser("migrate", help="Apply an ORIEL schema to SQLite.")
    db_migrate.add_argument("file", type=Path, nargs="?", default=Path("src/schema.orl"))
    db_migrate.add_argument("--database", type=Path, default=Path("data/oriel.db"))
    db_inspect = db_sub.add_parser("inspect", help="Inspect an ORIEL SQLite database.")
    db_inspect.add_argument("database", type=Path, nargs="?", default=Path("data/oriel.db"))
    api_openapi = api_sub.add_parser("openapi", help="Generate an OpenAPI 3.1 document.")
    api_openapi.add_argument("file", type=Path, nargs="?", default=Path("src/main.orl"))
    api_openapi.add_argument("--output", type=Path)
    gen = sub.add_parser("generate", help="Generate ORIEL application scaffolding.")
    gen_sub = gen.add_subparsers(dest="generate_command", required=True)
    crud = gen_sub.add_parser("crud", help="Generate CRUD API, validation and tests.")
    crud.add_argument("entity")
    crud.add_argument("--schema", type=Path, default=Path("src/schema.orl"))
    crud.add_argument("--output", type=Path, default=Path("generated"))
    auth = sub.add_parser("auth", help="Password and token utilities.")
    auth_sub = auth.add_subparsers(dest="auth_command", required=True)
    ah = auth_sub.add_parser("hash"); ah.add_argument("password")
    av = auth_sub.add_parser("verify"); av.add_argument("password"); av.add_argument("encoded")
    at = auth_sub.add_parser("token"); at.add_argument("subject"); at.add_argument("--secret", required=True); at.add_argument("--expires", type=int, default=3600)
    ac = auth_sub.add_parser("check-token"); ac.add_argument("token"); ac.add_argument("--secret", required=True)
    val = sub.add_parser("validate", help="Validate JSON data against an ORIEL validator.")
    val.add_argument("file", type=Path); val.add_argument("validator"); val.add_argument("json_data")
    compile_cmd=sub.add_parser("compile", help="Compile ORIEL source to portable bytecode.")
    compile_cmd.add_argument("file",type=Path); compile_cmd.add_argument("--output",type=Path); compile_cmd.add_argument("--optimize",action="store_true")
    runbc=sub.add_parser("run-bytecode",help="Run an ORIEL .obc file."); runbc.add_argument("file",type=Path)
    docs=sub.add_parser("docs",help="Generate Markdown API documentation."); docs.add_argument("file",type=Path); docs.add_argument("--output",type=Path,default=Path("docs/API.md"))
    sub.add_parser("doctor",help="Check the ORIEL development environment.")
    bench=sub.add_parser("benchmark",help="Benchmark an ORIEL source file."); bench.add_argument("file",type=Path); bench.add_argument("--iterations",type=int,default=10); bench.add_argument("--engine",choices=["vm","interpreter"],default="vm")
    dbg=sub.add_parser("debug",help="Run bytecode with source-line breakpoints."); dbg.add_argument("file",type=Path); dbg.add_argument("--breakpoint",type=int,action="append",default=[])
    prof=sub.add_parser("profile",help="Profile ORIEL VM bytecode."); prof.add_argument("file",type=Path); prof.add_argument("--iterations",type=int,default=1)
    sub.add_parser("repl",help="Start the interactive ORIEL console.")
    return parser


def read_source(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix.lower() != ".orl":
        raise ValueError("Oriel source files must use the .orl extension.")
    return path.read_text(encoding="utf-8")


def check_source(source: str) -> None:
    statements = Parser(Lexer(source).scan_tokens()).parse()
    TypeChecker().check(statements)


def check_file(path: Path) -> None:
    source, _ = load_module_graph(path)
    check_source(source)


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
        f'[project]\nname = "{clean}"\nversion = "0.1.0"\nentry = "src/main.orl"\n\n[dependencies]\noriel.core = "0.7.3"\n', encoding="utf-8"
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
            source, _ = load_module_graph(args.file)
            run_source(source, str(args.file))
            return 0
        if args.command == "check":
            check_file(args.file)
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
        if args.command == "add":
            version = package_manager.add(Path.cwd(), args.package, args.version, args.path)
            print(f"Added {args.package} {version}")
            return 0
        if args.command == "remove":
            package_manager.remove(Path.cwd(), args.package)
            print(f"Removed {args.package}")
            return 0
        if args.command == "install":
            count = package_manager.install(Path.cwd())
            print(f"Installed {count} package(s); lock file updated.")
            return 0
        if args.command == "publish":
            print(f"Published: {package_manager.publish(Path.cwd(), args.registry)}")
            return 0
        if args.command == "packages":
            for name, version, description in package_manager.list_registry():
                print(f"{name:<16} {version:<12} {description}")
            return 0
        if args.command == "generate":
            if args.generate_command == "crud":
                files = generate_crud(args.schema, args.entity, args.output)
                for file in files: print(f"Generated: {file}")
                return 0
        if args.command == "auth":
            import json
            if args.auth_command == "hash": print(hash_password(args.password)); return 0
            if args.auth_command == "verify": print("valid" if verify_password(args.password,args.encoded) else "invalid"); return 0
            if args.auth_command == "token": print(create_token(args.subject,args.secret,args.expires)); return 0
            if args.auth_command == "check-token": print(json.dumps(verify_token(args.token,args.secret),indent=2)); return 0
        if args.command == "validate":
            import json
            validators=parse_validators(read_source(args.file))
            if args.validator not in validators: raise ValueError(f"Validator not found: {args.validator}")
            issues=validate(json.loads(args.json_data),validators[args.validator])
            print(json.dumps({"valid":not issues,"issues":[i.__dict__ for i in issues]},indent=2)); return 1 if issues else 0
        if args.command == "compile":
            output=write_bytecode(args.file,args.output,args.optimize); print(f"Compiled: {output}"); return 0
        if args.command == "run-bytecode": run_bytecode(args.file); return 0
        if args.command == "docs": print(f"Documentation generated: {generate_docs(args.file,args.output)}"); return 0
        if args.command == "doctor":
            import json; print(json.dumps(doctor(),indent=2)); return 0
        if args.command == "benchmark":
            import json; print(json.dumps(benchmark(args.file,args.iterations,args.engine),indent=2)); return 0
        if args.command == "debug":
            from .debugger import Debugger
            from .console_tools import load_bytecode
            result,events=Debugger(set(args.breakpoint)).run(load_bytecode(args.file))
            import json; print(json.dumps([e.__dict__ for e in events],indent=2)); return 0
        if args.command == "profile":
            from .profiler import profile
            from .console_tools import load_bytecode
            import json; print(json.dumps(profile(load_bytecode(args.file),args.iterations).to_dict(),indent=2)); return 0
        if args.command == "repl": repl(); return 0
        if args.command == "lsp":
            return run_lsp()
        if args.command == "graph":
            _, files = load_module_graph(args.file)
            for file in files:
                print(file)
            return 0
        if args.command == "api":
            if args.api_command == "new":
                project = create_api_project(args.name, args.path)
                print(f"Created ORIEL API project: {project}")
                return 0
            if args.api_command == "routes":
                import json
                print(json.dumps(route_manifest(read_source(args.file)), indent=2))
                return 0
            if args.api_command == "openapi":
                import json
                document = json.dumps(openapi_manifest(read_source(args.file)), indent=2) + "\n"
                if args.output:
                    args.output.write_text(document, encoding="utf-8")
                    print(f"OpenAPI document written: {args.output}")
                else:
                    print(document, end="")
                return 0
            if args.api_command == "serve":
                serve(args.file, args.host, args.port)
                return 0
        if args.command == "db":
            import json
            if args.db_command == "new":
                project = create_database_project(args.name, args.path)
                print(f"Created ORIEL database project: {project}")
                return 0
            if args.db_command == "schema":
                print(json.dumps(schema_manifest(read_source(args.file)), indent=2))
                return 0
            if args.db_command == "migrate":
                count = migrate(args.file, args.database)
                print(f"Migration successful: {count} table(s) applied to {args.database}")
                return 0
            if args.db_command == "inspect":
                print(json.dumps(inspect_database(args.database), indent=2))
                return 0
    except Exception as error:
        print(error, file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
