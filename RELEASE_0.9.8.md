# ORIEL v0.9.8 release checklist

## Milestone

Cross-platform Desktop Framework for Windows, macOS, and Linux.

## Delivered

- [x] Desktop project model and validated scaffolding
- [x] Window, menu, shortcut, tray, file-dialog, clipboard, notification, and external-link contracts
- [x] Shared UI-tree renderer with accessibility metadata
- [x] Windows, macOS, and Linux packaging metadata
- [x] Deterministic ZIP/tar.gz staging packages and SHA-256 checksums
- [x] Native executable build command and native interoperability boundary
- [x] HTTPS-only update metadata and artifact verification
- [x] Signing-material checks and environment-only release credentials
- [x] CLI, automated tests, documentation, CI, MIT licensing, and release packaging

## Credential-bound gaps

- [ ] Windows Authenticode signing/MSIX requires a Windows certificate.
- [ ] macOS signing, notarization, and DMG distribution require Apple credentials.
- [ ] Linux signing/AppImage distribution requires release signing credentials and platform tools.
