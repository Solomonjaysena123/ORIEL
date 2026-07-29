from pathlib import Path
import tempfile
import unittest

from oriel.application_services import (
    parse_validators, validate, hash_password, verify_password,
    create_token, verify_token, repository, generate_crud, load_env,
)
from oriel.db_framework import migrate

SCHEMA = '''entity Product {
 id: Id
 name: String required
 quantity: Int required default 0
}
'''


class V06Tests(unittest.TestCase):
    def test_validation_matrix(self):
        rules = parse_validators(
            '''validator ProductInput {
 name: String required min 2 max 10
 quantity: Int min 0
}'''
        )['ProductInput']
        self.assertTrue(validate({'name': 'A', 'quantity': 1}, rules))
        self.assertTrue(validate({'name': 'A very long name', 'quantity': -1}, rules))
        self.assertTrue(validate({'name': 42, 'quantity': 1}, rules))
        self.assertFalse(validate({'name': 'Bearing', 'quantity': 4}, rules))

    def test_authentication_utilities(self):
        encoded = hash_password('secret')
        self.assertTrue(verify_password('secret', encoded))
        self.assertFalse(verify_password('bad', encoded))
        token = create_token('user', 'key')
        self.assertEqual(verify_token(token, 'key')['sub'], 'user')
        with self.assertRaises(ValueError):
            verify_token(token, 'wrong-key')

    def test_repository_crud_and_scaffold(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            schema = root / 'schema.orl'
            database = root / 'db.sqlite'
            schema.write_text(SCHEMA, encoding='utf-8')
            migrate(schema, database)
            repo = repository(SCHEMA, 'Product', database)
            row = repo.create({'name': 'Bearing', 'quantity': 4})
            self.assertEqual(repo.find(row['id'])['name'], 'Bearing')
            self.assertEqual(repo.update(row['id'], {'quantity': 8})['quantity'], 8)
            self.assertEqual(len(repo.all()), 1)
            self.assertEqual(len(repo.where('name', 'Bearing')), 1)
            self.assertTrue(repo.delete(row['id']))
            files = generate_crud(schema, 'Product', root / 'generated')
            self.assertEqual(len(files), 3)
            self.assertTrue(all(file.exists() for file in files))

    def test_environment_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('''ORIEL_MODE=development
API_PORT="8080"
''', encoding='utf-8')
            values = load_env(env_file)
            self.assertEqual(values['ORIEL_MODE'], 'development')
            self.assertEqual(values['API_PORT'], '8080')


if __name__ == '__main__':
    unittest.main()
