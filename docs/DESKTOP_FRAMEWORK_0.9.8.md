# ORIEL Desktop Framework 0.9.8

ORIEL 0.9.8 introduces a shared desktop application contract for Windows, macOS, and Linux.

## Included capabilities

- Validated window configuration, states, events, and lifecycle.
- Portable menus, keyboard shortcuts, tray icons, file dialogs, clipboard, notifications, and safe external links.
- Desktop rendering from the shared ORIEL UI tree with accessibility metadata.
- Windows WiX, macOS Info.plist, and Linux desktop/AppImage project metadata.
- Deterministic Windows/macOS ZIP and Linux tar.gz staging packages with SHA-256 checksums.
- PyInstaller native executable builds on the current host platform.
- HTTPS-only update metadata with checksum verification.
- Explicit symbol allowlists for native-library interoperability.
- Release validation that rejects embedded signing material and requires credentials from the environment.

## CLI

```bash
oriel desktop new DemoDesk --application-id org.example.demo --version 1.0.0
oriel desktop validate DemoDesk
oriel desktop package DemoDesk --target windows
oriel desktop package DemoDesk --target macos
oriel desktop package DemoDesk --target linux
oriel desktop build DemoDesk
```

`package` creates reproducible staging archives on any host. `build` invokes PyInstaller and must run on the target operating system.

## Release signing

Signing material must stay outside the repository. Release validation expects `ORIEL_WINDOWS_CERTIFICATE` on Windows, `ORIEL_APPLE_SIGNING_IDENTITY` and `ORIEL_APPLE_NOTARY_PROFILE` on macOS, and `ORIEL_LINUX_GPG_KEY` on Linux.

Native signing, notarization, MSIX/DMG/AppImage conversion, and store submission remain platform toolchain operations requiring valid external credentials.
