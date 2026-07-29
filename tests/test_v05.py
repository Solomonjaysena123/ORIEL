from pathlib import Path
import json
import tempfile
import unittest

from oriel.api_framework import openapi_manifest, parse_api
from oriel.db_framework import parse_entities, schema_manifest, migrate, inspect_database
from oriel.package_manager import resolve, dependency_graph


class V05Tests(unittest.TestCase):
    def test_openapi_generation(self):
        source = '''api App { get "/" => home post "/items" => create }
fn home() -> String { return "hello" }
fn create() -> Map { return {"ok":true} }'''
        document = openapi_manifest(source)
        self.assertEqual(document['openapi'], '3.1.0')
        self.assertIn('get', document['paths']['/'])
        self.assertIn('post', document['paths']['/items'])

    def test_api_json_literal_serialization(self):
        source = '''api App { get "/info" => info }
fn info() -> Map { return {"name":"ORIEL"} }'''
        _, handlers = parse_api(source)
        self.assertEqual(handlers['info'], {'name': 'ORIEL'})
        self.assertEqual(json.loads(json.dumps(handlers['info'])), {'name': 'ORIEL'})

    def test_entity_schema_and_sql_snapshot(self):
        source = '''entity Product {
 id: Id
 code: String required unique
 quantity: Int default 0
}'''
        entities = parse_entities(source)
        self.assertEqual(entities[0].table, 'products')
        manifest = schema_manifest(source)
        self.assertIn('CREATE TABLE', manifest[0]['sql'])
        self.assertIn('UNIQUE', manifest[0]['sql'])
        self.assertIn('DEFAULT 0', manifest[0]['sql'])

    def test_sqlite_migration_and_inspection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schema = root / 'schema.orl'
            schema.write_text(
                '''entity Product {
 id: Id
 name: String required
}''',
                encoding='utf-8',
            )
            database = root / 'app.db'
            self.assertEqual(migrate(schema, database), 1)
            inspected = inspect_database(database)
            self.assertIn('products', inspected)
            self.assertIn('_oriel_migrations', inspected)
            self.assertTrue(any(column['name'] == 'name' for column in inspected['products']))

    def test_v05_registry(self):
        self.assertEqual(resolve('oriel.api', 'latest'), '0.2.0')
        graph = dependency_graph({'oriel.db': '0.1.0'})
        self.assertEqual(graph['oriel.core'], '0.5.0')


if __name__ == '__main__':
    unittest.main()
