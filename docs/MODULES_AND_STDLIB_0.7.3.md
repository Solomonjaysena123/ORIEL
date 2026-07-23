# ORIEL 0.7.3 Modules and Standard Library

## Module model

ORIEL 0.7.3 provides deterministic dependency-first module resolution, circular-import detection, dotted and relative imports, public re-export metadata, import aliases, and path-containment checks.

```oriel
use tools.math
use tools.text as text
public use shared.logging
use "local_helpers.orl"
```

The bootstrap runtime still executes a flattened graph. Alias and public metadata are preserved by the module API for the language server and future namespace-aware compiler IR. Full namespace-qualified symbol access is planned after the AST/module linker is extracted from the bootstrap interpreter.

## Standard library modules

- `oriel.core`
- `oriel.text`
- `oriel.math`
- `oriel.collections`
- `oriel.files`
- `oriel.json`
- `oriel.time`
- `oriel.config`
- `oriel.logging`
- `oriel.testing`

The `.orl` modules are shipped as Python package data and are also available in the source repository `stdlib/` directory.

## Compatibility

Paths are normalized with `pathlib`, source is read as UTF-8, and relative imports are prevented from escaping the project root.
