from __future__ import annotations
from pathlib import Path
import hashlib, json, shutil, tomllib, re, tarfile, tempfile

BUILTIN_REGISTRY={
 "oriel.core":{"versions":{"0.3.0":{"description":"Core ORIEL utilities","dependencies":{}},"0.4.0":{"description":"Core ORIEL utilities","dependencies":{}},"0.5.0":{"description":"Core ORIEL utilities","dependencies":{}},"0.7.3":{"description":"Core ORIEL utilities","dependencies":{}}}},
 "oriel.text":{"versions":{"0.2.0":{"description":"Text helpers","dependencies":{"oriel.core":">=0.7.3"}}}},
 "oriel.math":{"versions":{"0.1.0":{"description":"Math helpers","dependencies":{"oriel.core":">=0.7.3"}}}},
 "oriel.json":{"versions":{"0.1.0":{"description":"JSON helpers","dependencies":{"oriel.core":">=0.3.0"}}}},
 "oriel.api":{"versions":{"0.1.0":{"description":"ORIEL API framework","dependencies":{"oriel.core":">=0.5.0","oriel.json":">=0.1.0"}},"0.2.0":{"description":"ORIEL API framework","dependencies":{"oriel.core":">=0.5.0","oriel.json":">=0.1.0"}}}},
 "oriel.db":{"versions":{"0.1.0":{"description":"ORIEL database framework","dependencies":{"oriel.core":"0.5.0","oriel.json":">=0.1.0"}}}},
}
def manifest_path(project):
 p=Path(project)/'oriel.toml'
 if not p.exists():raise FileNotFoundError('oriel.toml was not found. Run inside an ORIEL project.')
 return p
def read_manifest(project):return tomllib.loads(manifest_path(project).read_text(encoding='utf-8'))
def _ver(v):return tuple(int(x) for x in re.findall(r'\d+',v)[:3])
def _registry_root(project):return Path(project)/'.oriel'/'registry'
def _load_registry(project):
 data=json.loads(json.dumps(BUILTIN_REGISTRY))
 index=_registry_root(project)/'index.json'
 if index.exists():
  local=json.loads(index.read_text(encoding='utf-8'))
  for n,v in local.items():data.setdefault(n,{"versions":{}})["versions"].update(v.get("versions",{}))
 return data
def resolve(name,constraint=None,project=Path.cwd()):
 reg=_load_registry(project)
 if name not in reg:raise ValueError(f"Package '{name}' is not available in the ORIEL registry.")
 versions=sorted(reg[name]['versions'],key=_ver,reverse=True)
 if not constraint or constraint in ('*','latest'):return versions[0]
 if constraint.startswith('>='):matches=[v for v in versions if _ver(v)>=_ver(constraint[2:])]
 elif constraint.startswith('^'):
  w=_ver(constraint[1:]);matches=[v for v in versions if _ver(v)[0]==w[0] and _ver(v)>=w]
 elif constraint.startswith('~'):
  w=_ver(constraint[1:]);matches=[v for v in versions if _ver(v)[:2]==w[:2] and _ver(v)>=w]
 else:matches=[v for v in versions if v==constraint]
 if not matches:raise ValueError(f"No version of {name} satisfies '{constraint}'.")
 return matches[0]
def _write_manifest(project,data):
 p=data.get('project',{});deps=data.get('dependencies',{});lines=['[project]']
 for k in ('name','version','entry','profile'):
  if k in p:lines.append(f'{k} = "{p[k]}"')
 lines+=['','[dependencies]']
 for n in sorted(deps):
  value=deps[n]
  if isinstance(value,dict):
   attrs=', '.join(f'{k} = "{v}"' for k,v in value.items());lines.append(f'"{n}" = {{ {attrs} }}')
  else:lines.append(f'"{n}" = "{value}"')
 manifest_path(project).write_text('\n'.join(lines)+'\n',encoding='utf-8')
