import tempfile
import unittest
from pathlib import Path

from oriel.web_framework import StaticFiles, TemplateEngine, WebApplication, WebResponse, WebTestClient


class WebFramework092Tests(unittest.TestCase):
    def test_templates_escape_values_and_confine_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / "page.html").write_text("<h1>{{ title }}</h1>", encoding="utf-8")
            engine = TemplateEngine(root)
            self.assertEqual(engine.render("page.html", {"title": "<script>x</script>"}), "<h1>&lt;script&gt;x&lt;/script&gt;</h1>")
            with self.assertRaises(ValueError):
                engine.render("../secret.html")

    def test_dynamic_routes_query_and_redirect(self):
        app = WebApplication()
        @app.route("/users/{id}")
        def user(request):
            return WebResponse.text(f"{request.params['id']}:{request.query['tab'][0]}")
        @app.route("/old")
        def old(request):
            return WebResponse.redirect("/new", 301)
        client = WebTestClient(app)
        self.assertEqual(client.get("/users/42?tab=profile").body, b"42:profile")
        self.assertEqual(client.get("/old").headers["Location"], "/new")

    def test_method_not_allowed_and_middleware(self):
        app = WebApplication()
        @app.route("/submit", method="POST")
        def submit(request):
            return WebResponse.text("ok")
        def security(request, next_handler):
            response = next_handler(request)
            return WebResponse(response.body, response.status, {**response.headers, "X-Frame-Options": "DENY"})
        app.use(security); client = WebTestClient(app)
        response = client.get("/submit")
        self.assertEqual(response.status, 405)
        self.assertEqual(response.headers["Allow"], "POST")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")

    def test_static_files_have_mime_and_block_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / "app.css").write_text("body{}", encoding="utf-8")
            static = StaticFiles(root)
            app = WebApplication(); app.route("/static/{path}")(static); client = WebTestClient(app)
            response = client.get("/static/app.css")
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["Content-Type"], "text/css")
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(client.get("/static/..").status, 404)
