"""Authentication and application-security primitives for ORIEL 0.9.3."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
from dataclasses import dataclass, replace
from typing import Callable, Protocol, TypeVar


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class PasswordHasher:
    algorithm = "pbkdf2_sha256"
    maximum_iterations = 2_000_000

    def __init__(self, iterations: int = 310_000):
        if iterations < 100_000:
            raise ValueError("iterations below security minimum")
        self.iterations = iterations

    def hash(self, password: str) -> str:
        if not password:
            raise ValueError("password must not be empty")
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.iterations)
        return f"{self.algorithm}${self.iterations}${_encode(salt)}${_encode(digest)}"

    def verify(self, password: str, encoded: str) -> bool:
        try:
            algorithm, rounds, salt, expected = encoded.split("$", 3)
            if algorithm != self.algorithm:
                return False
            iteration_count = int(rounds)
            if not 100_000 <= iteration_count <= self.maximum_iterations:
                return False
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _decode(salt), iteration_count)
            return hmac.compare_digest(actual, _decode(expected))
        except (ValueError, TypeError):
            return False

    def needs_rehash(self, encoded: str) -> bool:
        try:
            algorithm, rounds, _, _ = encoded.split("$", 3)
            return algorithm != self.algorithm or int(rounds) != self.iterations
        except (ValueError, TypeError):
            return True


@dataclass(frozen=True)
class Identity:
    subject: str
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()

    def allows(self, permission: str) -> bool:
        return permission in self.permissions or "*" in self.permissions


class TokenService:
    """HMAC-SHA256 signed, versioned authentication tokens."""

    def __init__(self, secret: str, *, issuer: str = "oriel", audience: str = "oriel-app"):
        if len(secret.encode("utf-8")) < 32:
            raise ValueError("token secret must contain at least 32 bytes")
        self.secret = secret.encode("utf-8"); self.issuer = issuer; self.audience = audience

    def issue(self, identity: Identity, *, lifetime: int = 3600, now: int | None = None) -> str:
        if lifetime <= 0: raise ValueError("token lifetime must be positive")
        issued = int(time.time() if now is None else now)
        payload = {"v": 1, "sub": identity.subject, "iss": self.issuer, "aud": self.audience, "iat": issued, "exp": issued + lifetime, "roles": list(identity.roles), "permissions": list(identity.permissions), "jti": secrets.token_hex(16)}
        body = _encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        signature = _encode(hmac.new(self.secret, body.encode("ascii"), hashlib.sha256).digest())
        return body + "." + signature

    def verify(self, token: str, *, now: int | None = None) -> Identity:
        try:
            body, signature = token.split(".", 1)
            expected = _encode(hmac.new(self.secret, body.encode("ascii"), hashlib.sha256).digest())
            if not hmac.compare_digest(signature, expected): raise ValueError("invalid token signature")
            payload = json.loads(_decode(body))
        except Exception as error:
            if isinstance(error, ValueError) and str(error) == "invalid token signature": raise
            raise ValueError("malformed token") from error
        current = int(time.time() if now is None else now)
        if payload.get("iss") != self.issuer or payload.get("aud") != self.audience: raise ValueError("invalid token scope")
        if payload.get("v") != 1 or not isinstance(payload.get("sub"), str) or not payload["sub"]:
            raise ValueError("invalid token payload")
        try:
            issued_at, expires_at = int(payload["iat"]), int(payload["exp"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("invalid token payload") from error
        if issued_at > current: raise ValueError("token issued in the future")
        if current >= expires_at: raise ValueError("token expired")
        return Identity(payload["sub"], tuple(payload.get("roles", ())), tuple(payload.get("permissions", ())))


@dataclass(frozen=True)
class Session:
    session_id: str
    identity: Identity
    expires_at: int


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, Session] = {}; self._lock = threading.Lock()

    def create(self, identity: Identity, *, lifetime: int = 3600, now: int | None = None) -> Session:
        if lifetime <= 0:
            raise ValueError("session lifetime must be positive")
        current = int(time.time() if now is None else now)
        session = Session(secrets.token_urlsafe(32), identity, current + lifetime)
        with self._lock: self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str, *, now: int | None = None) -> Session | None:
        current = int(time.time() if now is None else now)
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.expires_at > current: return session
            if session: self._sessions.pop(session_id, None)
        return None

    def revoke(self, session_id: str) -> bool:
        with self._lock: return self._sessions.pop(session_id, None) is not None


class CSRFProtection:
    def __init__(self, secret: str):
        if len(secret.encode("utf-8")) < 32: raise ValueError("CSRF secret must contain at least 32 bytes")
        self.secret = secret.encode("utf-8")

    def issue(self, session_id: str) -> str:
        nonce = secrets.token_urlsafe(18)
        signature = _encode(hmac.new(self.secret, f"{session_id}:{nonce}".encode(), hashlib.sha256).digest())
        return nonce + "." + signature

    def verify(self, session_id: str, token: str) -> bool:
        try: nonce, signature = token.split(".", 1)
        except ValueError: return False
        expected = _encode(hmac.new(self.secret, f"{session_id}:{nonce}".encode(), hashlib.sha256).digest())
        return hmac.compare_digest(signature, expected)


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        if limit < 1 or window_seconds < 1: raise ValueError("rate limit values must be positive")
        self.limit = limit; self.window = window_seconds; self._events: dict[str, list[float]] = {}; self._lock = threading.Lock()

    def allow(self, key: str, *, now: float | None = None) -> bool:
        current = time.time() if now is None else now
        with self._lock:
            events = [value for value in self._events.get(key, []) if value > current - self.window]
            if len(events) >= self.limit:
                self._events[key] = events; return False
            events.append(current); self._events[key] = events; return True


def require_permission(identity: Identity | None, permission: str) -> None:
    if identity is None: raise PermissionError("authentication required")
    if not identity.allows(permission): raise PermissionError(f"permission required: {permission}")


class HeaderResponse(Protocol):
    headers: dict[str, str]


ResponseT = TypeVar("ResponseT", bound=HeaderResponse)


def security_headers(request: object, next_handler: Callable[[object], ResponseT]) -> ResponseT:
    response = next_handler(request)
    headers = {**response.headers, "Content-Security-Policy": "default-src 'self'; object-src 'none'; frame-ancestors 'none'", "Referrer-Policy": "strict-origin-when-cross-origin", "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Permissions-Policy": "camera=(), microphone=(), geolocation=()"}
    return replace(response, headers=headers)
