# ORIEL Complete Version Index — 0.1.0 to 0.8.1

This document provides a single navigation point for every milestone represented in the consolidated ORIEL repository.

| Version | Representation in repository | Primary evidence |
|---|---|---|
| 0.1.0 | Historical standalone package | `versions/0.1.0/` |
| 0.2.0 | Historical source and tests | `versions/0.2.0/` |
| 0.3.0 | Historical source and tests | `versions/0.3.0/` |
| 0.4.0 | Historical source and tests | `versions/0.4.0/` |
| 0.5.0 | Historical source and tests | `versions/0.5.0/` |
| 0.6.0 | Historical source and tests | `versions/0.6.0/` |
| 0.7.0 | Historical source and tests | `versions/0.7.0/` |
| 0.7.1 | Integrated active development milestone | `src/oriel/`, `tests/`, `docs/VERIFICATION_0.7.1.md` |
| 0.7.2 | Integrated active development milestone | `src/oriel/`, `tests/`, `docs/TYPE_SYSTEM_0.7.2.md`, `docs/VERIFICATION_0.7.2.md` |
| 0.7.3 | Integrated active development milestone | `src/oriel/`, `stdlib/`, `tests/`, `docs/MODULES_AND_STDLIB_0.7.3.md` |
| 0.7.4 | Integrated active development milestone | package-manager source and tests in the active tree |
| 0.7.5 | Integrated active development milestone | LSP, VS Code extension and tests in the active tree |
| 0.8.0 | Integrated active development milestone | IR, bytecode compiler, VM and tests in the active tree |
| 0.8.1 | Current verified baseline | `src/oriel/`, `tests/`, `docs/RELEASE_0.8.1.md`, `pyproject.toml` |

## Important interpretation

The repository is complete as a **consolidated development repository**, not as fourteen duplicated full source folders. Versions 0.1.0–0.7.0 have preserved standalone snapshots. Versions 0.7.1–0.8.1 are successive milestones integrated into the active codebase and documented through source, tests, release notes and verification reports.

For long-term release traceability, create a Git tag for each version and attach build artifacts to GitHub Releases.
