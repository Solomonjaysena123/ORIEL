from pathlib import Path
import tempfile
from oriel.application_services import parse_validators, validate, hash_password, verify_password, create_token, verify_token, repository, generate_crud
from oriel.db_framework import migrate

SCHEMA = '''entity Product {
 id: Id
 name: String required
 quantity: Int required default 0
}
'''

def test_validation():
    rules = parse_validators('validator P {\n name: String required min 2\n}')['P']
    assert validate({'name':'A'}, rules)
    assert not validate({'name':'AB'}, rules)

def test_auth():
    encoded = hash_password('secret')
    assert verify_password('secret', encoded)
    assert not verify_password('bad', encoded)
    token = create_token('user', 'key')
    assert verify_token(token, 'key')['sub'] == 'user'

def test_repository_and_crud():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); schema=root/'schema.orl'; db=root/'db.sqlite'
        schema.write_text(SCHEMA)
        migrate(schema, db)
        repo=repository(SCHEMA, 'Product', db)
        row=repo.create({'name':'Bearing','quantity':4})
        assert repo.find(row['id'])['name']=='Bearing'
        assert repo.update(row['id'], {'quantity':8})['quantity']==8
        assert repo.delete(row['id'])
        files=generate_crud(schema, 'Product', root/'generated')
        assert len(files)==3 and all(f.exists() for f in files)
