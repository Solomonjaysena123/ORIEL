import tempfile
import time
from pathlib import Path

import pytest

from oriel.cli import build_parser
from oriel.security_framework import security_headers as hardened_security_headers
from oriel.web_framework import (
    BadRequest,
    CSRFMiddleware,
    SessionCodec,
    SessionMiddleware,
    StaticFiles,
    TemplateEngine,
    WebApplication,
    WebRequest,
    WebResponse,
    WebTestClient,
    create_web_project,
    load_application,
    parse_form,
)


def test_typed_named_routes_groups_hooks_and_methods():
    app = WebApplication()
    seen = []
    group = app.group("/admin", name_prefix="admin.")

    @app.before_request
    def before(request):
        seen.append(("before", request.params["id"]))

    @app.after_request
    def after(request, response):
        seen.append(("after", request.params["id"]))
        return response.with_header("X-Hook", "yes")

    @group.get("/users/{id:int}", name="user")
    def user(request):
        return WebResponse.json({"id": request.params["id"]})

    client = WebTestClient(app)
    response = client.get("/admin/users/42")
    assert response.body == b'{"id":42}'
    assert response.headers["X-Hook"] == "yes"
    assert seen == [("before", 42), ("after", 42)]
    assert client.request("HEAD", "/admin/users/42").status == 200
    wrong_method = client.post("/admin/users/42")
    assert wrong_method.status == 405
    assert wrong_method.headers["Allow"] == "GET, HEAD"
    assert client.get("/admin/users/no").status == 404
    assert app.url_for("admin.user", id=7) == "/admin/users/7"
    with pytest.raises(ValueError, match="duplicate route"):
        app.get("/admin/users/{id:int}")(user)


def test_templates_confine_paths_and_escape_values():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "page.html").write_text(
            "{% if show %}{% for item in items %}<b>{{ item }}</b>{% endfor %}{% endif %}",
            encoding="utf-8",
        )
        rendered = TemplateEngine(root).render(
            "page.html", {"show": True, "items": ["<script>", "safe"]}
        )
        assert rendered == "<b>&lt;script&gt;</b><b>safe</b>"
        with pytest.raises(ValueError, match="escapes"):
            TemplateEngine(root).render("../page.html")


def test_sessions_csrf_multiple_cookies_and_tamper_resistance():
    app = WebApplication()
    app.use(SessionMiddleware("1234567890123456", secure=False))
    app.use(CSRFMiddleware())

    @app.get("/token")
    def token(request):
        return WebResponse.text(
            request.context["csrf_token"], content_type="text/plain; charset=utf-8"
        ).set_cookie("preference", "compact", secure=False)

    @app.post("/save")
    def save(request):
        request.context["session"]["saved"] = True
        return WebResponse.text("ok")

    client = WebTestClient(app)
    csrf_token = client.get("/token").body.decode()
    assert {"oriel_session", "preference"} <= client.cookies.keys()
    assert client.post("/save", form={"_csrf": csrf_token}).status == 200
    assert client.post("/save", form={"_csrf": "bad"}).status == 403
    client.cookies["oriel_session"] += "tampered"
    assert client.get("/token").status == 200

    with pytest.raises(ValueError, match="positive"):
        SessionCodec("1234567890123456", ttl=0)
    assert SessionCodec("1234567890123456").decode("x" * 20_000) == {}


def test_requests_forms_json_errors_and_hardened_security_integration():
    app = WebApplication(debug=False)
    app.use(hardened_security_headers)

    @app.post("/payload")
    def payload(request):
        values, errors = parse_form(request, {"age": int, "name": str})
        return WebResponse.json({"values": values, "errors": errors})

    @app.post("/json")
    def json_endpoint(request):
        return WebResponse.json(request.json())

    client = WebTestClient(app)
    form_response = client.post("/payload", form={"age": "20", "name": "A"})
    assert b'"age":20' in form_response.body
    response = client.post("/json", json_body={"ok": True})
    assert response.body == b'{"ok":true}'
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
    bad = client.post(
        "/json",
        headers={"Content-Type": "application/json"},
        body=b"{bad",
    )
    assert bad.status == BadRequest.status


def test_static_files_etags_redirects_and_header_validation():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "asset.txt").write_text("asset", encoding="utf-8")
        app = WebApplication()
        app.get("/static/{path:path}")(StaticFiles(root))
        app.get("/go")(lambda request: WebResponse.redirect("/static/asset.txt"))
        client = WebTestClient(app)
        first = client.get("/static/asset.txt")
        assert first.status == 200
        assert first.headers["X-Content-Type-Options"] == "nosniff"
        assert client.get(
            "/static/asset.txt", headers={"If-None-Match": first.headers["ETag"]}
        ).status == 304
        assert client.get("/../secret").status == 404
        assert client.get("/go", follow_redirects=True).body == b"asset"

    with pytest.raises(ValueError, match="location"):
        WebResponse.redirect("/safe\r\nX-Evil: yes")
    with pytest.raises(ValueError, match="header"):
        WebResponse.text("ok").with_header("X-Test", "safe\r\nevil")


def test_scaffold_loader_and_cli_contract():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        project = create_web_project("demo", root)
        app = load_application(project / "src" / "app.py")
        assert WebTestClient(app).get("/").status == 200
        args = build_parser().parse_args(
            ["web", "serve", str(project / "src" / "app.py"), "--port", "9000"]
        )
        assert args.web_command == "serve"
        assert args.port == 9000
        with pytest.raises(ValueError, match="existing Python"):
            load_application(project / "missing.py")


def test_expired_session_is_rejected(monkeypatch):
    codec = SessionCodec("1234567890123456", ttl=1)
    token = codec.encode({"user": "one"})
    monkeypatch.setattr(time, "time", lambda: 9_999_999_999)
    assert codec.decode(token) == {}
