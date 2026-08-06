from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import dataclass
import hashlib
from pathlib import Path
import json
import re
import sqlite3

ENTITY_RE = re.compile(r"entity\s+([A-Za-z_]\w*)\s*\{(.*?)\}", re.S)
FIELD_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)(.*)$")
TYPE_MAP = {
    "Id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "Int": "INTEGER",
    "Float": "REAL",
    "Decimal": "REAL",
    "Bool": "INTEGER",
    "String": "TEXT",
    "Text": "TEXT",
}

@dataclass
class Field:
    name: str
    type_name: str
    required: bool = False
    unique: bool = False
    default: str | None = None

@dataclass
class Entity:
    name: str
    fields: list[Field]

    @property
    def table(self) -> str:
        value = re.sub(r"(?<!^)(?=[A-Z])", "_", self.name).lower()
        return value + "s"


def parse_entities(source: str) -> list[Entity]:
    entities: list[Entity] = []
    entity_names: set[str] = set()
    for name, body in ENTITY_RE.findall(source):
        if name in entity_names:
            raise ValueError(f"Duplicate entity '{name}'.")
        entity_names.add(name)
        fields: list[Field] = []
        field_names: set[str] = set()
        for raw in body.splitlines():
            raw = raw.strip().rstrip(",")
            if not raw or raw.startswith("//"):
                continue
            match = FIELD_RE.match(raw)
            if not match:
                raise ValueError(f"Invalid entity field in {name}: {raw}")
            field_name, type_name, options = match.groups()
            if field_name in field_names:
                raise ValueError(f"Duplicate field '{name}.{field_name}'.")
            field_names.add(field_name)
            if type_name not in TYPE_MAP:
                raise ValueError(f"Unsupported database type '{type_name}' for {name}.{field_name}")
            default_match = re.search(r"default\s+([^\s]+)", options)
            fields.append(Field(
                field_name,
                type_name,
                required="required" in options,
                unique="unique" in options,
                default=default_match.group(1) if default_match else None,
            ))
        if not fields:
            raise ValueError(f"Entity '{name}' does not define any fields.")
        entities.append(Entity(name, fields))
    if not entities:
        raise ValueError("No entities found. Example: entity Product { id: Id }")
    return entities


def entity_sql(entity: Entity) -> str:
    columns = []
    for field in entity.fields:
        sql = f'"{field.name}" {TYPE_MAP[field.type_name]}'
        if field.required and field.type_name != "Id":
            sql += " NOT NULL"
        if field.unique:
            sql += " UNIQUE"
        if field.default is not None:
            sql += f" DEFAULT {field.default}"
        columns.append(sql)
    return f'CREATE TABLE IF NOT EXISTS "{entity.table}" (\n  ' + ",\n  ".join(columns) + "\n);"


def schema_manifest(source: str) -> list[dict]:
    return [
        {
            "entity": entity.name,
            "table": entity.table,
            "fields": [field.__dict__ for field in entity.fields],
            "sql": entity_sql(entity),
        }
        for entity in parse_entities(source)
    ]


def migrate(source_path: Path, database_path: Path) -> int:
    source = source_path.read_text(encoding="utf-8")
    entities = parse_entities(source)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    checksum = hashlib.sha256(source.encode("utf-8")).hexdigest()
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS _oriel_migrations (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, checksum TEXT NOT NULL UNIQUE, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info('_oriel_migrations')")}
        if "checksum" not in columns:
            connection.execute("ALTER TABLE _oriel_migrations ADD COLUMN checksum TEXT")
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS _oriel_migrations_checksum ON _oriel_migrations(checksum) WHERE checksum IS NOT NULL"
            )
        if connection.execute("SELECT 1 FROM _oriel_migrations WHERE checksum=?", (checksum,)).fetchone():
            return 0
        for entity in entities:
            connection.execute(entity_sql(entity))
        connection.execute("INSERT INTO _oriel_migrations(source, checksum) VALUES (?, ?)", (str(source_path), checksum))
        connection.commit()
    return len(entities)


def migration_history(database_path: Path) -> list[dict[str, object]]:
    if not database_path.exists():
        return []
    with closing(sqlite3.connect(database_path)) as connection:
        table = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='_oriel_migrations'").fetchone()
        if not table:
            return []
        columns = {row[1] for row in connection.execute("PRAGMA table_info('_oriel_migrations')")}
        if "checksum" not in columns:
            return [
                {"id": row[0], "source": row[1], "checksum": None, "applied_at": row[2]}
                for row in connection.execute("SELECT id, source, applied_at FROM _oriel_migrations ORDER BY id")
            ]
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute("SELECT id, source, checksum, applied_at FROM _oriel_migrations ORDER BY id")]


class Database:
    """Small SQLite session with explicit transaction boundaries."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def transaction(self):
        connection = self.connect()
        try:
            connection.execute("BEGIN")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def execute(self, sql: str, parameters: tuple[object, ...] = ()) -> int:
        with self.transaction() as connection:
            return connection.execute(sql, parameters).rowcount

    def query(self, sql: str, parameters: tuple[object, ...] = ()) -> list[dict[str, object]]:
        with closing(self.connect()) as connection:
            return [dict(row) for row in connection.execute(sql, parameters)]

    def healthy(self) -> bool:
        with closing(self.connect()) as connection:
            return connection.execute("SELECT 1").fetchone()[0] == 1


def inspect_database(database_path: Path) -> dict:
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")
    with closing(sqlite3.connect(database_path)) as connection:
        tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        result = {}
        for table in tables:
            result[table] = [
                {"name": row[1], "type": row[2], "required": bool(row[3]), "primary_key": bool(row[5])}
                for row in connection.execute(f'PRAGMA table_info("{table}")')
            ]
    return result


def create_database_project(name: str, base: Path) -> Path:
    root = base / name
    if root.exists():
        raise FileExistsError(f"Project already exists: {root}")
    (root / "src").mkdir(parents=True)
    (root / "data").mkdir()
    (root / "tests").mkdir()
    (root / "src" / "schema.orl").write_text('''use oriel.db\n\nentity Product {\n    id: Id\n    code: String required unique\n    name: String required\n    quantity: Int required default 0\n    price: Decimal required default 0\n}\n''', encoding="utf-8")
    (root / "oriel.toml").write_text(f'''[project]\nname = "{name}"\nversion = "0.1.0"\nprofile = "database"\nentry = "src/schema.orl"\n\n[database]\nengine = "sqlite"\npath = "data/{name}.db"\n\n[dependencies]\n"oriel.core" = "0.9.1"\n"oriel.db" = "0.9.1"\n''', encoding="utf-8")
    (root / "README.md").write_text("# ORIEL Database Project\n\nRun `oriel db migrate src/schema.orl`.\n", encoding="utf-8")
    return root
