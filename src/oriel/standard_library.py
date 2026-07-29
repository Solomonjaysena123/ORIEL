"""ORIEL 0.7.3 standard-library registry."""
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class StandardModule:
    name: str
    exports: tuple[str, ...]
    summary: str

MODULES = {
 "oriel.core": StandardModule("oriel.core", ("print","len","type_of","range"), "Core language helpers"),
 "oriel.text": StandardModule("oriel.text", ("upper","lower","trim","split","join"), "Text utilities"),
 "oriel.math": StandardModule("oriel.math", ("abs","min","max","round","sqrt"), "Mathematics"),
 "oriel.collections": StandardModule("oriel.collections", ("push","pop","contains","sort"), "Collection helpers"),
 "oriel.files": StandardModule("oriel.files", ("read","write","exists","remove"), "File-system helpers"),
 "oriel.json": StandardModule("oriel.json", ("encode","decode"), "JSON support"),
 "oriel.time": StandardModule("oriel.time", ("now","sleep"), "Date and time"),
 "oriel.config": StandardModule("oriel.config", ("load","get"), "Configuration"),
 "oriel.logging": StandardModule("oriel.logging", ("debug","info","warn","error"), "Logging"),
 "oriel.testing": StandardModule("oriel.testing", ("test","expect"), "Testing primitives"),
}

def list_modules(): return tuple(MODULES.values())
def resolve_standard_module(name: str) -> StandardModule:
    try: return MODULES[name]
    except KeyError: raise LookupError(f"Unknown standard module: {name}")
