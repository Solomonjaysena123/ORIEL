# Changelog

## 0.5.0 - 2026-07-29

- Added the `oriel.db` SQLite framework preview.
- Added entity schema parsing and deterministic SQL generation.
- Added database project generation, migrations, and schema inspection.
- Added OpenAPI 3.1 generation for `oriel.api` routes.
- Added structured JSON responses, errors, CORS headers, and query metadata.
- Added database, migration, OpenAPI, and API serialization regression tests.
- Fixed SQLite connection cleanup on Windows to prevent locked database files.

## 0.4.0 - 2026-07-29

- Added multi-file module graphs and `use` imports.
- Added circular-import detection and module graph inspection.
- Added LSP definition, references, rename, and document-symbol foundations.
- Added the first `oriel.api` preview with project generation, route parsing, and local serving.
- Added semantic dependency constraints, transitive resolution, and lock-file format version 2.
- Added module, circular-import, LSP navigation, API route, and package-resolution tests.

## 0.3.0 - 2026-07-28

- Added structured diagnostics with error codes and source locations.
- Added static type annotations and preview type checking.
- Added package manifests, reproducible lock files, and local package commands.
- Added the initial language server with diagnostics, completion, and hover.

## 0.2.0 - 2026-07-28

- Added list literals, indexing, indexed assignment, concatenation, and `for` loops.
- Added UTF-8 file read/write and JSON encode/decode helpers.
- Added project creation, formatting, testing, and reproducible ZIP build commands.
- Added collection, loop, file-system, JSON, and CLI integration tests.
- Added Windows, macOS, and Linux continuous integration.
- Added VS Code snippets for main functions and collection loops.

## 0.1.0

- Added the initial console interpreter and command-line interface.
