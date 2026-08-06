# ORIEL v0.9.4 release checklist

## Web Framework

- [x] Typed and named routing, groups, middleware, lifecycle hooks, and custom errors.
- [x] Safe templates, forms, JSON, redirects, cookies, sessions, CSRF, and static files.
- [x] Hardened header handling, bounded session decoding, secure cookie defaults, and v0.9.3 security middleware integration.
- [x] Development server, in-process test client, project scaffolding, and CLI documentation.
- [x] MIT license retained.
- [x] Complete automated test and QA gates pass.
- [x] Wheel, source archive, VS Code package, and checksums are built and verified.
- [ ] Commit, push, tag `v0.9.4`, and publish verified release assets.

The built-in HTTP server is a local development server. Production deployments require an appropriate production transport adapter and operational hardening.
