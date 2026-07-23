from __future__ import annotations
from dataclasses import dataclass, asdict
from time import perf_counter
from .compiler import ModuleIR
from .vm import VirtualMachine
@dataclass
class ProfileResult:
    elapsed_ms: float; instructions: int; instructions_per_second: float
    def to_dict(self): return asdict(self)
def profile(module:ModuleIR,iterations:int=1):
    total_steps=0;start=perf_counter()
    for _ in range(iterations):
        vm=VirtualMachine(output=lambda _:None);vm.run(module);total_steps+=vm.steps
    elapsed=perf_counter()-start
    return ProfileResult(elapsed*1000,total_steps,total_steps/elapsed if elapsed else 0.0)
