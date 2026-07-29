"""ORIEL 0.8.0 stack bytecode compiler and virtual machine.

The first VM milestone compiles literals, variables, arithmetic and print
statements from a compact ORIEL subset into a versioned instruction stream.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
import ast as pyast, json

BYTECODE_VERSION=1
class Op(str,Enum):
    CONST='CONST'; LOAD='LOAD'; STORE='STORE'; ADD='ADD'; SUB='SUB'; MUL='MUL'; DIV='DIV'; MOD='MOD'; NEG='NEG'; PRINT='PRINT'; POP='POP'; HALT='HALT'
@dataclass(frozen=True)
class Instruction:
    op:Op; arg:object=None; line:int=0
@dataclass
class Program:
    instructions:list[Instruction]; version:int=BYTECODE_VERSION
    def to_json(self): return json.dumps({'version':self.version,'instructions':[{'op':i.op.value,'arg':i.arg,'line':i.line} for i in self.instructions]},indent=2)
    @classmethod
    def from_json(cls,text):
        d=json.loads(text)
        if d['version']!=BYTECODE_VERSION: raise ValueError('Unsupported bytecode version')
        return cls([Instruction(Op(i['op']),i.get('arg'),i.get('line',0)) for i in d['instructions']],d['version'])

class CompileError(Exception): pass
class Compiler:
    def compile_source(self,source:str)->Program:
        out=[]
        for line_no,raw in enumerate(source.splitlines(),1):
            line=raw.strip()
            if not line or line.startswith('//') or line in {'fn main() {','}'}: continue
            if line.startswith(('let ','var ')):
                left,sep,right=line.partition('=')
                if not sep: raise CompileError(f'Expected assignment on line {line_no}')
                name=left.split()[1].strip(); self.expr(right.strip(),out,line_no); out.append(Instruction(Op.STORE,name,line_no)); continue
            if line.startswith('print(') and line.endswith(')'):
                self.expr(line[6:-1],out,line_no); out.append(Instruction(Op.PRINT,None,line_no)); continue
            self.expr(line,out,line_no); out.append(Instruction(Op.POP,None,line_no))
        out.append(Instruction(Op.HALT)); return Program(out)
    def expr(self,text,out,line):
        try: node=pyast.parse(text,mode='eval').body
        except SyntaxError as e: raise CompileError(f'Invalid expression on line {line}: {e.msg}')
        self.emit(node,out,line)
    def emit(self,node,out,line):
        if isinstance(node,pyast.Constant): out.append(Instruction(Op.CONST,node.value,line)); return
        if isinstance(node,pyast.Name): out.append(Instruction(Op.LOAD,node.id,line)); return
        if isinstance(node,pyast.UnaryOp) and isinstance(node.op,pyast.USub): self.emit(node.operand,out,line); out.append(Instruction(Op.NEG,None,line)); return
        if isinstance(node,pyast.BinOp):
            self.emit(node.left,out,line); self.emit(node.right,out,line)
            table={pyast.Add:Op.ADD,pyast.Sub:Op.SUB,pyast.Mult:Op.MUL,pyast.Div:Op.DIV,pyast.Mod:Op.MOD}
            op=table.get(type(node.op))
            if not op: raise CompileError('Unsupported binary operator')
            out.append(Instruction(op,None,line)); return
        raise CompileError(f'Unsupported expression: {type(node).__name__}')

class VMError(Exception): pass
class VirtualMachine:
    def __init__(self,output=None): self.stack=[]; self.globals={}; self.output=output or print; self.ip=0
    def run(self,program:Program):
        ins=program.instructions
        while self.ip < len(ins):
            i=ins[self.ip]; self.ip+=1
            if i.op==Op.CONST: self.stack.append(i.arg)
            elif i.op==Op.LOAD:
                if i.arg not in self.globals: raise VMError(f"Undefined variable '{i.arg}' at line {i.line}")
                self.stack.append(self.globals[i.arg])
            elif i.op==Op.STORE: self.globals[str(i.arg)]=self.stack.pop()
            elif i.op==Op.NEG: self.stack.append(-self.stack.pop())
            elif i.op in {Op.ADD,Op.SUB,Op.MUL,Op.DIV,Op.MOD}:
                b=self.stack.pop(); a=self.stack.pop()
                if i.op in {Op.DIV,Op.MOD} and b==0: raise VMError(f'Division by zero at line {i.line}')
                self.stack.append({Op.ADD:lambda:a+b,Op.SUB:lambda:a-b,Op.MUL:lambda:a*b,Op.DIV:lambda:a/b,Op.MOD:lambda:a%b}[i.op]())
            elif i.op==Op.PRINT: self.output(self.stack.pop())
            elif i.op==Op.POP: self.stack.pop()
            elif i.op==Op.HALT: break
        return self.globals

def disassemble(program): return '\n'.join(f'{n:04d} {i.op.value:<8} {"" if i.arg is None else repr(i.arg)}' for n,i in enumerate(program.instructions))
