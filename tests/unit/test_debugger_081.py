from oriel.vm import Compiler
from oriel.debugger import Debugger, Profiler

def test_breakpoint_event():
    p=Compiler().compile_source('let x = 1\nprint(x)')
    d=Debugger(p); d.add_breakpoint(2)
    assert any(e.kind=='breakpoint' and e.line==2 for e in d.trace())

def test_profiler_report():
    p=Compiler().compile_source('print(1 + 2)')
    r=Profiler().profile(p,5)
    assert r.iterations==5 and r.instruction_counts['ADD']==1 and r.average_seconds>=0
