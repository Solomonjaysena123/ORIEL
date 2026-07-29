"""ORIEL 0.8.1 bytecode debugger and deterministic profiler."""
from __future__ import annotations
from dataclasses import dataclass, field
from time import perf_counter
from collections import Counter
from .vm import Program, VirtualMachine, Op

@dataclass
class DebugEvent:
    kind:str; ip:int; line:int; op:str; stack:tuple; globals:dict

class Debugger:
    def __init__(self,program:Program): self.program=program; self.breakpoints=set(); self.events=[]
    def add_breakpoint(self,line:int): self.breakpoints.add(line)
    def trace(self):
        stack=[]; globals_={}; events=[]
        for ip,i in enumerate(self.program.instructions):
            if i.line in self.breakpoints: events.append(DebugEvent('breakpoint',ip,i.line,i.op.value,tuple(stack),dict(globals_)))
            events.append(DebugEvent('step',ip,i.line,i.op.value,tuple(stack),dict(globals_)))
            # lightweight state simulation for inspection
            if i.op==Op.CONST: stack.append(i.arg)
            elif i.op==Op.STORE and stack: globals_[str(i.arg)]=stack.pop()
            elif i.op==Op.LOAD and i.arg in globals_: stack.append(globals_[i.arg])
            elif i.op==Op.NEG and stack: stack[-1]=-stack[-1]
            elif i.op==Op.POP and stack: stack.pop()
            elif i.op==Op.PRINT and stack: stack.pop()
            elif i.op==Op.HALT: break
        self.events=events; return events

@dataclass
class ProfileReport:
    iterations:int; elapsed_seconds:float; instruction_counts:dict[str,int]; average_seconds:float

class Profiler:
    def profile(self,program:Program,iterations:int=100)->ProfileReport:
        if iterations<1: raise ValueError('iterations must be positive')
        counts=Counter(i.op.value for i in program.instructions)
        start=perf_counter()
        for _ in range(iterations): VirtualMachine(lambda value:None).run(program)
        elapsed=perf_counter()-start
        return ProfileReport(iterations,elapsed,dict(counts),elapsed/iterations)
