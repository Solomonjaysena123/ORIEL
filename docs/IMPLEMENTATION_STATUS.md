# ORIEL Implementation Status

## Current version: 0.8.1

A feature is complete only when code, automated tests, documentation, CI configuration and reproducible source artifacts are present.

| Version | Capability | Status | Verification |
|---|---|---|---|
| 0.7.4 | Package manager | Implemented and tested | Semantic constraints, transitive resolution, deterministic lock file, path dependencies, local registry publishing and offline installation tests |
| 0.7.5 | LSP and VS Code | Implemented and tested foundation | Diagnostics, completion, hover, definition, references, rename and document symbols; VS Code starts the shared stdio server |
| 0.8.0 | IR, bytecode and VM | Implemented and tested foundation | Typed AST compilation, serializable versioned IR, stack VM, functions, control flow, lists, calls and interpreter-independent execution |
| 0.8.1 | Debugging, profiling and optimization | Implemented and tested foundation | Source-line breakpoints, local-variable snapshots, instruction profiling, VM benchmarking and safe peephole optimization |

## Current limitations

- The package registry is local/offline; a hosted public registry and signed remote transport remain future work.
- The LSP currently indexes one open document at a time; workspace-wide module indexing and incremental analysis remain future work.
- The VM supports the current core AST but does not yet implement async execution, exceptions, closures or garbage collection.
- The debugger records breakpoint events but does not yet expose a full Debug Adapter Protocol server.
- Optimization is a conservative peephole pass rather than a control-flow/data-flow optimizer.
