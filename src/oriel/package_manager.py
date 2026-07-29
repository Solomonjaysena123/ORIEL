from __future__ import annotations
from pathlib import Path
import hashlib, json, shutil, tomllib, re

REGISTRY = {
 "oriel.core":{"versions":["0.3.0","0.4.0","0.5.0"],"description":"Core ORIEL utilities","dependencies":{}},
 "oriel.text":{"versions":["0.1.0","0.2.0"],"description":"Text helpers","dependencies":{"oriel.core":">=0.4.0"}},
 "oriel.math":{"versions":["0.1.0"],"description":"Math helpers","dependencies":{"oriel.core":">=0.3.0"}},
 "oriel.json":{"versions":["0.1.0"],"description":"JSON helpers","dependencies":{"oriel.core":">=0.3.0"}},
 "oriel.api":{"versions":["0.1.0","0.2.0"],"description":"ORIEL API framework with OpenAPI and structured responses","dependencies":{"oriel.core":">=0.5.0","oriel.json":">=0.1.0"}},
 "oriel.db":{"versions":["0.1.0"],"description":"ORIEL SQLite database and schema framework","dependencies":{"oriel.core":">=0.5.0","oriel.json":">=0.1.0"}},
}

def manifest_path(project):
 p=project/'oriel.toml'
 if not p.exists(): raise FileNotFoundError('oriel.toml was not found. Run inside an ORIEL project.')
 return p

def read_manifest(project): return tomllib.loads(manifest_path(project).read_text(encoding='utf-8'))
def _ver(v): return tuple(int(x) for x in re.findall(r'\d+',v)[:3])
def resolve(name,constraint=None):
 if name not in REGISTRY: raise ValueError(f"Package '{name}' is not available in the ORIEL registry.")
 versions=sorted(REGISTRY[name]['versions'],key=_ver,reverse=True)
 if not constraint or constraint in ('*','latest'): return versions[0]
 if constraint.startswith('>='):
  wanted=_ver(constraint[2:]); matches=[v for v in versions if _ver(v)>=wanted]
 elif constraint.startswith('^'):
  wanted=_ver(constraint[1:]); matches=[v for v in versions if _ver(v)[0]==wanted[0] and _ver(v)>=wanted]
 else: matches=[v for v in versions if v==constraint]
 if not matches: raise ValueError(f"No version of {name} satisfies '{constraint}'.")
 return matches[0]
def _write_manifest(project,data):
 p=data.get('project',{}); deps=data.get('dependencies',{}); lines=['[project]']
 for k in ('name','version','entry','profile'):
  if k in p: lines.append(f'{k} = "{p[k]}"')
 lines+=['','[dependencies]']; lines += [f'"{n}" = "{deps[n]}"' for n in sorted(deps)]
 manifest_path(project).write_text('\n'.join(lines)+'\n',encoding='utf-8')
def dependency_graph(deps):
 resolved={}; visiting=set()
 def visit(name,constraint):
  if name in visiting: raise ValueError(f'Circular package dependency involving {name}.')
  version=resolve(name,constraint)
  if name in resolved and resolved[name]!=version: raise ValueError(f'Version conflict for {name}: {resolved[name]} vs {version}')
  if name in resolved: return
  visiting.add(name); resolved[name]=version
  for child,c in REGISTRY[name].get('dependencies',{}).items(): visit(child,c)
  visiting.remove(name)
 for n,c in deps.items(): visit(n,c)
 return resolved
def add(project,package,version=None):
 data=read_manifest(project); constraint=version or 'latest'; resolve(package,constraint)
 data.setdefault('dependencies',{})[package]=constraint; _write_manifest(project,data); install(project); return resolve(package,constraint)
def remove(project,package):
 data=read_manifest(project)
 if package not in data.get('dependencies',{}): raise ValueError(f"Package '{package}' is not installed.")
 del data['dependencies'][package]; _write_manifest(project,data); install(project)
def install(project):
 data=read_manifest(project); resolved=dependency_graph(data.get('dependencies',{})); root=project/'.oriel'/'packages'
 if root.exists(): shutil.rmtree(root)
 root.mkdir(parents=True)
 for name,version in resolved.items():
  d=root/name; d.mkdir(parents=True); meta={"name":name,"version":version,"description":REGISTRY[name]['description'],"dependencies":REGISTRY[name].get('dependencies',{})}
  (d/'package.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
 write_lock(project,resolved); return len(resolved)
def write_lock(project,deps):
 packages=[{"name":n,"version":v,"checksum":hashlib.sha256(f'{n}@{v}'.encode()).hexdigest(),"dependencies":REGISTRY[n].get('dependencies',{})} for n,v in deps.items()]
 (project/'oriel.lock').write_text(json.dumps({"lock_version":2,"packages":packages},indent=2)+'\n',encoding='utf-8')
def list_registry(): return [(n,max(v['versions'],key=_ver),v['description']) for n,v in sorted(REGISTRY.items())]
