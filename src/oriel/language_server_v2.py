"""ORIEL 0.7.5 dependency-free JSON-RPC language server core."""
from __future__ import annotations
from dataclasses import dataclass
import json
from .interpreter import Lexer, Parser, TypeChecker, OrielError

@dataclass
class Document:
    uri:str; text:str; version:int=0

class Workspace:
    def __init__(self): self.documents={}
    def open(self,uri,text,version=0): self.documents[uri]=Document(uri,text,version)
    def change(self,uri,text,version): self.documents[uri]=Document(uri,text,version)
    def close(self,uri): self.documents.pop(uri,None)
    def diagnostics(self,uri):
        doc=self.documents.get(uri)
        if not doc: return []
        try:
            statements=Parser(Lexer(doc.text).scan_tokens()).parse(); TypeChecker().check(statements); return []
        except OrielError as e:
            return [{'range':{'start':{'line':max(e.line-1,0),'character':max(e.column-1,0)},'end':{'line':max(e.line-1,0),'character':max(e.end_column-1,0)}},'severity':1,'code':e.code,'source':'oriel','message':e.message}]
    def completion(self):
        return [{'label':x,'kind':14} for x in ('fn','let','var','if','else','while','for','return','true','false','none','print')]

class LanguageServer:
    def __init__(self): self.workspace=Workspace(); self.shutdown=False
    def handle(self,msg):
        method=msg.get('method'); params=msg.get('params',{}); mid=msg.get('id')
        if method=='initialize':
            return {'jsonrpc':'2.0','id':mid,'result':{'capabilities':{'textDocumentSync':1,'completionProvider':{},'hoverProvider':True,'documentFormattingProvider':True}}}
        if method=='shutdown': self.shutdown=True; return {'jsonrpc':'2.0','id':mid,'result':None}
        if method=='textDocument/didOpen':
            d=params['textDocument']; self.workspace.open(d['uri'],d['text'],d.get('version',0)); return self.publish(d['uri'])
        if method=='textDocument/didChange':
            d=params['textDocument']; text=params['contentChanges'][-1]['text']; self.workspace.change(d['uri'],text,d.get('version',0)); return self.publish(d['uri'])
        if method=='textDocument/completion': return {'jsonrpc':'2.0','id':mid,'result':self.workspace.completion()}
        if method=='textDocument/hover': return {'jsonrpc':'2.0','id':mid,'result':{'contents':{'kind':'markdown','value':'**ORIEL** language symbol'}}}
        if method=='textDocument/formatting': return {'jsonrpc':'2.0','id':mid,'result':[]}
        return {'jsonrpc':'2.0','id':mid,'result':None} if mid is not None else None
    def publish(self,uri): return {'jsonrpc':'2.0','method':'textDocument/publishDiagnostics','params':{'uri':uri,'diagnostics':self.workspace.diagnostics(uri)}}

def encode_message(payload):
    body=json.dumps(payload,separators=(',',':')).encode(); return f'Content-Length: {len(body)}\r\n\r\n'.encode()+body
