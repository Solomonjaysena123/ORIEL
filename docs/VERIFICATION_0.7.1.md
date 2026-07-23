# ORIEL 0.7.1 Verification Report

## Completed in this repository update

- Updated Python package and VS Code extension metadata to 0.7.1.
- Added shared `CompilerService` API.
- Added shared diagnostic data structures and LSP conversion.
- Routed Language Server diagnostics through the compiler-service API.
- Added unit and LSP tests.
- Added IDE support and implementation-status documentation.
- Added thin-adapter placeholders for JetBrains, Visual Studio, Eclipse and LSP editors.
- Expanded GitHub Actions to test, build and smoke-test on Windows, Ubuntu and macOS.
- Removed generated caches and compiled release files from the normal source repository.

## Local verification

- Automated tests: **32 passed**.
- Python source compilation: **passed**.
- `python -m oriel version`: **Oriel 0.7.1**.
- `python -m oriel run examples/hello.orl`: **passed**.

## Environment limitation

A local wheel/sdist build could not be executed in this sandbox because the `build` package was not available offline. The GitHub Actions workflow installs `build` and runs `python -m build` in its connected CI environment.
