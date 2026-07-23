from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .compiler import ModuleIR, Instruction
from .vm import VirtualMachine

@dataclass
class DebugEvent:
    source: str; line: int; ip: int; operation: str; locals: dict[str,Any]

class Debugger:
    def __init__(self, breakpoints: set[int]|None=None):
        self.breakpoints=set(breakpoints or set());self.events=[];self.paused=False
    def _trace(self,vm:VirtualMachine,ins:Instruction,ip:int,locals_):
        if ins.line in self.breakpoints:
            self.paused=True;self.events.append(DebugEvent(vm.module.source_name,ins.line,ip,ins.op.name,{k:v.value for k,v in locals_.items()}))
    def run(self,module:ModuleIR,output=None):
        vm=VirtualMachine(output=output,trace_hook=self._trace);result=vm.run(module);return result,self.events
