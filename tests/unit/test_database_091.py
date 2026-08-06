import tempfile
import unittest
from pathlib import Path

from oriel.db_framework import Database, migrate, migration_history, parse_entities

SCHEMA = """entity Product {
    id: Id
    code: String required unique
    quantity: Int required default 0
}
"""

class DatabaseFramework091Tests(unittest.TestCase):
    def test_duplicate_schema_names_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate entity"):
            parse_entities("entity Item { id: Id } entity Item { id: Id }")
        with self.assertRaisesRegex(ValueError, "Duplicate field"):
            parse_entities("entity Item {\n id: Id\n id: Int\n}")

    def test_migrations_are_idempotent_and_auditable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); schema = root / "schema.orl"; database = root / "app.db"
            schema.write_text(SCHEMA, encoding="utf-8")
            self.assertEqual(migrate(schema, database), 1)
            self.assertEqual(migrate(schema, database), 0)
            history = migration_history(database)
            self.assertEqual(len(history), 1)
            self.assertEqual(len(history[0]["checksum"]), 64)

    def test_transaction_commit_and_query(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Database(Path(folder) / "app.db")
            database.execute("CREATE TABLE values_table (id INTEGER PRIMARY KEY, value TEXT)")
            database.execute("INSERT INTO values_table(value) VALUES (?)", ("safe",))
            self.assertEqual(database.query("SELECT value FROM values_table"), [{"value": "safe"}])
            self.assertTrue(database.healthy())

    def test_transaction_rolls_back_on_error(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Database(Path(folder) / "app.db")
            database.execute("CREATE TABLE values_table (value TEXT)")
            with self.assertRaises(RuntimeError):
                with database.transaction() as connection:
                    connection.execute("INSERT INTO values_table VALUES ('discard')")
                    raise RuntimeError("rollback")
            self.assertEqual(database.query("SELECT * FROM values_table"), [])
