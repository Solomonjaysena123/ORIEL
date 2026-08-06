from oriel.vm import *

def test_compile_and_execute():
    output=[]; p=Compiler().compile_source('fn main() {\n let x = 10 + 2 * 3\n print(x)\n}')
    vm=VirtualMachine(output.append); vm.run(p)
    assert output==[16]

def test_serialization_roundtrip():
    p=Compiler().compile_source('print(4 + 5)')
    q=Program.from_json(p.to_json())
    assert disassemble(p)==disassemble(q)

def test_division_by_zero():
    import pytest
    with pytest.raises(VMError): VirtualMachine(lambda x:None).run(Compiler().compile_source('print(1 / 0)'))

def test_bytecode_has_halt():
    assert Compiler().compile_source('print(1)').instructions[-1].op==Op.HALT
