# ORIEL 0.7.0

ORIEL V0.7.0 delivers the roadmap's Initial Console Foundation with portable bytecode, an interactive REPL, environment diagnostics, documentation generation, benchmarking, and the complete ORIEL 0.6 application-services layer.

## Console commands

- `oriel compile <file>` - compile ORIEL source into a portable `.obc` preview artifact.
- `oriel run-bytecode <file>` - validate and execute an ORIEL bytecode artifact.
- `oriel repl` - start the interactive console.
- `oriel doctor` - inspect the local development environment.
- `oriel docs <file>` - generate Markdown API documentation.
- `oriel benchmark <file>` - run a repeatable execution benchmark.

## Validation

The release includes 28 automated tests covering the console milestone and all prior roadmap foundations. Python 3.10 or newer is required.
