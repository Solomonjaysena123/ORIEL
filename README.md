# Oriel CLI 0.2.0

Oriel 0.2.0 expands the prototype interpreter with collections, loops, file
operations, JSON utilities, and complete project workflows.

## Install

```bash
python -m pip install .
```

## Commands

```bash
oriel version
oriel run examples/collections.orl
oriel check examples/collections.orl
oriel new my_project
oriel format my_project
oriel test --path my_project
oriel build --path my_project
```

## Collections and loops

```oriel
fn main() {
    var values = [1, 2, 3]
    values[1] = 5

    for value in values {
        print(value)
    }

    print(values[0])
    print(length(values))
}
```

Lists support indexing, negative indexing, indexed assignment, concatenation,
and iteration. Strings support indexing and iteration.

## Files and JSON

```oriel
fn main() {
    write_file("data.json", json_encode([1, 2, 3]))
    let values = json_decode(read_file("data.json"))
    print(values[1])
}
```

Built-in helpers are `read_file`, `write_file`, `json_encode`, `json_decode`,
and `length`.
