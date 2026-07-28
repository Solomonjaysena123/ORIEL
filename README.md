# ORIEL Language 0.3.0 — Foundation Release

ORIEL 0.3 develops the next recommended layer after the console prototype.

## Included

- Structured compiler diagnostics with error codes and source locations
- Static type annotations for variables, parameters and return values
- Preview static type checker
- Local package manifest, dependency install and lock file
- CLI commands: `add`, `remove`, `install`, `packages`, `lsp`
- Preview Language Server Protocol server with live diagnostics, completion and hover
- Existing ORIEL 0.2 console features

## Example

```oriel
fn add(a: Int, b: Int) -> Int {
    return a + b
}

fn main() {
    let total: Int = add(2, 3)
    print(total)
}
```

## Commands

```bash
oriel check src/main.orl
oriel add oriel.text
oriel install
oriel packages
oriel lsp
```

## Scope

This is a developer-preview implementation. The package registry is local and curated; it is not yet an online public registry. The LSP currently provides the foundation for live diagnostics, completion and hover. Full references, rename and cross-module navigation remain future work.
