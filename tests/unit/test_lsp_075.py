from oriel.language_server_v2 import LanguageServer, encode_message

def test_initialize_capabilities():
    r=LanguageServer().handle({'jsonrpc':'2.0','id':1,'method':'initialize','params':{}})
    assert r['result']['capabilities']['completionProvider']=={}

def test_document_diagnostics():
    s=LanguageServer(); r=s.handle({'method':'textDocument/didOpen','params':{'textDocument':{'uri':'file:///bad.orl','text':'@','version':1}}})
    assert r['params']['diagnostics'][0]['code']=='E1001'

def test_completion():
    r=LanguageServer().handle({'id':2,'method':'textDocument/completion','params':{}})
    assert any(x['label']=='fn' for x in r['result'])

def test_protocol_frame():
    data=encode_message({'jsonrpc':'2.0','id':1,'result':None})
    assert data.startswith(b'Content-Length:') and b'\r\n\r\n' in data
