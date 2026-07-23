# ORIEL Core 0.2

The second working development release of the ORIEL Software Language.

## New in 0.2

- List literals: `[1, 2, 3]`
- List and string indexing: `items[0]`
- `for item in items` loops
- `none` value
- Built-ins: `len`, `range`, `push`, `type_of`
- File utilities: `read_file`, `write_file`
- JSON utilities: `json_encode`, `json_decode`
- Structured projects with `src`, `tests`, and `oriel.toml`
- CLI commands: `format`, `test`, and `build`

## Install

```bash
python -m pip install oriel_language-0.2.0-py3-none-any.whl
```

## Create and run a project

```bash
oriel new my-app
cd my-app
oriel run src/main.orl
oriel test
oriel build
```

## Example

```oriel
fn main() {
    let platforms = ["Web", "Mobile", "Desktop", "AI"]
    push(platforms, "Cloud")

    for platform in platforms {
        print("Building " + platform + " with ORIEL")
    }

    write_file("platforms.json", json_encode(platforms))
}
```
