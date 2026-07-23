# ORIEL IDE Support Strategy

ORIEL uses one compiler frontend, one Language Server Protocol (LSP) service and, in a later milestone, one Debug Adapter Protocol (DAP) service. IDE integrations remain thin and must not duplicate parsing, type checking, diagnostics or symbol analysis.

## Official priority

1. Visual Studio Code
2. JetBrains platform, including IntelliJ IDEA and Android Studio
3. Visual Studio
4. Eclipse

## LSP-based support

Neovim, Vim, Emacs, Helix, Zed, Fleet, Kate and Sublime Text will connect to the same `oriel lsp` process.

## ORIEL 0.7.1 scope

- Stable compiler-service API
- Shared diagnostics
- LSP diagnostics and basic language intelligence
- VS Code thin-client verification
- Adapter design notes for other IDEs

Full debugger parity is assigned to the later DAP milestone.
