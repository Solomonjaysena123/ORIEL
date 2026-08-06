import unittest

from oriel.security_framework import CSRFProtection, Identity, PasswordHasher, RateLimiter, SessionStore, TokenService, require_permission, security_headers
from oriel.web_framework import WebApplication, WebResponse, WebTestClient


SECRET = "a-secure-development-secret-that-is-long-enough"


class SecurityFramework093Tests(unittest.TestCase):
    def test_password_hashing_and_rehash_policy(self):
        hasher = PasswordHasher(100_000); encoded = hasher.hash("correct horse battery staple")
        self.assertTrue(hasher.verify("correct horse battery staple", encoded))
        self.assertFalse(hasher.verify("wrong", encoded))
        self.assertTrue(PasswordHasher(120_000).needs_rehash(encoded))

    def test_signed_tokens_scope_expiry_and_tampering(self):
        service = TokenService(SECRET, issuer="test", audience="app")
        token = service.issue(Identity("user-1", ("admin",), ("users:read",)), lifetime=60, now=100)
        self.assertEqual(service.verify(token, now=120).subject, "user-1")
        with self.assertRaisesRegex(ValueError, "expired"):
            service.verify(token, now=160)
        with self.assertRaises(ValueError):
            service.verify(token + "x", now=120)

    def test_sessions_revoke_and_expire(self):
        store = SessionStore(); session = store.create(Identity("user-1"), lifetime=10, now=100)
        self.assertIsNotNone(store.get(session.session_id, now=109))
        self.assertIsNone(store.get(session.session_id, now=110))
        another = store.create(Identity("user-2"), now=100)
        self.assertTrue(store.revoke(another.session_id)); self.assertIsNone(store.get(another.session_id, now=101))

    def test_csrf_tokens_bind_to_session(self):
        csrf = CSRFProtection(SECRET); token = csrf.issue("session-a")
        self.assertTrue(csrf.verify("session-a", token))
        self.assertFalse(csrf.verify("session-b", token))

    def test_permissions_and_rate_limits(self):
        identity = Identity("user", permissions=("orders:read",))
        require_permission(identity, "orders:read")
        with self.assertRaises(PermissionError): require_permission(identity, "orders:write")
        limiter = RateLimiter(2, 10)
        self.assertTrue(limiter.allow("user", now=1)); self.assertTrue(limiter.allow("user", now=2)); self.assertFalse(limiter.allow("user", now=3)); self.assertTrue(limiter.allow("user", now=12))

    def test_security_header_middleware(self):
        app = WebApplication(); app.use(security_headers)
        @app.route("/")
        def home(request): return WebResponse.text("ok")
        headers = WebTestClient(app).get("/").headers
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
