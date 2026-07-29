# ORIEL Software Language 0.5

ORIEL 0.5 adds the first database framework and expands `oriel.api`.

## New in 0.5

- `oriel.db` SQLite schema framework
- `entity` schema parser and SQL generation
- Database project generator, migration, and inspection commands
- `oriel.api` OpenAPI 3.1 generation
- Structured JSON API responses and errors
- JSON object/array handler responses
- CORS headers and query-string metadata
- Updated local package registry and dependency graph

## Commands

```bash
oriel db new inventory-db
oriel db schema src/schema.orl
oriel db migrate src/schema.orl --database data/inventory.db
oriel db inspect data/inventory.db
oriel api openapi src/main.orl --output openapi.json
oriel api serve src/main.orl --port 8000
```

This remains a prototype implementation distributed through Python.
