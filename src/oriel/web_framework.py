"""ORIEL 0.9.4 dependency-free web framework.

The module provides transport-independent request dispatch, typed routes, route
names/groups, middleware, templates, forms, secure cookies/sessions, CSRF,
static files, error handling, a small HTTP server and an in-process test client.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import html
import importlib.util
import json
import mimetypes
import re
import secrets
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from email.utils import format_datetime
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import parse_qs, quote, urlencode, urlparse

Handler = Callable[["WebRequest"], "WebResponse"]
Middleware = Callable[["WebRequest", Handler], "WebResponse"]
ErrorHandler = Callable[["WebRequest", Exception | None], "WebResponse"]

@dataclass(frozen=True)
class WebRequest:
    method: str
    path: str
    query: dict[str, list[str]] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    body: bytes = b""
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def cookies(self) -> dict[str, str]:
        cookie = SimpleCookie(); cookie.load(self.header("cookie", ""))
        return {name: morsel.value for name, morsel in cookie.items()}

    def header(self, name: str, default: str = "") -> str:
        wanted=name.lower()
        return next((v for k,v in self.headers.items() if k.lower()==wanted), default)

    def form(self) -> dict[str, list[str]]:
        content_type=self.header("content-type").split(";",1)[0].strip().lower()
        if content_type != "application/x-www-form-urlencoded":
            return {}
        return parse_qs(self.body.decode("utf-8"), keep_blank_values=True)

    def json(self) -> Any:
        if not self.body: return None
        try: return json.loads(self.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BadRequest("Invalid JSON request body") from exc

@dataclass(frozen=True)
class WebResponse:
    body: bytes = b""
    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self)->None:
        if not isinstance(self.status,int) or not 100<=self.status<=599:
            raise ValueError("status must be an HTTP status code")
        if not isinstance(self.body,bytes): raise TypeError("response body must be bytes")
        for name,value in self.headers.items():
            if not name or any(character in name for character in "\r\n:"):
                raise ValueError("invalid response header name")
            if not isinstance(value,str) or "\r" in value:
                raise ValueError("invalid response header value")
            if "\n" in value and name.lower()!="set-cookie":
                raise ValueError("invalid response header value")
            if name.lower()=="set-cookie":
                for line in value.splitlines():
                    parsed=SimpleCookie(); parsed.load(line)
                    if not parsed: raise ValueError("invalid Set-Cookie header")

    @classmethod
    def text(cls, value: str, status: int = 200, content_type: str = "text/html; charset=utf-8") -> "WebResponse":
        if not isinstance(status, int) or not 100 <= status <= 599:
            raise ValueError("status must be an HTTP status code")
        return cls(value.encode("utf-8"), status, {"Content-Type": content_type})

    @classmethod
    def html(cls, value: str, status: int = 200) -> "WebResponse":
        return cls.text(value, status)

    @classmethod
    def json(cls, value: Any, status: int = 200) -> "WebResponse":
        return cls(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode(), status, {"Content-Type":"application/json; charset=utf-8"})

    @classmethod
    def redirect(cls, location: str, status: int = 302) -> "WebResponse":
        if status not in {301,302,303,307,308}: raise ValueError("invalid redirect status")
        if "\r" in location or "\n" in location: raise ValueError("invalid redirect location")
        return cls(b"", status, {"Location":location})

    def with_header(self, name: str, value: str) -> "WebResponse":
        if not name or any(character in name for character in "\r\n:"):
            raise ValueError("invalid response header name")
        if "\r" in value or "\n" in value:
            raise ValueError("invalid response header value")
        return replace(self, headers={**self.headers, name:value})

    def set_cookie(self, name: str, value: str, *, max_age: int | None=None, path: str="/", secure: bool=True, http_only: bool=True, same_site: str="Lax") -> "WebResponse":
        cookie=SimpleCookie(); cookie[name]=value; morsel=cookie[name]
        morsel["path"]=path
        if max_age is not None: morsel["max-age"]=str(max_age)
        if secure: morsel["secure"]=True
        if http_only: morsel["httponly"]=True
        if same_site: morsel["samesite"]=same_site
        rendered=morsel.OutputString()
        existing=self.headers.get("Set-Cookie")
        return replace(self,headers={**self.headers,"Set-Cookie":f"{existing}\n{rendered}" if existing else rendered})

class HTTPError(Exception):
    status=500
    def __init__(self, message: str=""):
        super().__init__(message or HTTPStatus(self.status).phrase)
class BadRequest(HTTPError): status=400
class Forbidden(HTTPError): status=403
class NotFound(HTTPError): status=404

class TemplateEngine:
    """Safe variable/if/for renderer. Expressions and code execution are forbidden."""
    _var=re.compile(r"{{\s*([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*}}")
    _if=re.compile(r"{%\s*if\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*%}(.*?){%\s*endif\s*%}", re.S)
    _for=re.compile(r"{%\s*for\s+([A-Za-z_]\w*)\s+in\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*%}(.*?){%\s*endfor\s*%}", re.S)
    def __init__(self, root: str|Path): self.root=Path(root).resolve()
    def _resolve(self,name: str)->Path:
        candidate=(self.root/name).resolve()
        if self.root!=candidate and self.root not in candidate.parents: raise ValueError("template path escapes configured root")
        if candidate.suffix not in {".html",".htm"}: raise ValueError("templates must be HTML files")
        return candidate
    @staticmethod
    def _get(values: Mapping[str,Any], dotted: str)->Any:
        value: Any=values
        for part in dotted.split("."):
            if isinstance(value, Mapping): value=value.get(part,"")
            else: value=getattr(value,part,"")
        return value
    def _render(self, source: str, values: dict[str,Any])->str:
        source=self._if.sub(lambda m:self._render(m.group(2),values) if self._get(values,m.group(1)) else "",source)
        def loop(m: re.Match[str])->str:
            return "".join(self._render(m.group(3),{**values,m.group(1):item}) for item in (self._get(values,m.group(2)) or []))
        source=self._for.sub(loop,source)
        return self._var.sub(lambda m:html.escape(str(self._get(values,m.group(1))),quote=True),source)
    def render(self,name: str,context: dict[str,Any]|None=None)->str:
        return self._render(self._resolve(name).read_text(encoding="utf-8"),context or {})

_CONVERTERS: dict[str,tuple[str,Callable[[str],Any]]] = {
    "str":(r"[^/]+",str), "int":(r"-?\d+",int), "float":(r"-?(?:\d+(?:\.\d*)?|\.\d+)",float),
    "path":(r".+",str), "slug":(r"[A-Za-z0-9_-]+",str),
}
@dataclass(frozen=True)
class WebRoute:
    method: str; path: str; handler: Handler; name: str|None=None
    def _compiled(self):
        names=[]; converters=[]; fragments=[]
        segments=self.path.strip("/").split("/") if self.path!="/" else []
        for segment in segments:
            match=re.fullmatch(r"{([A-Za-z_]\w*)(?::([A-Za-z]+))?}",segment)
            if match:
                name,kind=match.group(1),match.group(2) or "str"
                if kind not in _CONVERTERS: raise ValueError(f"unknown route converter: {kind}")
                regex,converter=_CONVERTERS[kind]; names.append(name); converters.append(converter); fragments.append(f"({regex})")
            else: fragments.append(re.escape(segment))
        pattern="^/"+"/".join(fragments)+"/?$" if fragments else "^/?$"
        return re.compile(pattern),names,converters
    def match(self,value: str)->dict[str,Any]|None:
        pattern,names,converters=self._compiled(); matched=pattern.match(value)
        if not matched:return None
        try:return {n:c(v) for n,c,v in zip(names,converters,matched.groups())}
        except ValueError:return None

class RouteGroup:
    def __init__(self,app:"WebApplication",prefix: str="",name_prefix: str="",middleware:Iterable[Middleware]=()):
        self.app=app; self.prefix=prefix.rstrip("/"); self.name_prefix=name_prefix; self.middleware=list(middleware)
    def route(self,path: str,*,method: str="GET",name: str|None=None):
        full=(self.prefix+(path if path.startswith("/") else "/"+path)) or "/"
        def deco(handler: Handler):
            wrapped=handler
            for layer in reversed(self.middleware):
                nxt=wrapped; wrapped=lambda req,layer=layer,nxt=nxt:layer(req,nxt)
            self.app.add_route(full,wrapped,method=method,name=self.name_prefix+(name or "") if name else None)
            return handler
        return deco
    def get(self,path: str,**kw): return self.route(path,method="GET",**kw)
    def post(self,path: str,**kw): return self.route(path,method="POST",**kw)

class WebApplication:
    def __init__(self,*,debug: bool=False):
        self.routes:list[WebRoute]=[]; self.middleware:list[Middleware]=[]; self.debug=debug
        self.error_handlers:dict[int,ErrorHandler]={}; self.before_hooks:list[Callable[[WebRequest],None]]=[]; self.after_hooks:list[Callable[[WebRequest,WebResponse],WebResponse]]=[]
    def add_route(self,path: str,handler:Handler,*,method="GET",name: str|None=None):
        if not path.startswith("/"): raise ValueError("route path must start with /")
        if name and any(r.name==name for r in self.routes): raise ValueError(f"duplicate route name: {name}")
        normalized_method=method.upper()
        if any(r.method==normalized_method and r.path==path for r in self.routes):
            raise ValueError(f"duplicate route: {normalized_method} {path}")
        route=WebRoute(normalized_method,path,handler,name)
        route._compiled()
        self.routes.append(route)
    def route(self,path: str,*,method="GET",name: str|None=None):
        def decorate(handler:Handler): self.add_route(path,handler,method=method,name=name); return handler
        return decorate
    def get(self,path: str,**kw): return self.route(path,method="GET",**kw)
    def post(self,path: str,**kw): return self.route(path,method="POST",**kw)
    def put(self,path: str,**kw): return self.route(path,method="PUT",**kw)
    def delete(self,path: str,**kw): return self.route(path,method="DELETE",**kw)
    def group(self,prefix: str="",*,name_prefix: str="",middleware:Iterable[Middleware]=())->RouteGroup: return RouteGroup(self,prefix,name_prefix,middleware)
    def use(self,middleware:Middleware)->None:self.middleware.append(middleware)
    def before_request(self,hook): self.before_hooks.append(hook); return hook
    def after_request(self,hook): self.after_hooks.append(hook); return hook
    def error(self,status:int):
        def deco(handler:ErrorHandler):self.error_handlers[status]=handler;return handler
        return deco
    def url_for(self,name: str,**params:Any)->str:
        route=next((r for r in self.routes if r.name==name),None)
        if not route: raise KeyError(f"unknown route: {name}")
        path=route.path
        for key,value in params.items(): path=re.sub(r"{"+re.escape(key)+r"(?::[A-Za-z]+)?}",quote(str(value),safe=""),path)
        if re.search(r"{[^}]+}",path): raise ValueError("missing route parameters")
        return path
    def _error_response(self,request:WebRequest,status:int,exc:Exception|None=None)->WebResponse:
        if status in self.error_handlers:return self.error_handlers[status](request,exc)
        message=str(exc) if self.debug and exc else HTTPStatus(status).phrase
        return WebResponse.text(message,status,"text/plain; charset=utf-8")
    def dispatch(self,request:WebRequest)->WebResponse:
        def endpoint(current:WebRequest)->WebResponse:
            path_matches=[]
            for route in self.routes:
                params=route.match(current.path)
                if params is not None:
                    path_matches.append(route)
                    method=current.method.upper()
                    if route.method==method or (method=="HEAD" and route.method=="GET"):
                        routed=replace(current,params=params)
                        for hook in self.before_hooks: hook(routed)
                        response=route.handler(routed)
                        for hook in reversed(self.after_hooks): response=hook(routed,response)
                        return response
            if path_matches:
                response=self._error_response(current,405)
                methods={r.method for r in path_matches}
                if "GET" in methods: methods.add("HEAD")
                return response.with_header("Allow",", ".join(sorted(methods)))
            return self._error_response(current,404)
        next_handler=endpoint
        for layer in reversed(self.middleware):
            following=next_handler; next_handler=lambda current,layer=layer,following=following:layer(current,following)
        try:return next_handler(request)
        except HTTPError as exc:return self._error_response(request,exc.status,exc)
        except Exception as exc:return self._error_response(request,500,exc)

class StaticFiles:
    def __init__(self,root: str|Path,*,cache_seconds:int=3600): self.root=Path(root).resolve(); self.cache_seconds=cache_seconds
    def __call__(self,request:WebRequest)->WebResponse:
        relative=str(request.params.get("path","")); candidate=(self.root/relative).resolve()
        if self.root!=candidate and self.root not in candidate.parents:return WebResponse.text("Not Found",404,"text/plain; charset=utf-8")
        if not candidate.is_file():return WebResponse.text("Not Found",404,"text/plain; charset=utf-8")
        data=candidate.read_bytes(); content_type=mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        etag='"'+hashlib.sha256(data).hexdigest()+'"'
        if request.header("if-none-match")==etag:return WebResponse(b"",304,{"ETag":etag})
        return WebResponse(data,200,{"Content-Type":content_type,"Content-Length":str(len(data)),"Cache-Control":f"public, max-age={self.cache_seconds}","ETag":etag,"X-Content-Type-Options":"nosniff"})

class SessionCodec:
    def __init__(self,secret: str|bytes,*,ttl:int=3600):
        self.secret=secret.encode() if isinstance(secret,str) else secret; self.ttl=ttl
        if len(self.secret)<16: raise ValueError("session secret must be at least 16 bytes")
        if ttl <= 0: raise ValueError("session lifetime must be positive")
    def encode(self,data:Mapping[str,Any])->str:
        payload=json.dumps({"exp":int(time.time())+self.ttl,"data":dict(data)},separators=(",",":"),sort_keys=True).encode()
        sig=hmac.new(self.secret,payload,hashlib.sha256).digest()
        return base64.urlsafe_b64encode(payload+sig).decode().rstrip("=")
    def decode(self,token:str)->dict[str,Any]:
        try:
            if not token or len(token) > 16_384: return {}
            raw=base64.urlsafe_b64decode(token+"="*(-len(token)%4)); payload,sig=raw[:-32],raw[-32:]
            if len(raw) < 33: return {}
            if not hmac.compare_digest(sig,hmac.new(self.secret,payload,hashlib.sha256).digest()):return {}
            value=json.loads(payload)
            expires=value.get("exp"); data=value.get("data")
            if not isinstance(expires,int) or not isinstance(data,dict): return {}
            return dict(data) if int(time.time())<expires else {}
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):return {}

class SessionMiddleware:
    def __init__(self,secret:str|bytes,*,cookie_name="oriel_session",ttl=3600,secure=True): self.codec=SessionCodec(secret,ttl=ttl); self.cookie_name=cookie_name; self.ttl=ttl; self.secure=secure
    def __call__(self,request:WebRequest,next_handler:Handler)->WebResponse:
        session=self.codec.decode(request.cookies.get(self.cookie_name,"")); enriched=replace(request,context={**request.context,"session":session})
        response=next_handler(enriched)
        return response.set_cookie(self.cookie_name,self.codec.encode(session),max_age=self.ttl,secure=self.secure)

class CSRFMiddleware:
    SAFE={"GET","HEAD","OPTIONS","TRACE"}
    def __init__(self,*,field_name="_csrf",header_name="x-csrf-token"): self.field_name=field_name; self.header_name=header_name
    def __call__(self,request:WebRequest,next_handler:Handler)->WebResponse:
        session=request.context.get("session")
        if session is None: raise RuntimeError("CSRF middleware requires SessionMiddleware before it")
        token=session.setdefault("_csrf",secrets.token_urlsafe(32))
        enriched=replace(request,context={**request.context,"csrf_token":token})
        if request.method.upper() not in self.SAFE:
            supplied=request.header(self.header_name) or (request.form().get(self.field_name,[""])[0])
            if not hmac.compare_digest(token,supplied): raise Forbidden("CSRF validation failed")
        return next_handler(enriched)

def security_headers(request:WebRequest,next_handler:Handler)->WebResponse:
    response=next_handler(request); headers={**response.headers}
    headers.setdefault("X-Content-Type-Options","nosniff"); headers.setdefault("X-Frame-Options","DENY")
    headers.setdefault("Referrer-Policy","strict-origin-when-cross-origin"); headers.setdefault("Content-Security-Policy","default-src 'self'; object-src 'none'; base-uri 'self'")
    return replace(response,headers=headers)

def parse_form(request:WebRequest,schema:Mapping[str,Callable[[str],Any]|type]=())->tuple[dict[str,Any],dict[str,str]]:
    raw=request.form(); values={}; errors={}
    for name,converter in schema.items():
        value=raw.get(name,[""])[0]
        try:
            if not value: raise ValueError("required")
            values[name]=converter(value)
        except Exception as exc: errors[name]=str(exc)
    return values,errors

class WebTestClient:
    def __init__(self,app:WebApplication): self.app=app; self.cookies:dict[str,str]={}
    def request(self,method:str,target:str,*,headers:dict[str,str]|None=None,body:bytes=b"",form:Mapping[str,Any]|None=None,json_body:Any=None,follow_redirects:bool=False)->WebResponse:
        parsed=urlparse(target); hdrs=dict(headers or {})
        if self.cookies: hdrs.setdefault("Cookie","; ".join(f"{k}={v}" for k,v in self.cookies.items()))
        if form is not None: body=urlencode(form).encode(); hdrs.setdefault("Content-Type","application/x-www-form-urlencoded")
        if json_body is not None: body=json.dumps(json_body).encode(); hdrs.setdefault("Content-Type","application/json")
        response=self.app.dispatch(WebRequest(method.upper(),parsed.path,parse_qs(parsed.query,keep_blank_values=True),hdrs,body=body))
        for line in response.headers.get("Set-Cookie","").splitlines():
            cookie=SimpleCookie(); cookie.load(line)
            for name,morsel in cookie.items(): self.cookies[name]=morsel.value
        if follow_redirects and response.status in {301,302,303,307,308}:
            return self.request("GET" if response.status in {301,302,303} else method,response.headers["Location"],headers=headers,follow_redirects=False)
        return response
    def get(self,target:str,**kwargs)->WebResponse:return self.request("GET",target,**kwargs)
    def post(self,target:str,**kwargs)->WebResponse:return self.request("POST",target,**kwargs)
    def put(self,target:str,**kwargs)->WebResponse:return self.request("PUT",target,**kwargs)
    def delete(self,target:str,**kwargs)->WebResponse:return self.request("DELETE",target,**kwargs)

def create_web_project(name:str,base:Path)->Path:
    root=base/name
    if root.exists(): raise FileExistsError(f"Project already exists: {root}")
    for folder in (root/"src",root/"templates",root/"static",root/"tests"): folder.mkdir(parents=True,exist_ok=True)
    (root/"src"/"app.py").write_text('''from pathlib import Path\nfrom oriel.web_framework import TemplateEngine, WebApplication, WebResponse, security_headers\n\napp = WebApplication(debug=True)\napp.use(security_headers)\ntemplates = TemplateEngine(Path(__file__).parents[1] / "templates")\n\n@app.get("/", name="home")\ndef home(request):\n    return WebResponse.html(templates.render("index.html", {"title": "ORIEL Web"}))\n''',encoding="utf-8")
    (root/"templates"/"index.html").write_text("<!doctype html><title>{{ title }}</title><h1>{{ title }}</h1>",encoding="utf-8")
    (root/"static"/"app.css").write_text("body { font-family: system-ui; max-width: 60rem; margin: 3rem auto; }\n",encoding="utf-8")
    (root/"oriel.toml").write_text(f'[project]\nname = "{name}"\nversion = "0.1.0"\nprofile = "web"\n\n[dependencies]\n"oriel.core" = "0.9.4"\n"oriel.web" = "0.9.4"\n',encoding="utf-8")
    (root/"README.md").write_text(f"# {name}\n\nRun: `oriel web serve src/app.py`\n",encoding="utf-8")
    return root

def load_application(path: str|Path)->WebApplication:
    source=Path(path).resolve()
    if not source.is_file() or source.suffix!=".py":
        raise ValueError("web application must be an existing Python file")
    spec=importlib.util.spec_from_file_location(f"_oriel_web_{hashlib.sha256(str(source).encode()).hexdigest()[:12]}",source)
    if spec is None or spec.loader is None: raise ValueError(f"cannot load web application: {source}")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app=getattr(module,"app",None)
    if not isinstance(app,WebApplication): raise ValueError("web application file must define 'app = WebApplication()'")
    return app

def serve(app:WebApplication,host="127.0.0.1",port=8080)->None:
    if not 0 <= port <= 65535: raise ValueError("port must be between 0 and 65535")
    class Handler(BaseHTTPRequestHandler):
        def _handle(self):
            parsed=urlparse(self.path); length=int(self.headers.get("Content-Length","0")); body=self.rfile.read(length) if length else b""
            response=app.dispatch(WebRequest(self.command,parsed.path,parse_qs(parsed.query,keep_blank_values=True),dict(self.headers.items()),body=body))
            self.send_response(response.status)
            for name,value in response.headers.items():
                for item in value.splitlines(): self.send_header(name,item)
            if "Content-Length" not in response.headers:self.send_header("Content-Length",str(len(response.body)))
            self.end_headers()
            if self.command!="HEAD":self.wfile.write(response.body)
        do_GET=_handle; do_POST=_handle; do_PUT=_handle; do_DELETE=_handle; do_PATCH=_handle; do_HEAD=_handle
        def log_message(self,fmt,*args): print("[oriel.web]",fmt%args)
    print(f"ORIEL Web running at http://{host}:{port}")
    ThreadingHTTPServer((host,port),Handler).serve_forever()
