from pathlib import Path
import json, pytest
from oriel.package_resolver import *

def rel(name,v,deps=None): return PackageRelease(name,Version.parse(v),deps or {})

def test_semver_constraints():
    assert satisfies(Version.parse('1.4.0'),'^1.2.0')
    assert not satisfies(Version.parse('2.0.0'),'^1.2.0')
    assert satisfies(Version.parse('1.2.9'),'~1.2.0')

def test_transitive_resolution():
    registry={'a':[rel('a','1.0.0',{'b':'^2.0.0'})], 'b':[rel('b','2.1.0'),rel('b','2.0.0')]}
    selected=Resolver(registry).resolve({'a':'1.0.0'})
    assert str(selected['b'].version)=='2.1.0'

def test_conflict_detection():
    registry={'a':[rel('a','1.0.0',{'b':'1.0.0'})], 'c':[rel('c','1.0.0',{'b':'2.0.0'})], 'b':[rel('b','1.0.0'),rel('b','2.0.0')]}
    with pytest.raises(ResolutionError): Resolver(registry).resolve({'a':'1.0.0','c':'1.0.0'})

def test_lock_is_reproducible(tmp_path: Path):
    selected={'a':rel('a','1.0.0')}; p=write_lock(tmp_path/'oriel.lock',selected)
    first=p.read_text(); write_lock(p,selected); assert p.read_text()==first
