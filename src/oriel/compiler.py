from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Any
from .interpreter import (
    Lexer, Parser, TypeChecker, Stmt, Expr, Literal, Variable, Assign, Unary,
    Binary, Grouping, Call, ListLiteral, IndexExpr, ExpressionStmt, PrintStmt,
    VarStmt, BlockStmt, IfStmt, WhileStmt, ForStmt, FunctionStmt, ReturnStmt,
    TokenType,
)

class Op(Enum):
    CONST=auto(); LOAD=auto(); DEFINE=auto(); STORE=auto(); POP=auto(); PRINT=auto()
    NEG=auto(); NOT=auto(); ADD=auto(); SUB=auto(); MUL=auto(); DIV=auto(); MOD=auto()
    EQ=auto(); NE=auto(); GT=auto(); GE=auto(); LT=auto(); LE=auto()
    JUMP=auto(); JUMP_IF_FALSE=auto(); CALL=auto(); RETURN=auto(); MAKE_LIST=auto()
    INDEX=auto(); ITER=auto(); ITER_NEXT=auto(); FUNCTION=auto(); HALT=auto()

@dataclass(frozen=True)
class Instruction:
    op: Op
    arg: Any = None
    line: int = 0

@dataclass
class FunctionIR:
    name: str
    params: list[str]
    code: list[Instruction]

@dataclass
class ModuleIR:
    source_name: str
    constants: list[Any]
    code: list[Instruction]
    functions: dict[str, FunctionIR]
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        def ins(i: Instruction): return {"op": i.op.name, "arg": i.arg, "line": i.line}
        return {"format":"ORIEL-IR","version":self.version,"source_name":self.source_name,
                "constants":self.constants,"code":[ins(i) for i in self.code],
                "functions":{n:{"name":f.name,"params":f.params,"code":[ins(i) for i in f.code]} for n,f in self.functions.items()}}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModuleIR":
        if data.get("format") != "ORIEL-IR": raise ValueError("Invalid ORIEL IR format")
        def ins(x): return Instruction(Op[x["op"]], x.get("arg"), x.get("line",0))
        funcs={n:FunctionIR(v["name"],list(v["params"]),[ins(i) for i in v["code"]]) for n,v in data.get("functions",{}).items()}
        return cls(data.get("source_name","<bytecode>"),list(data.get("constants",[])),[ins(i) for i in data["code"]],funcs,int(data.get("version",1)))

