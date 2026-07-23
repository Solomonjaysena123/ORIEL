from __future__ import annotations
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, re
from urllib.parse import parse_qs, urlparse

@dataclass
class Route:
    method: str
    path: str
    handler: str

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


def openapi_manifest(source: str, title: str = "ORIEL API", version: str = "0.1.0") -> dict:
    paths: dict[str, dict] = {}
    for route in route_manifest(source):
        paths.setdefault(route["path"], {})[route["method"].lower()] = {
            "operationId": route["handler"],
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
fn info() -> Map {{ return {{"framework":"oriel.api","version":"0.2.0"}} }}
''', encoding='utf-8')
    (root/'oriel.toml').write_text(f'''[project]
name = "{name}"
version = "0.1.0"
entry = "src/main.orl"
profile = "api"

[dependencies]
"oriel.core" = "0.5.0"
"oriel.api" = "0.2.0"
''', encoding='utf-8')
    return root


def serve(source_path: Path, host='127.0.0.1', port=8000):
    source=source_path.read_text(encoding='utf-8'); routes,handlers=parse_api(source)
    route_map={(r.method,r.path):handlers[r.handler] for r in routes}
    openapi = openapi_manifest(source)
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, payload):
            raw=json.dumps(payload).encode(); self.send_response(status)
            self.send_header('Content-Type','application/json'); self.send_header('Access-Control-Allow-Origin','*')
            self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
        def _handle(self):
            parsed=urlparse(self.path)
            if parsed.path == '/openapi.json':
                return self._send(200, openapi)
            value=route_map.get((self.command,parsed.path))
            if value is None:
                return self._send(404,{"error":{"code":"API404","message":"Route not found","path":parsed.path}})
            self._send(200,{"data":value,"meta":{"method":self.command,"query":parse_qs(parsed.query)}})
        do_GET=_handle; do_POST=_handle; do_PUT=_handle; do_DELETE=_handle; do_PATCH=_handle
        def do_OPTIONS(self):
            self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Methods','GET,POST,PUT,PATCH,DELETE,OPTIONS'); self.end_headers()
        def log_message(self, fmt, *args): print('[oriel.api]', fmt%args)
    print(f'ORIEL API running at http://{host}:{port}')
    print(f'OpenAPI document: http://{host}:{port}/openapi.json')
    ThreadingHTTPServer((host,port),Handler).serve_forever()
