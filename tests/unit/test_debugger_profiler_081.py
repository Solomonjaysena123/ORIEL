from oriel.compiler import Compiler
from oriel.debugger import Debugger
from oriel.profiler import profile

def test_debugger_breakpoint_and_profile():
    m=Compiler('debug.orl').compile_source('fn main() {\n let value = 3\n print(value)\n}')
    result,events=Debugger({2}).run(m,output=lambda _:None)
    assert events and events[0].line==2
    p=profile(m,2)
    assert p.instructions>0 and p.elapsed_ms>=0
