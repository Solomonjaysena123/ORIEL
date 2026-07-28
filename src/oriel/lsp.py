from __future__ import annotations
import json, sys
from .interpreter import Lexer, Parser, TypeChecker, OrielError

KEYWORDS = ["fn","let","var","return","if","else","while","for","in","true","false","none","print"]
BUILTINS = ["len","range","push","read_file","write_file","json_encode","json_decode","type_of"]

def _send(payload):
    raw=json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(raw)}\r\n\r\n".encode()+raw); sys.stdout.buffer.flush()

def _read():
    length=None
    while True:
        line=sys.stdin.buffer.readline()
        if not line: return None
        if line in (b"\r\n",b"\n"): break
        if line.lower().startswith(b"content-length:"): length=int(line.split(b":",1)[1])
    return json.loads(sys.stdin.buffer.read(length)) if length else None

def diagnostics(text):
    try:
        statements=Parser(Lexer(text).scan_tokens()).parse(); TypeChecker().check(statements); return []
    except OrielError as e:
        return [{"range":{"start":{"line":max(0,e.line-1),"character":max(0,e.column-1)},"end":{"line":max(0,e.line-1),"character":max(1,e.column)}},"severity":1,"code":e.code,"source":"oriel","message":e.message}]
    except Exception as e:
        return [{"range":{"start":{"line":0,"character":0},"end":{"line":0,"character":1}},"severity":1,"source":"oriel","message":str(e)}]

def run_lsp():
    docs={}
    while True:
        msg=_read()
        if msg is None: return 0
        method=msg.get("method"); params=msg.get("params",{}); mid=msg.get("id")
        if method=="initialize":
            _send({"jsonrpc":"2.0","id":mid,"result":{"capabilities":{"textDocumentSync":1,"completionProvider":{"triggerCharacters":["."]},"hoverProvider":True}}})
        elif method=="initialized": pass
        elif method=="shutdown": _send({"jsonrpc":"2.0","id":mid,"result":None})
        elif method=="exit": return 0
        elif method=="textDocument/didOpen":
            item=params["textDocument"]; docs[item["uri"]]=item["text"]
            _send({"jsonrpc":"2.0","method":"textDocument/publishDiagnostics","params":{"uri":item["uri"],"diagnostics":diagnostics(item["text"])}})
        elif method=="textDocument/didChange":
            uri=params["textDocument"]["uri"]; text=params["contentChanges"][-1]["text"]; docs[uri]=text
            _send({"jsonrpc":"2.0","method":"textDocument/publishDiagnostics","params":{"uri":uri,"diagnostics":diagnostics(text)}})
        elif method=="textDocument/completion":
            items=[{"label":x,"kind":14 if x in KEYWORDS else 3,"detail":"Oriel keyword" if x in KEYWORDS else "Oriel built-in"} for x in KEYWORDS+BUILTINS]
            _send({"jsonrpc":"2.0","id":mid,"result":{"isIncomplete":False,"items":items}})
        elif method=="textDocument/hover":
            _send({"jsonrpc":"2.0","id":mid,"result":{"contents":{"kind":"markdown","value":"**ORIEL 0.3** language symbol"}}})
        elif mid is not None: _send({"jsonrpc":"2.0","id":mid,"result":None})
