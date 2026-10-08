"""Replay the frozen audit in a fresh temp directory; never generate a strategy.
Requires Python 3 and numpy. No solver, network, or repository writes.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,zipfile

HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'archive-manifest.json').read_text(encoding='utf8'))
archive=HERE/'calculation-archive.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['archive_sha256']
work=Path(tempfile.mkdtemp(prefix='solver-nine-audit-'))
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist())==set(manifest['files'])
    for name,meta in manifest['files'].items():
        target=(work/name).resolve()
        assert target.is_relative_to(work.resolve())
        data=z.read(name)
        assert len(data)==meta['bytes'] and hashlib.sha256(data).hexdigest()==meta['sha256']
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
analysis=work/'analysis'
expected=json.loads((analysis/'rounding_boundary_audit.json').read_text(encoding='utf8'))
# Mechanical relocation in disposable copies only. Original archived bytes stay immutable.
for name in ['utg_cbet_six_audit.py','bb_defense_nine_frequency_audit.py']:
    p=analysis/name;t=p.read_text(encoding='utf8')
    old="ROOT=Path(r'D:\\current\\coding\\Solver\\tsgpu-batch-production-v012')"
    assert old in t
    p.write_text(t.replace(old,'ROOT=Path('+repr(str(work))+')'),encoding='utf8')
p=analysis/'frequency_table_ev_audit.py';t=p.read_text(encoding='utf8')
old="MD=Path(r'D:\\current\\manuals\\покер\\strategy_unified_flops.md')"
assert old in t
p.write_text(t.replace(old,'MD=Path('+repr(str(analysis/'intermediate-strategy.md'))+')'),encoding='utf8')
print('Verified archive; audit working directory:',work,flush=True)
subprocess.run([sys.executable,'-X','utf8','-B',str(analysis/'rounding_boundary_audit.py')],check=True)
actual=json.loads((analysis/'rounding_boundary_audit.json').read_text(encoding='utf8'))
def compare(a,b,path=''):
    if isinstance(a,dict):
        assert a.keys()==b.keys(),path
        for k in a:compare(a[k],b[k],path+'/'+k)
    elif isinstance(a,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
    elif isinstance(a,(float,int)):
        assert abs(a-b)<=1e-9*max(1,abs(a)),(path,a,b)
    else:assert a==b,(path,a,b)
compare(expected,actual)
print('PASS: all saved rounding results reproduced; temporary evidence retained at',work)
