# ORIEL Language 0.4.0 — Modules, LSP and API Framework

ORIEL 0.4 advances the language platform with:

- Project modules using `use utilities` or `use "utilities.orl"`
- Module graph resolution and circular-import detection
- Stronger package resolution with semantic constraints and transitive dependencies
- Lock-file format version 2 with checksums and dependency metadata
- LSP definitions, references, rename, document symbols, completions, hover and diagnostics
- First functional framework package: `oriel.api`
- API project generator, route inspection and development server

## Install

```powershell
python -m pip install --upgrade .\oriel_language-0.4.0-py3-none-any.whl
```

## Modules

`src/math_tools.orl`:

```oriel
fn double(value: Int) -> Int { return value * 2 }
```

`src/main.orl`:

```oriel
use math_tools
fn main() { print(double(10)) }
```

```powershell
oriel run src\main.orl
oriel graph src\main.orl
```

## API Framework

```powershell
oriel api new hello-api
cd hello-api
oriel api routes src\main.orl
oriel api serve src\main.orl --port 8000
```
