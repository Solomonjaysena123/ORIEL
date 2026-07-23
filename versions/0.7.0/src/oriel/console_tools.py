from __future__ import annotations
from pathlib import Path
from time import perf_counter
import json, platform, shutil, sys
from .interpreter import Lexer, Parser, TypeChecker, run_source

BYTECODE_MAGIC = 'ORIELBC1'

def compile_bytecode(source, filename='<source>'):
    tokens = Lexer(source).scan_tokens()
    statements = Parser(tokens).parse()
    TypeChecker().check(statements)
    return {
        'magic': BYTECODE_MAGIC,
        'source_name': filename,
        'tokens': [{'type': t.type.name, 'lexeme': t.lexeme, 'literal': t.literal, 'line': t.line, 'column': t.column} for t in tokens],
        'source': source,
    }

def write_bytecode(source_path: Path, output=None):
    output = output or source_path.with_suffix('.obc')
    payload = compile_bytecode(source_path.read_text(encoding='utf-8'), str(source_path))
    output.write_text(json.dumps(payload, separators=(',', ':')), encoding='utf-8')
    return output

def run_bytecode(path: Path):
    payload = json.loads(path.read_text(encoding='utf-8'))
    if payload.get('magic') != BYTECODE_MAGIC:
        raise ValueError('Invalid ORIEL bytecode file.')
    return run_source(payload['source'], payload.get('source_name', str(path)))

def generate_docs(source_path: Path, output: Path):
    import re
    source = source_path.read_text(encoding='utf-8')
    functions = re.findall(r'fn\s+([A-Za-z_]\w*)\s*\(([^)]*)\)(?:\s*->\s*([A-Za-z_]\w*))?', source)
    lines = [f'# API documentation: {source_path.name}', '']
    for name, params, ret in functions:
        lines += [f'## `{name}({params})`', f'**Returns:** `{ret or "Any"}`', '']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines), encoding='utf-8')
    return output

def doctor():
    return {
        'oriel': 'ok',
        'python': sys.version.split()[0],
        'platform': platform.platform(),
        'cwd': str(Path.cwd()),
        'vscode_cli': bool(shutil.which('code')),
        'write_access': _write_access(Path.cwd()),
    }

def _write_access(path):
    try:
        probe = path / '.oriel_write_test'
        probe.write_text('ok')
        probe.unlink()
        return True
    except Exception:
        return False

def benchmark(source_path: Path, iterations=10):
    source = source_path.read_text(encoding='utf-8')
    times = []
    for _ in range(iterations):
        start = perf_counter()
        run_source(source, str(source_path))
        times.append((perf_counter() - start) * 1000)
    return {'iterations': iterations, 'min_ms': min(times), 'max_ms': max(times), 'average_ms': sum(times)/len(times)}

def repl():
    print('ORIEL 0.7 REPL. Enter :quit to exit.')
    buffer = []
    while True:
        try:
            line = input('oriel> ' if not buffer else '... ')
        except EOFError:
            break
        if line.strip() == ':quit':
            break
        buffer.append(line)
        source = '\n'.join(buffer)
        if source.count('{') > source.count('}'):
            continue
        try:
            run_source(source, '<repl>')
        except Exception as error:
            print(error)
        buffer = []
