#!/usr/bin/env python3
from collections import defaultdict
from analyze_cfg002_compare import load, newagg, add, finish
from report_cfg001_refine import old_bc

BCS=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')

def agg(rows, flt):
    d=defaultdict(newagg)
    for r in rows:
        if flt(r): add(d[r['oldbc']], r)
    return {k:finish(v) for k,v in d.items()}

def hole(r): return r['fx']['hole']
def nodraw(r): return r['fx']['sd'] is None and not r['fx']['bdfd'] and not r['fx']['bdsd_paths']
def p(z): return f"w={z['weight']:.1f} FCR={100*z['fold']:.1f}/{100*z['call']:.1f}/{100*z['raise']:.1f} lossF={z['loss_F']:.4f} lossC={z['loss_C']:.4f} lossR={z['loss_R']:.4f}"

path,rows=load('CFG001')
for r in rows: r['oldbc']=old_bc(r)
print('DATASET',path)
# exact broad row: high-card + 2OC + no draw
sets=[
 ('2OC_NODRAW_ALL', lambda r:r['fx']['made']=='High card' and r['fx']['two_over'] and nodraw(r)),
 ('2OC_NODRAW_EXCL_AK_AQ_AJ', lambda r:r['fx']['made']=='High card' and r['fx']['two_over'] and nodraw(r) and hole(r) not in ('AK','AQ','AJ')),
 ('2OC_NODIRECT_ALL', lambda r:r['fx']['made']=='High card' and r['fx']['two_over'] and r['fx']['sd'] is None),
 ('2OC_NODIRECT_EXCL_AK_AQ_AJ', lambda r:r['fx']['made']=='High card' and r['fx']['two_over'] and r['fx']['sd'] is None and hole(r) not in ('AK','AQ','AJ')),
]
for name,flt in sets:
    print(name)
    d=agg(rows,flt)
    total=newagg()
    for r in rows:
        if flt(r): add(total,r)
    for b in BCS:
        if b in d: print(b,p(d[b]))
    z=finish(total); print('ALL',p(z))