def _constraint(spec):return spec.get('version','latest') if isinstance(spec,dict) else spec
def dependency_graph(project, deps=None):
 legacy = deps is None
 if legacy:
  deps=project; project=Path.cwd()
 reg=_load_registry(project);resolved={};visiting=set()
 def visit(name,spec):
  if isinstance(spec,dict) and 'path' in spec:
   p=(Path(project)/spec['path']).resolve();m=read_manifest(p);ver=m.get('project',{}).get('version','0.0.0');key=(name,ver,str(p))
   if name in resolved and resolved[name]['version']!=ver:raise ValueError(f'Version conflict for {name}')
   resolved[name]={"version":ver,"source":"path","path":str(p),"dependencies":m.get('dependencies',{})}
   for child,childspec in m.get('dependencies',{}).items():visit(child,childspec)
   return
  if name in visiting:raise ValueError(f'Circular package dependency involving {name}.')
  constraint=_constraint(spec)
  if name in resolved:
   current=resolved[name]['version']
   # Keep an already selected version when it satisfies the incoming constraint.
   try:
    candidates=_load_registry(project)[name]['versions']
    if constraint in (None,'*','latest') or (constraint.startswith('>=') and _ver(current)>=_ver(constraint[2:])) or (constraint.startswith('^') and _ver(current)[0]==_ver(constraint[1:])[0] and _ver(current)>=_ver(constraint[1:])) or current==constraint:
     return
   except Exception:
    pass
   raise ValueError(f'Version conflict for {name}: {current} does not satisfy {constraint}')
  version=resolve(name,constraint,project)
  visiting.add(name);meta=reg[name]['versions'][version];resolved[name]={"version":version,"source":"registry","dependencies":meta.get('dependencies',{}),"archive":meta.get('archive')}
  for child,c in meta.get('dependencies',{}).items():visit(child,c)
  visiting.remove(name)
 for n,s in deps.items():visit(n,s)
 return {n:m["version"] for n,m in resolved.items()} if legacy else resolved
def add(project,package,version=None,path=None):
 data=read_manifest(project);spec={"path":path} if path else (version or 'latest')
 if not path:resolve(package,spec,project)
 data.setdefault('dependencies',{})[package]=spec;_write_manifest(project,data);install(project);return spec
def remove(project,package):
 data=read_manifest(project)
 if package not in data.get('dependencies',{}):raise ValueError(f"Package '{package}' is not installed.")
 del data['dependencies'][package];_write_manifest(project,data);install(project)
def _checksum_file(path):
 h=hashlib.sha256();
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(65536),b''):h.update(chunk)
 return h.hexdigest()
def install(project):
 project=Path(project);resolved=dependency_graph(project,read_manifest(project).get('dependencies',{}));root=project/'.oriel'/'packages'
 if root.exists():shutil.rmtree(root)
 root.mkdir(parents=True)
 for name,meta in resolved.items():
  d=root/name;source=meta['source']
  if source=='path':shutil.copytree(meta['path'],d,ignore=shutil.ignore_patterns('.git','.oriel','build','dist','__pycache__'))
  elif meta.get('archive') and Path(meta['archive']).exists():
   d.mkdir();
   with tarfile.open(meta['archive'],'r:gz') as tf:tf.extractall(d,filter='data')
  else:d.mkdir();(d/'package.json').write_text(json.dumps({"name":name,**meta},indent=2),encoding='utf-8')
 write_lock(project,resolved);return len(resolved)
def write_lock(project,deps):
 packages=[]
 ordered=list(deps.items())
 for n,m in ordered:
  identity=f'{n}@{m["version"]}:{m["source"]}'.encode();packages.append({"name":n,"version":m['version'],"source":m['source'],"checksum":hashlib.sha256(identity).hexdigest(),"dependencies":m.get('dependencies',{})})
 (Path(project)/'oriel.lock').write_text(json.dumps({"lock_version":2,"packages":packages},indent=2)+'\n',encoding='utf-8')
def publish(project,registry=None):
 project=Path(project);manifest=read_manifest(project);p=manifest.get('project',{});name=p.get('name');version=p.get('version')
 if not name or not version:raise ValueError('Project name and version are required to publish.')
 root=Path(registry) if registry else _registry_root(project);root.mkdir(parents=True,exist_ok=True);archive=root/f'{name}-{version}.tar.gz'
 with tarfile.open(archive,'w:gz') as tf:
  for path in project.rglob('*'):
   if path.is_file() and not any(x in path.parts for x in ('.git','.oriel','build','dist','__pycache__')):tf.add(path,arcname=path.relative_to(project))
 index=root/'index.json';data=json.loads(index.read_text()) if index.exists() else {};data.setdefault(name,{"versions":{}})['versions'][version]={"description":p.get('description',''),"dependencies":manifest.get('dependencies',{}),"archive":str(archive),"checksum":_checksum_file(archive)};index.write_text(json.dumps(data,indent=2)+'\n');return archive
def list_registry(project=Path.cwd()):
 reg=_load_registry(project);out=[]
 for n,v in sorted(reg.items()):
  latest=max(v['versions'],key=_ver);out.append((n,latest,v['versions'][latest].get('description','')))
 return out
