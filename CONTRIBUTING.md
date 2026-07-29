# Contributing to ORIEL

1. Fork the repository and create a focused branch.
2. Add or update tests for every behavior change.
3. Run `python -m pytest` before opening a pull request.
4. Keep compiler layers independent according to `docs/ARCHITECTURE.md`.
5. Update documentation and `CHANGELOG.md` for user-visible changes.
6. Do not mark roadmap features complete without working source and passing tests.

Commit style examples:

- `feat(parser): support typed function returns`
- `fix(runtime): preserve lexical scope in closures`
- `test(lexer): add malformed string regressions`
- `docs: clarify package manifest format`
