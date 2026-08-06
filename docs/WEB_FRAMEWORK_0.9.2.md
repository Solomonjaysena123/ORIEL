# ORIEL Web Framework 0.9.2

ORIEL 0.9.2 provides transport-independent primitives for server-rendered applications: requests, responses, parameterized routes, middleware, redirects, safe templates, static files, and an in-process client.

```python
from oriel.web_framework import TemplateEngine, WebApplication, WebResponse

templates = TemplateEngine("templates")
app = WebApplication()

@app.route("/users/{id}")
def user(request):
    page = templates.render("user.html", {"id": request.params["id"]})
    return WebResponse.text(page)
```

Template values are HTML-escaped automatically and template/static paths must remain within their configured roots. Static responses include MIME types and `X-Content-Type-Options: nosniff`. Middleware wraps the same dispatcher used by the test client.

## Limitations

- Templates support escaped scalar variables only; they do not execute expressions, loops, or arbitrary code.
- Route handlers currently use the Python host bridge pending full ORIEL-native request handler execution.
- The milestone does not include a production HTTP server, sessions, CSRF middleware, frontend bundling, hydration, components, WebSockets, or browser automation.
