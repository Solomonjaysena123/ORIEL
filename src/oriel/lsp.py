from __future__ import annotations
import json, re, sys
from .compiler_services import CompilerService

KEYWORDS=["fn","let","var","return","if","else","while","for","in","true","false","none","print","use","api","get","post","put","delete","patch"]
BUILTINS=["len","range","push","read_file","write_file","json_encode","json_decode","type_of"]
IDENT=re.compile(r'[A-Za-z_]\w*')
DECL=re.compile(r'\b(?:fn|let|var)\s+([A-Za-z_]\w*)')

def _send(payload):
 raw=json.dumps(payload).encode(); sys.stdout.buffer.write(f'Content-Length: {len(raw)}\r\n\r\n'.encode()+raw); sys.stdout.buffer.flush()
def _read():
 length=None
 while True:
  line=sys.stdin.buffer.readline()
  if not line:return None
  if line in (b'\r\n',b'\n'):break
  if line.lower().startswith(b'content-length:'):length=int(line.split(b':',1)[1])
 return json.loads(sys.stdin.buffer.read(length)) if length else None
def diagnostics(text):
 # API DSL is validated separately from the core parser.
 if re.search(r'\bapi\s+\w+\s*\{', text):
  return []
 return [item.to_lsp() for item in CompilerService().analyze(text).diagnostics]
def word_at(text,line,char):
 lines=text.splitlines(); row=lines[line] if line<len(lines) else ''
 for m in IDENT.finditer(row):
  if m.start()<=char<=m.end(): return m.group(),m.start(),m.end()
 return '',char,char+1
def declaration(text,name):
 for i,row in enumerate(text.splitlines()):
  m=re.search(rf'\b(?:fn|let|var)\s+({re.escape(name)})\b',row)
  if m:return {"line":i,"start":m.start(1),"end":m.end(1)}
 return None
def locations(uri,text,name):
 out=[]
 for i,row in enumerate(text.splitlines()):
  for m in re.finditer(rf'\b{re.escape(name)}\b',row):out.append({"uri":uri,"range":{"start":{"line":i,"character":m.start()},"end":{"line":i,"character":m.end()}}})
 return out

def run_lsp():
 docs={}
 while True:
  msg=_read()
  if msg is None:return 0
  method=msg.get('method'); p=msg.get('params',{}); mid=msg.get('id')
  if method=='initialize':
   caps={"textDocumentSync":1,"completionProvider":{"triggerCharacters":["."]},"hoverProvider":True,"definitionProvider":True,"referencesProvider":True,"renameProvider":True,"documentSymbolProvider":True}
   _send({"jsonrpc":"2.0","id":mid,"result":{"capabilities":caps}})
  elif method=='shutdown':_send({"jsonrpc":"2.0","id":mid,"result":None})
  elif method=='exit':return 0
  elif method in ('textDocument/didOpen','textDocument/didChange'):
   if method.endswith('didOpen'): item=p['textDocument']; uri=item['uri']; text=item['text']
   else: uri=p['textDocument']['uri']; text=p['contentChanges'][-1]['text']
   docs[uri]=text; _send({"jsonrpc":"2.0","method":"textDocument/publishDiagnostics","params":{"uri":uri,"diagnostics":diagnostics(text)}})
  elif method=='textDocument/completion':
   uri=p['textDocument']['uri']; text=docs.get(uri,''); symbols=sorted(set(DECL.findall(text)))
   items=[{"label":x,"kind":14,"detail":"ORIEL keyword"} for x in KEYWORDS]+[{"label":x,"kind":3,"detail":"ORIEL built-in"} for x in BUILTINS]+[{"label":x,"kind":6,"detail":"Project symbol"} for x in symbols]
   _send({"jsonrpc":"2.0","id":mid,"result":{"isIncomplete":False,"items":items}})
  elif method in ('textDocument/hover','textDocument/definition','textDocument/references','textDocument/rename'):
   uri=p['textDocument']['uri']; text=docs.get(uri,''); pos=p['position']; name,_,_=word_at(text,pos['line'],pos['character']); decl=declaration(text,name)
   if method.endswith('hover'):
    value=f'**{name}** — ORIEL symbol' if name else '**ORIEL 0.7.1**'
    _send({"jsonrpc":"2.0","id":mid,"result":{"contents":{"kind":"markdown","value":value}}})
   elif method.endswith('definition'):
    result=None if not decl else {"uri":uri,"range":{"start":{"line":decl['line'],"character":decl['start']},"end":{"line":decl['line'],"character":decl['end']}}}
    _send({"jsonrpc":"2.0","id":mid,"result":result})
   elif method.endswith('references'):_send({"jsonrpc":"2.0","id":mid,"result":locations(uri,text,name)})
   else:
    edits=[{"range":x['range'],"newText":p['newName']} for x in locations(uri,text,name)]
    _send({"jsonrpc":"2.0","id":mid,"result":{"changes":{uri:edits}}})
  elif method=='textDocument/documentSymbol':
   uri=p['textDocument']['uri']; text=docs.get(uri,''); result=[]
   for i,row in enumerate(text.splitlines()):
    m=re.search(r'\b(fn|let|var)\s+([A-Za-z_]\w*)',row)
    if m: result.append({"name":m.group(2),"kind":12 if m.group(1)=='fn' else 13,"range":{"start":{"line":i,"character":m.start()},"end":{"line":i,"character":len(row)}},"selectionRange":{"start":{"line":i,"character":m.start(2)},"end":{"line":i,"character":m.end(2)}}})
   _send({"jsonrpc":"2.0","id":mid,"result":result})
  elif mid is not None:_send({"jsonrpc":"2.0","id":mid,"result":None})
