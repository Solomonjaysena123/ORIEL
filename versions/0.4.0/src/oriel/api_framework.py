from __future__ import annotations
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, re

@dataclass
class Route:
    method: str
    path: str
    handler: str

ROUTE_RE = re.compile(r'\b(get|post|put|delete|patch)\s+"([^"]+)"\s*=>\s*([A-Za-z_]\w*)', re.I)
RETURN_RE = re.compile(r'fn\s+([A-Za-z_]\w*)\s*\([^)]*\)(?:\s*->\s*\w+)?\s*\{\s*return\s+"([^"]*)"\s*\}', re.S)

def parse_api(source: str) -> tuple[list[Route], dict[str,str]]:
    routes=[Route(m.upper(), p, h) for m,p,h in ROUTE_RE.findall(source)]
    handlers={name:value for name,value in RETURN_RE.findall(source)}
    if not routes:
        raise ValueError('No API routes found. Example: get "/" => home')
    missing=[r.handler for r in routes if r.handler not in handlers]
    if missing:
        raise ValueError('Missing handler function(s): ' + ', '.join(sorted(set(missing))))
    return routes, handlers

def route_manifest(source: str) -> list[dict]:
    routes,_=parse_api(source)
    return [{"method":r.method,"path":r.path,"handler":r.handler} for r in routes]

def create_api_project(name: str, base: Path) -> Path:
    root=base/name
    if root.exists(): raise FileExistsError(f'Project already exists: {root}')
    (root/'src').mkdir(parents=True); (root/'tests').mkdir()
    (root/'src'/'main.orl').write_text(f'''use oriel.api

api {name.replace('-', '_').title().replace('_','')} {{
    get "/" => home
    get "/health" => health
}}

fn home() -> String {{ return "Welcome to ORIEL API" }}
fn health() -> String {{ return "ok" }}
''', encoding='utf-8')
    (root/'oriel.toml').write_text(f'''[project]
name = "{name}"
version = "0.1.0"
entry = "src/main.orl"
profile = "api"

[dependencies]
"oriel.core" = "0.4.0"
"oriel.api" = "0.1.0"
''', encoding='utf-8')
    return root

def serve(source_path: Path, host='127.0.0.1', port=8000):
    source=source_path.read_text(encoding='utf-8'); routes,handlers=parse_api(source)
    route_map={(r.method,r.path):handlers[r.handler] for r in routes}
    class Handler(BaseHTTPRequestHandler):
        def _handle(self):
            value=route_map.get((self.command,self.path.split('?',1)[0]))
            if value is None:
                self.send_response(404); payload={"error":"Not found"}
            else:
                self.send_response(200); payload={"data":value}
            raw=json.dumps(payload).encode(); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
        do_GET=_handle; do_POST=_handle; do_PUT=_handle; do_DELETE=_handle; do_PATCH=_handle
        def log_message(self, fmt, *args): print('[oriel.api]', fmt%args)
    print(f'ORIEL API running at http://{host}:{port}')
    ThreadingHTTPServer((host,port),Handler).serve_forever()
