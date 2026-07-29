# ORIEL Open-Source Architecture

```text
Developer Experience
VS Code Extension | CLI | REPL | Formatter | Tests | Documentation
                          |
Language Services
LSP | Project Manager | Package Manager | Build Manager | Diagnostics
                          |
Compiler Frontend
Source Manager -> Lexer -> Parser -> AST -> Semantic Analysis -> Type Checker
                          |
Intermediate Representation
Typed AST -> ORIEL IR -> Optimizer -> Bytecode Generator
                          |
Runtime System
Virtual Machine | Interpreter | Memory | Exceptions | Modules | Native Bridge
                          |
Standard Library
Core | Text | Math | Collections | Files | JSON | Time | Network | Testing
                          |
Frameworks
API | Database | Web | Desktop | Mobile | Data | AI | Cloud
```

## Dependency rules

- Lexer does not depend on Parser.
- Parser depends only on Lexer, source spans, diagnostics and AST.
- Semantic analysis depends on AST, symbols and types.
- Runtime does not depend on CLI or frameworks.
- CLI coordinates services but contains no compiler logic.
- LSP reuses compiler frontend and semantic analysis.
- Frameworks depend on the standard library and runtime.
- Compiler core never depends on frameworks.

## Current bootstrap mapping

The active 0.7.0 implementation is still partly monolithic. The stabilization branch should progressively split `interpreter.py` into source, lexer, parser, AST, semantic, type and runtime packages without changing public behavior.
