from oriel.compiler import Compiler, ModuleIR, optimize
from oriel.vm import VirtualMachine

def run(source):
    out=[];m=Compiler('test.orl').compile_source(source);VirtualMachine(out.append).run(m);return out,m

def test_vm_executes_function_and_main():
    out,m=run('fn add(a: Int, b: Int) -> Int { return a + b }\nfn main() { print(add(2, 3)) }')
    assert out==['5']
    assert 'main' in m.functions

def test_ir_round_trip():
    _,m=run('fn main() { print("ok") }')
    restored=ModuleIR.from_dict(m.to_dict());out=[];VirtualMachine(out.append).run(restored)
    assert out==['ok']

def test_optimization_preserves_output():
    source='fn main() { 10\n print("same") }'
    m=Compiler('x.orl').compile_source(source);a=[];b=[]
    VirtualMachine(a.append).run(m);VirtualMachine(b.append).run(optimize(m))
    assert a==b==['same']
