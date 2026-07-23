from __future__ import annotations
from pathlib import Path
from time import perf_counter
import json, platform, shutil, sys
from .interpreter import run_source
from .compiler import Compiler, ModuleIR, optimize
from .vm import VirtualMachine

BYTECODE_MAGIC='ORIELBC2'
def compile_bytecode(source,filename='<source>',optimized=False):
    module=Compiler(filename).compile_source(source)
    if optimized:module=optimize(module)
    return {'magic':BYTECODE_MAGIC,'module':module.to_dict()}
def write_bytecode(source_path:Path,output=None,optimized=False):
    output=output or source_path.with_suffix('.obc');payload=compile_bytecode(source_path.read_text(encoding='utf-8'),str(source_path),optimized);output.write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8');return output
def load_bytecode(path:Path):
    payload=json.loads(path.read_text(encoding='utf-8'))
    if payload.get('magic')!=BYTECODE_MAGIC:raise ValueError('Invalid or unsupported ORIEL bytecode file.')
    return ModuleIR.from_dict(payload['module'])
def run_bytecode(path:Path,output=None):return VirtualMachine(output=output).run(load_bytecode(path))
def generate_docs(source_path:Path,output:Path):
    import re
    source=source_path.read_text(encoding='utf-8');functions=re.findall(r'fn\s+([A-Za-z_]\w*)\s*\(([^)]*)\)(?:\s*->\s*([A-Za-z_]\w*))?',source);lines=[f'# API documentation: {source_path.name}','']
    for name,params,ret in functions:lines += [f'## `{name}({params})`',f'**Returns:** `{ret or "Any"}`','']
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text('\n'.join(lines),encoding='utf-8');return output
def doctor():return {'oriel':'ok','python':sys.version.split()[0],'platform':platform.platform(),'cwd':str(Path.cwd()),'vscode_cli':bool(shutil.which('code')),'write_access':_write_access(Path.cwd())}
def _write_access(path):
    try:probe=path/'.oriel_write_test';probe.write_text('ok');probe.unlink();return True
    except Exception:return False
def benchmark(source_path:Path,iterations=10,engine='vm'):
    source=source_path.read_text(encoding='utf-8');module=Compiler(str(source_path)).compile_source(source);times=[]
    for _ in range(iterations):
        start=perf_counter();VirtualMachine(output=lambda _:None).run(module) if engine=='vm' else run_source(source,str(source_path),output=lambda _:None);times.append((perf_counter()-start)*1000)
    return {'engine':engine,'iterations':iterations,'min_ms':min(times),'max_ms':max(times),'average_ms':sum(times)/len(times)}
def repl():
    print('ORIEL 0.8.1 REPL. Enter :quit to exit.');buffer=[]
    while True:
        try:line=input('oriel> ' if not buffer else '... ')
        except EOFError:break
        if line.strip()==':quit':break
        buffer.append(line);source='\n'.join(buffer)
        if source.count('{')>source.count('}'):continue
        try:run_source(source,'<repl>')
        except Exception as error:print(error)
        buffer=[]
