"""Dependency-free server-rendered web primitives for ORIEL 0.9.2."""

from __future__ import annotations

import html
import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class WebRequest:
    method: str
    path: str
    query: dict[str, list[str]] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    body: bytes = b""


@dataclass(frozen=True)
class WebResponse:
    body: bytes = b""
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def text(cls, value: str, status: int = 200, content_type: str = "text/html; charset=utf-8") -> "WebResponse":
        return cls(value.encode("utf-8"), status, {"Content-Type": content_type})

    @classmethod
    def redirect(cls, location: str, status: int = 302) -> "WebResponse":
        if status not in {301, 302, 303, 307, 308}:
            raise ValueError("invalid redirect status")
        return cls(b"", status, {"Location": location})


class TemplateEngine:
    """Escaping variable renderer; templates cannot execute code."""

    _variable = re.compile(r"{{\s*([A-Za-z_]\w*)\s*}}")

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def _resolve(self, name: str) -> Path:
        candidate = (self.root / name).resolve()
        if self.root != candidate and self.root not in candidate.parents:
            raise ValueError("template path escapes configured root")
        if candidate.suffix not in {".html", ".htm"}:
            raise ValueError("templates must be HTML files")
        return candidate

    def render(self, name: str, context: dict[str, object] | None = None) -> str:
        source = self._resolve(name).read_text(encoding="utf-8")
        values = context or {}
        return self._variable.sub(lambda match: html.escape(str(values.get(match.group(1), "")), quote=True), source)


@dataclass(frozen=True)
class WebRoute:
    method: str
    path: str
    handler: Callable[[WebRequest], WebResponse]

    def match(self, value: str) -> dict[str, str] | None:
        names: list[str] = []
        fragments: list[str] = []
        for segment in self.path.strip("/").split("/") if self.path != "/" else []:
            if segment.startswith("{") and segment.endswith("}"):
                names.append(segment[1:-1]); fragments.append("([^/]+)")
            else:
                fragments.append(re.escape(segment))
        pattern = "^/" + "/".join(fragments) + "/?$" if fragments else "^/?$"
        matched = re.match(pattern, value)
        return dict(zip(names, matched.groups())) if matched else None


Middleware = Callable[[WebRequest, Callable[[WebRequest], WebResponse]], WebResponse]


class WebApplication:
    def __init__(self):
        self.routes: list[WebRoute] = []
        self.middleware: list[Middleware] = []

    def route(self, path: str, *, method: str = "GET"):
        def decorate(handler: Callable[[WebRequest], WebResponse]):
            self.routes.append(WebRoute(method.upper(), path, handler))
            return handler
        return decorate

    def use(self, middleware: Middleware) -> None:
        self.middleware.append(middleware)

    def dispatch(self, request: WebRequest) -> WebResponse:
        def endpoint(current: WebRequest) -> WebResponse:
            path_matches: list[WebRoute] = []
            for route in self.routes:
                params = route.match(current.path)
                if params is not None:
                    path_matches.append(route)
                    if route.method == current.method.upper():
                        enriched = WebRequest(current.method, current.path, current.query, current.headers, params, current.body)
                        return route.handler(enriched)
            if path_matches:
                allowed = ", ".join(sorted({route.method for route in path_matches}))
                return WebResponse(b"Method Not Allowed", 405, {"Content-Type": "text/plain; charset=utf-8", "Allow": allowed})
            return WebResponse.text("Not Found", 404, "text/plain; charset=utf-8")

        next_handler = endpoint
        for layer in reversed(self.middleware):
            following = next_handler
            next_handler = lambda current, layer=layer, following=following: layer(current, following)
        return next_handler(request)


class StaticFiles:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def __call__(self, request: WebRequest) -> WebResponse:
        relative = request.params.get("path", "")
        candidate = (self.root / relative).resolve()
        if self.root != candidate and self.root not in candidate.parents:
            return WebResponse.text("Not Found", 404, "text/plain; charset=utf-8")
        if not candidate.is_file():
            return WebResponse.text("Not Found", 404, "text/plain; charset=utf-8")
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        return WebResponse(candidate.read_bytes(), 200, {"Content-Type": content_type, "X-Content-Type-Options": "nosniff"})


class WebTestClient:
    def __init__(self, app: WebApplication):
        self.app = app

    def request(self, method: str, target: str, *, headers: dict[str, str] | None = None, body: bytes = b"") -> WebResponse:
        parsed = urlparse(target)
        return self.app.dispatch(WebRequest(method.upper(), parsed.path, parse_qs(parsed.query), headers or {}, body=body))

    def get(self, target: str, **kwargs) -> WebResponse:
        return self.request("GET", target, **kwargs)

    def post(self, target: str, **kwargs) -> WebResponse:
        return self.request("POST", target, **kwargs)
