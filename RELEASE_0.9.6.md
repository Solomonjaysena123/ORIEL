# ORIEL v0.9.6 release checklist

## Android Framework

- [x] Android UI renderer, lifecycle, typed device APIs, permissions, notifications, and background work.
- [x] Gradle project generation, secure manifests, resources, debug/release profiles, APK/AAB commands, and store validation.
- [x] Environment-only signing configuration and embedded signing-key detection.
- [x] Deterministic mocks and comprehensive framework/project tests that do not require an emulator.
- [x] v0.9.5 functionality, Python compatibility, CI, VS Code packaging, and MIT licensing preserved.
- [x] Complete Python and ORIEL QA gates pass.
- [x] Generated Android project and store-readiness validation pass.
- [x] Hosted Java 17/Gradle 8.9/Android SDK smoke build produces and verifies a real debug APK.
- [ ] Signed release AAB build and Play submission pass with user-supplied signing and store credentials.
- [x] Wheel, source archive, VSIX, and checksums are built and verified.
- [ ] Commit, push, tag `v0.9.6`, and publish verified release assets.

The current development machine has no Java, Gradle, Android SDK, or ADB installation. That external-toolchain gap must be reported unless a separate Android-capable runner completes the native build.
