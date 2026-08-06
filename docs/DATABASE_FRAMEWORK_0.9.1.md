# ORIEL Database Framework 0.9.1

ORIEL schemas define SQLite tables with supported scalar types, required and unique constraints, and defaults. Version 0.9.1 adds deterministic migration tracking and explicit transaction sessions.

```oriel
entity Product {
    id: Id
    code: String required unique
    quantity: Int required default 0
}
```

Each distinct schema source is identified by SHA-256. Applying the same schema again is a no-op, while `oriel db status` returns its source, checksum, and application time.

```python
from oriel.db_framework import Database

database = Database("data/inventory.db")
with database.transaction() as connection:
    connection.execute("INSERT INTO products(code, quantity) VALUES (?, ?)", ("A-1", 3))
```

Transactions commit on successful exit and roll back on exceptions. `execute` and `query` accept parameter tuples so data does not need to be interpolated into SQL.

## Limitations

- SQLite is the only bundled engine.
- Schema migration creates missing tables; destructive column changes, renames, and rollback migrations are not generated.
- Migration checksums identify complete schema sources rather than ordered migration files.
- Connection pooling, replication, async drivers, and distributed transactions are outside this milestone.
