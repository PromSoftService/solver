#!/usr/bin/env python3
from collections import defaultdict
from analyze_cfg002_compare import load,newagg,add,finish
from report_cfg001_refine import old_bc

BCS=('A[K-J]x','BBx','K[9-2]x','[Q-8]x','A[T-2]x','[7-4]x')

def agg(rows,flt):
    d=defaultdict(newagg)
    for r in rows:
        if flt(r): add(d[r['oldbc']],r)
    return {k:finish(v) for k,v in d.items()}

def pr(name,d):
    vals=[]
    for b in BCS:
        if b not in d: vals.append(f'{b}=--'); continue
        z=d[b]
        vals.append(f"{b}=F{z['loss_F']:.4f}/C{z['loss_C']:.4f}/R{z['loss_R']:.4f} [{100*z['fold']:.1f}/{100*z['call']:.1f}/{100*z['raise']:.1f}]")
    print(name,' | '.join(vals))

p,rows=load('CFG001')
for r in rows:r['oldbc']=old_bc(r)
print('BB_CALL_DEFAULT',p)
# mutually useful broad rows
pr('Two pair+',agg(rows,lambda r:r['fx']['made'] in ('Straight','Set/Trips','Two pair')))
pr('Any ordinary pair',agg(rows,lambda r:r['fx']['made'] in ('Overpair','High underpair','Top pair','Second pair','Third pair')))
pr('Weak pocket pair',agg(rows,lambda r:r['fx']['made']=='Weak pocket pair'))
pr('OESD no pair',agg(rows,lambda r:r['fx']['made']=='High card' and r['fx']['sd']=='OESD'))
pr('Gutshot+BDFD no pair',agg(rows,lambda r:r['fx']['made']=='High card' and r['fx']['sd']=='Gutshot' and r['fx']['bdfd']))
pr('Gutshot noBDFD no pair',agg(rows,lambda r:r['fx']['made']=='High card' and r['fx']['sd']=='Gutshot' and not r['fx']['bdfd']))
pr('2OC+draw',agg(rows,lambda r:r['fx']['made']=='High card' and r['fx']['two_over'] and (r['fx']['sd'] is not None or r['fx']['bdfd'] or r['fx']['bdsd_paths'])))
pr('Bare AK/AQ/AJ',agg(rows,lambda r:r['fx']['made']=='High card' and r['fx']['hole'] in ('AK','AQ','AJ') and r['fx']['sd'] is None and not r['fx']['bdfd'] and not r['fx']['bdsd_paths']))
pr('Residual 2OC',agg(rows,lambda r:r['fx']['made']=='High card' and r['fx']['two_over'] and r['fx']['hole'] not in ('AK','AQ','AJ') and r['fx']['sd'] is None and not r['fx']['bdfd'] and not r['fx']['bdsd_paths']))
pr('Air',agg(rows,lambda r:r['fx']['made']=='High card' and not r['fx']['two_over'] and r['fx']['sd'] is None and not r['fx']['bdfd']))
