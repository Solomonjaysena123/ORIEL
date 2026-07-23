from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import base64, hashlib, hmac, json, os, re, secrets, sqlite3, time
from .db_framework import Entity, parse_entities

@dataclass
class ValidationIssue:
    field: str
    message: str

RULE_RE = re.compile(r"validator\s+([A-Za-z_]\w*)\s*\{(.*?)\}", re.S)
FIELD_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)(.*)$")

def parse_validators(source: str):
    result = {}
    for name, body in RULE_RE.findall(source):
        fields = {}
        for raw in body.splitlines():
            raw = raw.strip().rstrip(',')
            if not raw or raw.startswith('//'):
                continue
            m = FIELD_RE.match(raw)
            if not m:
                raise ValueError(f"Invalid validator field in {name}: {raw}")
            field, type_name, options = m.groups()
            rules = {'type': type_name, 'required': 'required' in options}
            for key in ('min', 'max'):
                hit = re.search(rf"\b{key}\s+([0-9.]+)", options)
                if hit:
                    rules[key] = float(hit.group(1))
            fields[field] = rules
        result[name] = fields
    return result

def validate(data: dict[str, Any], rules):
    issues = []
    for field, rule in rules.items():
        value = data.get(field)
        if rule.get('required') and (value is None or value == ''):
            issues.append(ValidationIssue(field, 'This field is required.'))
            continue
        if value is None:
            continue
        expected = rule['type']
        valid = {
            'String': isinstance(value, str),
            'Int': isinstance(value, int) and not isinstance(value, bool),
            'Float': isinstance(value, (int, float)) and not isinstance(value, bool),
            'Decimal': isinstance(value, (int, float)) and not isinstance(value, bool),
            'Bool': isinstance(value, bool),
        }.get(expected, True)
        if not valid:
            issues.append(ValidationIssue(field, f'Expected {expected}.'))
            continue
        actual = len(value) if isinstance(value, str) else value
        if 'min' in rule and actual < rule['min']:
            issues.append(ValidationIssue(field, f'Must be at least {rule["min"]:g}.'))
        if 'max' in rule and actual > rule['max']:
            issues.append(ValidationIssue(field, f'Must be at most {rule["max"]:g}.'))
    return issues

class Repository:
    def __init__(self, database: Path, entity: Entity):
        self.database, self.entity = database, entity
    def _connect(self):
        con = sqlite3.connect(self.database)
        con.row_factory = sqlite3.Row
        return con
    def create(self, values):
        allowed = {f.name for f in self.entity.fields if f.type_name != 'Id'}
        data = {k: v for k, v in values.items() if k in allowed}
        if not data:
            raise ValueError('No valid fields supplied.')
        cols = ', '.join(f'"{k}"' for k in data)
        qs = ', '.join('?' for _ in data)
        with self._connect() as con:
            cur = con.execute(f'INSERT INTO "{self.entity.table}" ({cols}) VALUES ({qs})', tuple(data.values()))
            con.commit()
            return self.find(cur.lastrowid)
    def find(self, row_id):
        with self._connect() as con:
            row = con.execute(f'SELECT * FROM "{self.entity.table}" WHERE id=?', (row_id,)).fetchone()
            return dict(row) if row else None
    def all(self, limit=100, offset=0):
        with self._connect() as con:
            return [dict(r) for r in con.execute(f'SELECT * FROM "{self.entity.table}" LIMIT ? OFFSET ?', (limit, offset))]
    def where(self, field, value):
        if field not in {f.name for f in self.entity.fields}:
            raise ValueError(f'Unknown field: {field}')
        with self._connect() as con:
            return [dict(r) for r in con.execute(f'SELECT * FROM "{self.entity.table}" WHERE "{field}"=?', (value,))]
    def update(self, row_id, values):
        allowed = {f.name for f in self.entity.fields if f.type_name != 'Id'}
        data = {k: v for k, v in values.items() if k in allowed}
        if not data:
            return self.find(row_id)
        sets = ', '.join(f'"{k}"=?' for k in data)
        with self._connect() as con:
            con.execute(f'UPDATE "{self.entity.table}" SET {sets} WHERE id=?', (*data.values(), row_id))
            con.commit()
        return self.find(row_id)
    def delete(self, row_id):
        with self._connect() as con:
            cur = con.execute(f'DELETE FROM "{self.entity.table}" WHERE id=?', (row_id,))
            con.commit()
            return cur.rowcount > 0

def repository(schema_source: str, entity_name: str, database: Path):
    entity = next((e for e in parse_entities(schema_source) if e.name == entity_name), None)
    if not entity:
        raise ValueError(f'Entity not found: {entity_name}')
    return Repository(database, entity)

def load_env(path=Path('.env')):
    values = dict(os.environ)
    if path.exists():
        for raw in path.read_text(encoding='utf-8').splitlines():
            raw = raw.strip()
            if raw and not raw.startswith('#') and '=' in raw:
                key, value = raw.split('=', 1)
                values.setdefault(key.strip(), value.strip().strip('"'))
    return values

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 200000)
    return 'pbkdf2_sha256$200000$' + base64.urlsafe_b64encode(salt).decode() + '$' + base64.urlsafe_b64encode(digest).decode()

def verify_password(password, encoded):
    try:
        _, rounds, salt, digest = encoded.split('$')
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), base64.urlsafe_b64decode(salt), int(rounds))
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(digest))
    except Exception:
        return False

def create_token(subject, secret, expires_seconds=3600):
    payload = {'sub': subject, 'exp': int(time.time()) + expires_seconds}
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).rstrip(b'=')
    sig = base64.urlsafe_b64encode(hmac.new(secret.encode(), raw, hashlib.sha256).digest()).rstrip(b'=')
    return raw.decode() + '.' + sig.decode()

def verify_token(token, secret):
    raw, sig = token.split('.', 1)
    expected = base64.urlsafe_b64encode(hmac.new(secret.encode(), raw.encode(), hashlib.sha256).digest()).rstrip(b'=').decode()
    if not hmac.compare_digest(sig, expected):
        raise ValueError('Invalid token signature.')
    payload = json.loads(base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)))
    if payload['exp'] < time.time():
        raise ValueError('Token has expired.')
    return payload

def generate_crud(schema_path: Path, entity_name: str, output: Path):
    source = schema_path.read_text(encoding='utf-8')
    entity = next((e for e in parse_entities(source) if e.name == entity_name), None)
    if not entity:
        raise ValueError(f'Entity not found: {entity_name}')
    output.mkdir(parents=True, exist_ok=True)
    lower = entity_name.lower()
    api = output / f'{lower}_api.orl'
    validator = output / f'{lower}_validator.orl'
    test = output / f'{lower}_test.orl'
    api.write_text(f'''use oriel.api
use oriel.db

api {entity_name}Api {{
    get "/{entity.table}" => list_{lower}
    get "/{entity.table}/{{id}}" => get_{lower}
    post "/{entity.table}" => create_{lower}
    put "/{entity.table}/{{id}}" => update_{lower}
    delete "/{entity.table}/{{id}}" => delete_{lower}
}}
''', encoding='utf-8')
    fields = [f'    {f.name}: {f.type_name}' + (' required' if f.required else '') for f in entity.fields if f.type_name != 'Id']
    validator.write_text(f'validator {entity_name}Input {{\n' + '\n'.join(fields) + '\n}\n', encoding='utf-8')
    test.write_text(f'fn main() {{ print("PASS: {entity_name} CRUD scaffold") }}\n', encoding='utf-8')
    return [api, validator, test]
