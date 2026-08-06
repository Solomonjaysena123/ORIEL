# ORIEL Web Framework 0.9.4

ORIEL 0.9.4 provides a dependency-free web framework that can be tested without opening a network socket and served through its built-in development HTTP server.

## Application and routing

```python
from oriel.web_framework import WebApplication, WebResponse

app = WebApplication()

@app.get("/users/{id:int}", name="user")
def user(request):
    return WebResponse.json({"id": request.params["id"]})
```

Routes support `str`, `int`, `float`, `slug`, and `path` parameters. Applications also support named routes, reverse URL generation, prefixed route groups, GET, HEAD, POST, PUT, and DELETE dispatch, 404/405 responses, and configurable error handlers.

## Middleware and lifecycle

Use `app.use(middleware)` for ordered global middleware. Route groups may have their own middleware. `before_request` and `after_request` hooks receive the routed request, including converted path parameters.

The v0.9.3 `oriel.security_framework.security_headers` middleware works directly with web responses and supplies CSP, referrer, content-type, frame, and permissions policies.

## Templates and static files

`TemplateEngine` supports escaped variables, conditionals, and loops without evaluating arbitrary Python expressions. Template and static paths are resolved beneath configured roots to prevent traversal.

`StaticFiles` provides MIME detection, SHA-256 ETags, cache-control headers, conditional requests, and `nosniff` protection.

## Forms, sessions, and CSRF

`WebRequest.form()` parses URL-encoded forms, and `parse_form` applies field converters. `WebRequest.json()` rejects malformed JSON with a 400 response.

`SessionMiddleware` signs cookie data with HMAC-SHA256, applies an expiry, rejects malformed or oversized tokens, and uses Secure, HttpOnly, and SameSite cookie settings by default. Place `SessionMiddleware` before `CSRFMiddleware`.

```python
app.use(SessionMiddleware("replace-with-at-least-16-bytes"))
app.use(CSRFMiddleware())
```

For production, use a randomly generated secret, HTTPS, a production WSGI/ASGI adapter, and environment-specific security policies. The bundled threaded server is intended for local development.

## Testing

```python
from oriel.web_framework import WebTestClient

client = WebTestClient(app)
response = client.get("/users/42")
assert response.status == 200
```

The test client retains cookies, supports forms and JSON bodies, conditional headers, all framework methods, and one-hop redirect following.

## CLI

```bash
oriel web new example
oriel web serve example/src/app.py --host 127.0.0.1 --port 8080
```

The application file must define `app = WebApplication()`.
