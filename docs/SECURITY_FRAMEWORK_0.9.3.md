# ORIEL Authentication and Security Framework 0.9.3

ORIEL 0.9.3 supplies dependency-free security building blocks for its API framework and future web framework.

`PasswordHasher` creates salted PBKDF2-SHA256 hashes with a configurable work factor, constant-time verification, and rehash detection. `TokenService` issues versioned HMAC-SHA256 tokens scoped to an issuer and audience with expiry, roles, permissions, and a unique token ID.

```python
from oriel.security_framework import Identity, PasswordHasher, TokenService

hasher = PasswordHasher()
stored = hasher.hash("user password")
assert hasher.verify("user password", stored)

tokens = TokenService(secret_from_environment, issuer="inventory", audience="inventory-web")
token = tokens.issue(Identity("user-1", roles=("admin",), permissions=("items:write",)))
identity = tokens.verify(token)
```

The framework also provides thread-safe expiring sessions and revocation, session-bound CSRF tokens, permission enforcement, sliding-window rate limiting, and framework-neutral middleware for CSP, referrer, permissions, framing, and MIME-sniffing policies.

## Security boundaries

- Secrets must come from a protected environment or secret manager; never hard-code production secrets.
- The token format is ORIEL-specific and is not advertised as JWT, OAuth 2.0, or OpenID Connect.
- The in-memory session and rate-limit stores are process-local and unsuitable for multi-instance coordination.
- Account storage, password reset, MFA, breached-password screening, key rotation, audit persistence, TLS termination, OAuth providers, and formal security certification are outside this milestone.
- Applications still require threat modeling, dependency review, secure deployment, monitoring, and independent security assessment.
