"""Read-only checks for the manually approved document; no table generation."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
old=(HERE/'intermediate-strategy.md').read_text(encoding='utf8')
new=(HERE/'approved-strategy.md').read_text(encoding='utf8')
def block(t,title):return t.split(title,1)[1].split('\n### ',1)[0]
def rows(t):
    result={}
    for line in t.splitlines():
        if not line.startswith('|'):continue
        cells=[x.strip() for x in line.strip('|').split('|')]
        if cells[0]=='Рука' or cells[0].startswith('-') or 'Весь диапазон' in cells[0]:continue
        result[cells[0]]=cells[1:]
    return result
cases=[
 ('### UTG vs BB: BB чек → UTG','### UTG vs BB: BB чек → UTG ставит или чекает',False),
 ('### BB против UTG: частота рейза среди продолжений','### BB против UTG: BB чек → UTG ставит ½ банка → BB',True),
 ('### BTN vs BB: BB чек → BTN','### BTN vs BB: BB чек → BTN ставит или чекает',False),
 ('### BB против BTN: частота рейза среди продолжений','### BB против BTN: BB чек → BTN ставит ½ банка → BB',True)]
previous=-1;checked=0
for before,after,defense in cases:
    ix=new.index(after);assert ix>previous;previous=ix
    source,target=rows(block(old,before)),rows(block(new,after))
    assert source.keys()==target.keys() and len(source)==12
    for hand,values in source.items():
        assert len(values)==len(target[hand])==9
        for src,dst in zip(values,target[hand]):
            left=[x.strip() for x in src.split('/')];right=[x.strip() for x in dst.split('·')]
            assert len(left)==len(right),(hand,src,dst)
            for a,b in zip(left,right):
                if a in {'F','—','К1','К2'}:assert a==b;continue
                star=a.endswith('*');n=int(a.rstrip('*'))
                expected=('C' if n<=30 else 'R' if n>=70 else 'C/R') if defense else ('X' if n<=30 else 'B' if n>=70 else 'X/B')
                assert b==expected+('*' if star else ''),(hand,src,dst)
                checked+=1
# Verify both classifier tables independently of the four main grids.
for key,nextkey in [('К1','К2'),('К2',None)]:
    ob=old.split('**'+key+'.',1)[1]
    ob=ob.split('**'+nextkey+'.',1)[0] if nextkey else ob.split('### Глобальные правила',1)[0]
    nb=new.split('**'+key+'.',1)[1]
    nb=nb.split('**'+nextkey+'.',1)[0] if nextkey else nb.split('### Классификаторы защиты',1)[0]
    sr=[l for l in ob.splitlines() if l.startswith('|')][2:]
    tr=[l for l in nb.splitlines() if l.startswith('|')][2:]
    assert len(sr)==len(tr)
    for a,b in zip(sr,tr):
        aa=[x.strip().replace('**','').replace('%','') for x in a.strip('|').split('|')][1:]
        bb=[x.strip() for x in b.strip('|').split('|')][1:]
        for numeric,action in zip(aa,bb[::-1]):
            parts=[int(x.strip()) for x in numeric.split('/')]
            expected=' · '.join('X' if x<=30 else 'B' if x>=70 else 'X/B' for x in parts)
            assert action==expected,(key,numeric,action)
theory='### Как обосновывать ставку через диапазоны'
assert new.split(theory,1)[1].strip()==old.split(theory,1)[1].split('## Защита BB против c-bet',1)[0].strip()
for token in ['Пограничное отправлено','Метод расчёта промежуточных','Почему предложено 30/70','Весь диапазон']:
    assert token not in new
if len(sys.argv)>1:
    external=Path(sys.argv[1]).read_text(encoding='utf8')
    assert external[external.index(new.splitlines()[0]):].strip()==new.strip()
print('PASS:',checked,'numeric subcells; 4 tables/12 rows/9 columns; both classifiers; table order; theory unchanged; external copy matches when supplied.')