class Compiler:
    def __init__(self, source_name: str = "<source>"):
        self.source_name=source_name; self.constants=[]; self.functions={}; self.code=[]
    def compile_source(self, source: str) -> ModuleIR:
        statements=Parser(Lexer(source).scan_tokens()).parse(); TypeChecker().check(statements)
        for s in statements: self._stmt(s,self.code)
        if "main" in self.functions: self.code += [Instruction(Op.LOAD,"main"),Instruction(Op.CALL,0)]
        self.code.append(Instruction(Op.HALT)); return ModuleIR(self.source_name,self.constants,self.code,self.functions)
    def _const(self,v):
        try:return self.constants.index(v)
        except ValueError:self.constants.append(v);return len(self.constants)-1
    def _emit(self,c,op,arg=None,line=0): c.append(Instruction(op,arg,line)); return len(c)-1
    def _patch(self,c,idx,target): c[idx]=Instruction(c[idx].op,target,c[idx].line)
    def _stmt(self,s,c):
        if isinstance(s,ExpressionStmt): self._expr(s.expression,c);self._emit(c,Op.POP)
        elif isinstance(s,PrintStmt): self._expr(s.expression,c);self._emit(c,Op.PRINT)
        elif isinstance(s,VarStmt): self._expr(s.initializer,c);self._emit(c,Op.DEFINE,{"name":s.name.lexeme,"mutable":s.mutable},s.name.line)
        elif isinstance(s,BlockStmt):
            for x in s.statements:self._stmt(x,c)
        elif isinstance(s,IfStmt):
            self._expr(s.condition,c); jf=self._emit(c,Op.JUMP_IF_FALSE,None)
            self._stmt(s.then_branch,c); jend=self._emit(c,Op.JUMP,None)
            self._patch(c,jf,len(c));
            if s.else_branch:self._stmt(s.else_branch,c)
            self._patch(c,jend,len(c))
        elif isinstance(s,WhileStmt):
            start=len(c);self._expr(s.condition,c);jf=self._emit(c,Op.JUMP_IF_FALSE,None);self._stmt(s.body,c);self._emit(c,Op.JUMP,start);self._patch(c,jf,len(c))
        elif isinstance(s,ForStmt):
            self._expr(s.iterable,c);self._emit(c,Op.ITER);start=len(c);nxt=self._emit(c,Op.ITER_NEXT,{"name":s.name.lexeme,"target":None},s.name.line);self._stmt(s.body,c);self._emit(c,Op.JUMP,start);arg=dict(c[nxt].arg);arg["target"]=len(c);c[nxt]=Instruction(Op.ITER_NEXT,arg,c[nxt].line)
        elif isinstance(s,FunctionStmt):
            fc=[]
            for x in s.body:self._stmt(x,fc)
            fc += [Instruction(Op.CONST,self._const(None)),Instruction(Op.RETURN)]
            self.functions[s.name.lexeme]=FunctionIR(s.name.lexeme,[p.lexeme for p in s.params],fc);self._emit(c,Op.FUNCTION,s.name.lexeme,s.name.line)
        elif isinstance(s,ReturnStmt):
            if s.value:self._expr(s.value,c)
            else:self._emit(c,Op.CONST,self._const(None))
            self._emit(c,Op.RETURN,line=s.keyword.line)
        else: raise TypeError(type(s).__name__)
    def _expr(self,e,c):
        if isinstance(e,Literal): self._emit(c,Op.CONST,self._const(e.value))
        elif isinstance(e,Variable): self._emit(c,Op.LOAD,e.name.lexeme,e.name.line)
        elif isinstance(e,Assign): self._expr(e.value,c);self._emit(c,Op.STORE,e.name.lexeme,e.name.line)
        elif isinstance(e,Grouping): self._expr(e.expression,c)
        elif isinstance(e,Unary): self._expr(e.right,c);self._emit(c,Op.NEG if e.operator.type==TokenType.MINUS else Op.NOT,line=e.operator.line)
        elif isinstance(e,Binary):
            self._expr(e.left,c);self._expr(e.right,c)
            ops={TokenType.PLUS:Op.ADD,TokenType.MINUS:Op.SUB,TokenType.STAR:Op.MUL,TokenType.SLASH:Op.DIV,TokenType.PERCENT:Op.MOD,TokenType.EQUAL_EQUAL:Op.EQ,TokenType.BANG_EQUAL:Op.NE,TokenType.GREATER:Op.GT,TokenType.GREATER_EQUAL:Op.GE,TokenType.LESS:Op.LT,TokenType.LESS_EQUAL:Op.LE}
            if e.operator.type not in ops: raise NotImplementedError(f"operator {e.operator.lexeme}")
            self._emit(c,ops[e.operator.type],line=e.operator.line)
        elif isinstance(e,Call):
            self._expr(e.callee,c)
            for a in e.arguments:self._expr(a,c)
            self._emit(c,Op.CALL,len(e.arguments),e.paren.line)
        elif isinstance(e,ListLiteral):
            for x in e.items:self._expr(x,c)
            self._emit(c,Op.MAKE_LIST,len(e.items))
        elif isinstance(e,IndexExpr): self._expr(e.target,c);self._expr(e.index,c);self._emit(c,Op.INDEX,line=e.bracket.line)
        else: raise TypeError(type(e).__name__)

def optimize(module: ModuleIR) -> ModuleIR:
    """Safe peephole optimization: remove POP after pure CONST and unreachable code after RETURN."""
    def opt(code):
        out=[]; i=0
        while i<len(code):
            if i+1<len(code) and code[i].op==Op.CONST and code[i+1].op==Op.POP: i+=2; continue
            out.append(code[i])
            if code[i].op==Op.RETURN:
                i+=1
                while i<len(code) and code[i].op not in (Op.FUNCTION,): i+=1
                continue
            i+=1
        return out
    return ModuleIR(module.source_name,list(module.constants),opt(module.code),{n:FunctionIR(f.name,list(f.params),opt(f.code)) for n,f in module.functions.items()},module.version)
