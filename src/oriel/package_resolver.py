"""ORIEL 0.7.4 semantic-version package resolver and reproducible lock files."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib, json, re

@dataclass(frozen=True, order=True)
class Version:
    major:int; minor:int; patch:int
    @classmethod
    def parse(cls,text):
        m=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)',text.strip())
        if not m: raise ValueError(f"Invalid semantic version: {text}")
        return cls(*map(int,m.groups()))
    def __str__(self): return f"{self.major}.{self.minor}.{self.patch}"

def satisfies(version: Version, constraint: str) -> bool:
    c=constraint.strip()
    if c.startswith('^'):
        base=Version.parse(c[1:]); return version>=base and version.major==base.major
    if c.startswith('~'):
        base=Version.parse(c[1:]); return version>=base and (version.major,version.minor)==(base.major,base.minor)
    if c.startswith('>='): return version>=Version.parse(c[2:])
    return version==Version.parse(c)

@dataclass(frozen=True)
class PackageRelease:
    name:str; version:Version; dependencies:dict[str,str]; checksum:str=''

class ResolutionError(Exception): pass

class Resolver:
    def __init__(self, registry: dict[str,list[PackageRelease]]): self.registry=registry
    def resolve(self, requirements: dict[str,str]) -> dict[str,PackageRelease]:
        selected={}; pending=list(requirements.items())
        while pending:
            name,constraint=pending.pop(0)
            if name in selected:
                if not satisfies(selected[name].version,constraint): raise ResolutionError(f"Conflict for {name}: {selected[name].version} vs {constraint}")
                continue
            choices=sorted((r for r in self.registry.get(name,[]) if satisfies(r.version,constraint)), key=lambda r:r.version, reverse=True)
            if not choices: raise ResolutionError(f"No compatible release for {name} {constraint}")
            selected[name]=choices[0]; pending.extend(choices[0].dependencies.items())
        return selected

def write_lock(path: Path, selected: dict[str,PackageRelease]) -> Path:
    payload={'lockVersion':1,'packages':[]}
    for name,r in sorted(selected.items()):
        checksum=r.checksum or hashlib.sha256(f'{name}@{r.version}'.encode()).hexdigest()
        payload['packages'].append({'name':name,'version':str(r.version),'dependencies':r.dependencies,'sha256':checksum})
    path.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8'); return path

def read_registry(path: Path):
    data=json.loads(path.read_text(encoding='utf-8')); result={}
    for name,releases in data.items():
        result[name]=[PackageRelease(name,Version.parse(x['version']),x.get('dependencies',{}),x.get('sha256','')) for x in releases]
    return result
