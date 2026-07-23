# ORIEL 0.7.2 Type System

ORIEL 0.7.2 completes the first dependable static type-checking layer used by the CLI, shared compiler services and every IDE client.

## Supported annotations

- Primitive: `Int`, `Float`, `Number`, `Text`, `String`, `Bool`, `None`, `Any`
- Nullable: `Int?`, `Text?`, and other `T?` forms
- Collections: `List`, `List[Int]`, and nested `List[List[Text]]`
- Functions: typed parameters and return values

## Enforced checks

- Declaration and assignment compatibility
- Immutable `let` protection
- Undefined and duplicate symbols
- Function argument count and argument types
- Boolean conditions for `if`, `while`, `and`, `or`, and `!`
- Numeric operator validation
- Integer indexes for lists and text
- Basic return-path analysis for non-nullable function returns

## IDE architecture

The type checker is exposed through `CompilerService`; IDE extensions must not implement their own typing rules. VS Code, JetBrains, Android Studio, Visual Studio, Eclipse and LSP clients receive the same diagnostics.
