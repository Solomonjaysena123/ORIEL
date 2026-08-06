from __future__ import annotations
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, re
from urllib.parse import parse_qs, urlparse

@dataclass
class Route:
    method: str
    path: str
    handler: str

    def match(self, path: str) -> dict[str, str] | None:
        names: list[str] = []
        parts: list[str] = []
        for segment in self.path.strip('/').split('/') if self.path != '/' else []:
            if segment.startswith('{') and segment.endswith('}'):
                names.append(segment[1:-1])
                parts.append(r'([^/]+)')
            else:
                parts.append(re.escape(segment))
        pattern = r'^/' + '/'.join(parts) + r'/?$' if parts else r'^/?$'
        matched = re.match(pattern, path)
        return dict(zip(names, matched.groups())) if matched else None


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    query: dict[str, list[str]] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    body: object = None
    params: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Response:
    status: int = 200
    body: object = None
    headers: dict[str, str] = field(default_factory=dict)


class APIApplication:
    """Compiled ORIEL API with transport-independent request dispatch."""

    def __init__(self, source: str, *, title: str = 'ORIEL API', version: str = '0.9.2'):
        self.source = source
        self.routes, self.handlers = parse_api(source)
        self.openapi = openapi_manifest(source, title, version)

    def dispatch(self, request: Request) -> Response:
        if request.path == '/openapi.json':
            return Response(body=self.openapi)
        path_matches: list[tuple[Route, dict[str, str]]] = []
        for route in self.routes:
            params = route.match(request.path)
            if params is not None:
                path_matches.append((route, params))
                if route.method == request.method.upper():
                    value = self.handlers[route.handler]
                    return Response(body={'data': value, 'meta': {'method': request.method.upper(), 'query': request.query, 'params': params}})
        if path_matches:
            allowed = sorted({route.method for route, _ in path_matches})
            return Response(405, {'error': {'code': 'API405', 'message': 'Method not allowed', 'path': request.path}}, {'Allow': ', '.join(allowed)})
        return Response(404, {'error': {'code': 'API404', 'message': 'Route not found', 'path': request.path}})


class TestClient:
    """In-process client for deterministic API tests."""

    __test__ = False

    def __init__(self, app: APIApplication):
        self.app = app

    def request(self, method: str, target: str, *, json_body: object = None, headers: dict[str, str] | None = None) -> Response:
        parsed = urlparse(target)
        return self.app.dispatch(Request(method.upper(), parsed.path, parse_qs(parsed.query), headers or {}, json_body))

    def get(self, target: str, **kwargs) -> Response:
        return self.request('GET', target, **kwargs)

    def post(self, target: str, **kwargs) -> Response:
        return self.request('POST', target, **kwargs)

ROUTE_RE = re.compile(r'\b(get|post|put|delete|patch)\s+"([^"]+)"\s*=>\s*([A-Za-z_]\w*)', re.I)
RETURN_RE = re.compile(r'fn\s+([A-Za-z_]\w*)\s*\([^)]*\)(?:\s*->\s*\w+)?\s*\{\s*return\s+(.+?)\s*\}\s*(?=fn\b|$)', re.S)


def _literal(value: str):
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value in ('true', 'false'):
        return value == 'true'
    if value == 'none':
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


def parse_api(source: str) -> tuple[list[Route], dict[str, object]]:
    routes=[Route(m.upper(), p, h) for m,p,h in ROUTE_RE.findall(source)]
    handlers={name:_literal(value) for name,value in RETURN_RE.findall(source)}
    if not routes:
        raise ValueError('No API routes found. Example: get "/" => home')
    missing=[r.handler for r in routes if r.handler not in handlers]
    if missing:
        raise ValueError('Missing handler function(s): ' + ', '.join(sorted(set(missing))))
    return routes, handlers


def route_manifest(source: str) -> list[dict]:
    routes,_=parse_api(source)
    return [{"method":r.method,"path":r.path,"handler":r.handler} for r in routes]


def openapi_manifest(source: str, title: str = "ORIEL API", version: str = "0.9.2") -> dict:
    paths: dict[str, dict] = {}
    for route in route_manifest(source):
        parameters = [{"name": name, "in": "path", "required": True, "schema": {"type": "string"}} for name in re.findall(r'\{([^}]+)\}', route["path"])]
        paths.setdefault(route["path"], {})[route["method"].lower()] = {
            "operationId": route["handler"],
            "parameters": parameters,
            "responses": {"200": {"description": "Successful response"}, "404": {"description": "Not found"}},
        }
    return {"openapi": "3.1.0", "info": {"title": title, "version": version}, "paths": paths}


def create_api_project(name: str, base: Path) -> Path:
    root=base/name
    if root.exists(): raise FileExistsError(f'Project already exists: {root}')
    (root/'src').mkdir(parents=True); (root/'tests').mkdir()
    (root/'src'/'main.orl').write_text(f'''use oriel.api

api {name.replace('-', '_').title().replace('_','')} {{
    get "/" => home
    get "/health" => health
    get "/info" => info
}}

fn home() -> String {{ return "Welcome to ORIEL API" }}
fn health() -> String {{ return "ok" }}
fn info() -> Map {{ return {{"framework":"oriel.api","version":"0.9.2"}} }}
''', encoding='utf-8')
    (root/'oriel.toml').write_text(f'''[project]
name = "{name}"
version = "0.1.0"
entry = "src/main.orl"
profile = "api"

[dependencies]
"oriel.core" = "0.9.2"
"oriel.api" = "0.9.2"
''', encoding='utf-8')
    return root


def serve(source_path: Path, host='127.0.0.1', port=8000):
    app = APIApplication(source_path.read_text(encoding='utf-8'))
    class Handler(BaseHTTPRequestHandler):
        def _send(self, response):
            status, payload = response.status, response.body
            raw=json.dumps(payload).encode(); self.send_response(status)
            self.send_header('Content-Type','application/json'); self.send_header('Access-Control-Allow-Origin','*')
            for name, value in response.headers.items(): self.send_header(name, value)
            self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
        def _handle(self):
            parsed=urlparse(self.path)
            length = int(self.headers.get('Content-Length', '0'))
            raw = self.rfile.read(length) if length else b''
            try: body = json.loads(raw) if raw else None
            except json.JSONDecodeError: return self._send(Response(400, {'error': {'code': 'API400', 'message': 'Invalid JSON body'}}))
            request = Request(self.command, parsed.path, parse_qs(parsed.query), dict(self.headers.items()), body)
            self._send(app.dispatch(request))
        do_GET=_handle; do_POST=_handle; do_PUT=_handle; do_DELETE=_handle; do_PATCH=_handle
        def do_OPTIONS(self):
            self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','GET,POST,PUT,PATCH,DELETE,OPTIONS'); self.end_headers()
        def log_message(self, fmt, *args): print('[oriel.api]', fmt%args)
    print(f'ORIEL API running at http://{host}:{port}')
    print(f'OpenAPI document: http://{host}:{port}/openapi.json')
    ThreadingHTTPServer((host,port),Handler).serve_forever()
