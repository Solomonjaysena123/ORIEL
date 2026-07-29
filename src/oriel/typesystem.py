"""ORIEL 0.7.2 static type-system foundation.

Provides immutable type representations, generic collections, nullable types,
function signatures, inference helpers and assignability rules.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class TypeRef:
    name: str
    args: tuple["TypeRef", ...] = ()
    nullable: bool = False

    def __str__(self) -> str:
        suffix = "?" if self.nullable else ""
        if self.args:
            return f"{self.name}<" + ", ".join(map(str, self.args)) + f">{suffix}"
        return self.name + suffix

    def non_nullable(self) -> "TypeRef":
        return TypeRef(self.name, self.args, False)

PRIMITIVES = {name: TypeRef(name) for name in (
    "Int", "Float", "Decimal", "Bool", "String", "Char", "None", "Any", "Never"
)}

class TypeSyntaxError(ValueError): pass

class _Parser:
    def __init__(self, text: str): self.text=text; self.i=0
    def ws(self):
        while self.i < len(self.text) and self.text[self.i].isspace(): self.i += 1
    def identifier(self):
        self.ws(); start=self.i
        while self.i < len(self.text) and (self.text[self.i].isalnum() or self.text[self.i]=='_'): self.i += 1
        if start==self.i: raise TypeSyntaxError(f"Expected type name at column {self.i+1}")
        return self.text[start:self.i]
    def type(self):
        name=self.identifier(); args=[]; self.ws()
        if self.i < len(self.text) and self.text[self.i]=='<':
            self.i += 1
            while True:
                args.append(self.type()); self.ws()
                if self.i < len(self.text) and self.text[self.i]==',': self.i += 1; continue
                if self.i < len(self.text) and self.text[self.i]=='>': self.i += 1; break
                raise TypeSyntaxError(f"Expected ',' or '>' at column {self.i+1}")
        self.ws(); nullable=False
        if self.i < len(self.text) and self.text[self.i]=='?': nullable=True; self.i += 1
        return TypeRef(name, tuple(args), nullable)

def parse_type(text: str) -> TypeRef:
    p=_Parser(text); result=p.type(); p.ws()
    if p.i != len(text): raise TypeSyntaxError(f"Unexpected input at column {p.i+1}")
    return result

def infer_literal(value) -> TypeRef:
    if value is None: return PRIMITIVES["None"]
    if isinstance(value, bool): return PRIMITIVES["Bool"]
    if isinstance(value, int): return PRIMITIVES["Int"]
    if isinstance(value, float): return PRIMITIVES["Float"]
    if isinstance(value, str): return PRIMITIVES["String"]
    if isinstance(value, list):
        if not value: return TypeRef("List", (PRIMITIVES["Any"],))
        item=common_type(infer_literal(v) for v in value)
        return TypeRef("List", (item,))
    if isinstance(value, dict):
        if not value: return TypeRef("Map", (PRIMITIVES["Any"], PRIMITIVES["Any"]))
        return TypeRef("Map", (common_type(infer_literal(k) for k in value), common_type(infer_literal(v) for v in value.values())))
    return PRIMITIVES["Any"]

def is_assignable(source: TypeRef, target: TypeRef) -> bool:
    if target.name == "Any" or source.name == "Never": return True
    if source.name == "None": return target.nullable or target.name in {"None", "Any"}
    if source.nullable and not target.nullable: return False
    if source.name == "Int" and target.name in {"Float", "Decimal"}: return True
    if source.name != target.name or len(source.args) != len(target.args): return False
    return all(is_assignable(s, t) for s,t in zip(source.args,target.args))

def common_type(types: Iterable[TypeRef]) -> TypeRef:
    items=list(types)
    if not items: return PRIMITIVES["Any"]
    result=items[0]
    for item in items[1:]:
        if item == result: continue
        if {item.name,result.name} <= {"Int","Float"}: result=PRIMITIVES["Float"]
        elif item.name == "None": result=TypeRef(result.name,result.args,True)
        elif result.name == "None": result=TypeRef(item.name,item.args,True)
        else: result=PRIMITIVES["Any"]
    return result

@dataclass(frozen=True)
class FunctionType:
    parameters: tuple[TypeRef, ...]
    returns: TypeRef
    def accepts(self, arguments: Iterable[TypeRef]) -> bool:
        args=tuple(arguments)
        return len(args)==len(self.parameters) and all(is_assignable(a,p) for a,p in zip(args,self.parameters))
