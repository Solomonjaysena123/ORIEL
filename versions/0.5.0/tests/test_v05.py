from pathlib import Path
import json

from oriel.api_framework import openapi_manifest, parse_api
from oriel.db_framework import parse_entities, schema_manifest, migrate, inspect_database
from oriel.package_manager import resolve, dependency_graph


def test_openapi_generation():
    source = '''api App { get "/" => home post "/items" => create }\nfn home() -> String { return "hello" }\nfn create() -> Map { return {"ok":true} }'''
    doc = openapi_manifest(source)
    assert doc["openapi"] == "3.1.0"
    assert "get" in doc["paths"]["/"]
    assert "post" in doc["paths"]["/items"]


def test_api_json_literal():
    source = '''api App { get "/info" => info }\nfn info() -> Map { return {"name":"ORIEL"} }'''
    _, handlers = parse_api(source)
    assert handlers["info"] == {"name": "ORIEL"}


def test_entity_schema_and_sql():
    source = '''entity Product {\n id: Id\n code: String required unique\n quantity: Int default 0\n}'''
    entities = parse_entities(source)
    assert entities[0].table == "products"
    manifest = schema_manifest(source)
    assert "CREATE TABLE" in manifest[0]["sql"]
    assert "UNIQUE" in manifest[0]["sql"]


def test_sqlite_migration(tmp_path: Path):
    schema = tmp_path / "schema.orl"
    schema.write_text('''entity Product {\n id: Id\n name: String required\n}''', encoding="utf-8")
    db = tmp_path / "app.db"
    assert migrate(schema, db) == 1
    inspected = inspect_database(db)
    assert "products" in inspected
    assert "_oriel_migrations" in inspected


def test_v05_registry():
    assert resolve("oriel.api", "latest") == "0.2.0"
    graph = dependency_graph({"oriel.db": "0.1.0"})
    assert graph["oriel.core"] == "0.5.0"
