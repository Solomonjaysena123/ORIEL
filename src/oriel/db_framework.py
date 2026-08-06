from __future__ import annotations

from dataclasses import dataclass
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
    for name, body in ENTITY_RE.findall(source):
        fields: list[Field] = []
        for raw in body.splitlines():
            raw = raw.strip().rstrip(",")
            if not raw or raw.startswith("//"):
                continue
            match = FIELD_RE.match(raw)
            if not match:
                raise ValueError(f"Invalid entity field in {name}: {raw}")
            field_name, type_name, options = match.groups()
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
    with sqlite3.connect(database_path) as connection:
        for entity in entities:
            connection.execute(entity_sql(entity))
        connection.execute(
            "CREATE TABLE IF NOT EXISTS _oriel_migrations (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        connection.execute("INSERT INTO _oriel_migrations(source) VALUES (?)", (str(source_path),))
        connection.commit()
    return len(entities)


def inspect_database(database_path: Path) -> dict:
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")
    with sqlite3.connect(database_path) as connection:
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
    (root / "oriel.toml").write_text(f'''[project]\nname = "{name}"\nversion = "0.1.0"\nprofile = "database"\nentry = "src/schema.orl"\n\n[database]\nengine = "sqlite"\npath = "data/{name}.db"\n\n[dependencies]\n"oriel.core" = "0.5.0"\n"oriel.db" = "0.1.0"\n''', encoding="utf-8")
    (root / "README.md").write_text("# ORIEL Database Project\n\nRun `oriel db migrate src/schema.orl`.\n", encoding="utf-8")
    return root
