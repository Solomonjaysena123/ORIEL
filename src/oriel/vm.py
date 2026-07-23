from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from .compiler import ModuleIR, Instruction, Op

@dataclass
class Binding:
    value: Any
    mutable: bool=True
@dataclass
class FunctionValue:
    name: str

class VirtualMachine:
    def __init__(self, output: Callable[[str],None]|None=None, trace_hook=None):
        self.output=output or print; self.trace_hook=trace_hook; self.globals={}; self.stack=[]; self.steps=0
        self.natives={"len":len,"range":lambda a,b:list(range(int(a),int(b))),"push":self._push,"type_of":lambda x:type(x).__name__}
    def run(self,module: ModuleIR):
        self.module=module
        for n in module.functions:self.globals[n]=Binding(FunctionValue(n),False)
        return self._execute(module.code,{})
    def _execute(self,code,locals_):
        ip=0; iterators=[]
        while ip<len(code):
            ins=code[ip]; self.steps+=1
            if self.trace_hook:self.trace_hook(self,ins,ip,locals_)
            op=ins.op
            if op==Op.CONST:self.stack.append(self.module.constants[ins.arg])
            elif op==Op.LOAD:
                if ins.arg in locals_:self.stack.append(locals_[ins.arg].value)
                elif ins.arg in self.globals:self.stack.append(self.globals[ins.arg].value)
                elif ins.arg in self.natives:self.stack.append(self.natives[ins.arg])
                else:raise RuntimeError(f"Undefined symbol '{ins.arg}' at line {ins.line}")
            elif op==Op.DEFINE:
                locals_[ins.arg['name']]=Binding(self.stack.pop(),ins.arg['mutable'])
                if locals_ is not self.globals and ins.arg['name'] not in self.globals: pass
            elif op==Op.STORE:
                b=locals_.get(ins.arg) or self.globals.get(ins.arg)
                if not b:raise RuntimeError(f"Undefined symbol '{ins.arg}'")
                if not b.mutable:raise RuntimeError(f"Cannot assign immutable '{ins.arg}'")
                b.value=self.stack[-1]
            elif op==Op.POP:self.stack.pop()
            elif op==Op.PRINT:self.output(self._string(self.stack.pop()))
            elif op in (Op.NEG,Op.NOT): self.stack.append(-self.stack.pop() if op==Op.NEG else not bool(self.stack.pop()))
            elif op in (Op.ADD,Op.SUB,Op.MUL,Op.DIV,Op.MOD,Op.EQ,Op.NE,Op.GT,Op.GE,Op.LT,Op.LE):
                b=self.stack.pop();a=self.stack.pop();self.stack.append(self._binary(op,a,b))
            elif op==Op.JUMP:ip=ins.arg;continue
            elif op==Op.JUMP_IF_FALSE:
                if not bool(self.stack.pop()):ip=ins.arg;continue
            elif op==Op.FUNCTION:self.globals[ins.arg]=Binding(FunctionValue(ins.arg),False)
            elif op==Op.CALL:
                argc=ins.arg;args=self.stack[-argc:] if argc else []; 
                if argc:del self.stack[-argc:]
                callee=self.stack.pop()
                if isinstance(callee,FunctionValue):
                    f=self.module.functions[callee.name]
                    if len(args)!=len(f.params):raise RuntimeError(f"Expected {len(f.params)} arguments")
                    value=self._execute(f.code,{p:Binding(v,True) for p,v in zip(f.params,args)})
                elif callable(callee):value=callee(*args)
                else:raise RuntimeError("Can only call functions")
                self.stack.append(value)
            elif op==Op.RETURN:return self.stack.pop() if self.stack else None
            elif op==Op.MAKE_LIST:
                n=ins.arg;items=self.stack[-n:] if n else []
                if n:del self.stack[-n:]
                self.stack.append(items)
            elif op==Op.INDEX:
                idx=self.stack.pop();target=self.stack.pop();self.stack.append(target[idx])
            elif op==Op.ITER:iterators.append(iter(self.stack.pop()))
            elif op==Op.ITER_NEXT:
                try:locals_[ins.arg['name']]=Binding(next(iterators[-1]),False)
                except StopIteration:iterators.pop();ip=ins.arg['target'];continue
            elif op==Op.HALT:return self.stack.pop() if self.stack else None
            ip+=1
        return None
    @staticmethod
    def _push(a,b):a.append(b);return a
    @staticmethod
    def _string(v):
        if v is None:return 'none'
        if v is True:return 'true'
        if v is False:return 'false'
        return str(v)
    @staticmethod
    def _binary(op,a,b):
        if op==Op.ADD:return a+b if not(isinstance(a,str) or isinstance(b,str)) else str(a)+str(b)
        if op==Op.SUB:return a-b
        if op==Op.MUL:return a*b
        if op==Op.DIV:return a/b
        if op==Op.MOD:return a%b
        return {Op.EQ:a==b,Op.NE:a!=b,Op.GT:a>b,Op.GE:a>=b,Op.LT:a<b,Op.LE:a<=b}[op]
