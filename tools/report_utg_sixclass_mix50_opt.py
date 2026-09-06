#!/usr/bin/env python3
import csv, glob, itertools
from collections import defaultdict
from analyze_cfg002_compare import features

BCS=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')
CATS=('Two pair+','Overpair','Underpair','Top pair','Second pair','Third pair','Weak pocket pair','OESD','Gutshot','BDFD','2 overcards','Air')

def f(s): return float(str(s).replace(',','.'))
def bc(fx):
    h,m=fx['top'],fx['mid']
    if h==14:return 'A[K-J]x' if m>=11 else 'A[T-2]x'
    if sum(v>=10 for v in (fx['top'],fx['mid'],fx['low']))>=2:return 'BBx'
    if h==13:return 'K[9-2]x'
    if 8<=h<=12:return '[Q-8]x'
    return '[7-4]x'
def cat(fx):
    m=fx['made']
    if m in ('Straight','Set/Trips','Two pair'): return 'Two pair+'
    if m=='Overpair': return 'Overpair'
    if m=='High underpair': return 'Underpair'
    if m=='Top pair': return 'Top pair'
    if m=='Second pair': return 'Second pair'
    if m=='Third pair': return 'Third pair'
    if m=='Weak pocket pair': return 'Weak pocket pair'
    if fx['sd']=='OESD': return 'OESD'
    if fx['sd']=='Gutshot': return 'Gutshot'
    if fx['bdfd']: return 'BDFD'
    if fx['two_over']: return '2 overcards'
    return 'Air'

p=sorted(glob.glob('datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-*.csv'))[-1]
cells=defaultdict(lambda:[0.,0.,0.,0.]) # w, target betw, lossBw, lossXw
with open(p,encoding='utf-8-sig',newline='') as fh:
    for x in csv.DictReader(fh):
        fx=features(x['board'],x['combo']); k=bc(fx); c=cat(fx); w=f(x['reach_probability'])
        a=cells[(k,c)]; a[0]+=w; a[1]+=w*f(x['bet_frequency']); a[2]+=w*f(x['loss_if_bet_utg']); a[3]+=w*f(x['loss_if_check_utg'])

# Enumerate all 0/50/100 assignments. Besides exact aggregate frequency and local regret,
# also measure weighted squared distance from the solver's hand-class frequencies. This
# discourages pathological solutions that match the total by checking a 95%-bet category
# while betting a 20%-bet category.
for k in BCS:
    present=[c for c in CATS if cells[(k,c)][0]>0]
    W=sum(cells[(k,c)][0] for c in present); target=sum(cells[(k,c)][1] for c in present)/W
    best_close=None; best2=None; best5=None; best_shape2=None; best_shape5=None
    for acts in itertools.product((0.,.5,1.), repeat=len(present)):
        ab=sum(cells[(k,c)][0]*q for c,q in zip(present,acts))/W
        loss=sum(q*cells[(k,c)][2]+(1-q)*cells[(k,c)][3] for c,q in zip(present,acts))/W
        shape=sum(cells[(k,c)][0]*(q-cells[(k,c)][1]/cells[(k,c)][0])**2 for c,q in zip(present,acts))/W
        err=abs(ab-target)
        rec=(err,loss,shape,ab,acts)
        if best_close is None or (err,loss)<(best_close[0],best_close[1]): best_close=rec
        if err<=.02 and (best2 is None or (loss,err)<(best2[1],best2[0])): best2=rec
        if err<=.05 and (best5 is None or (loss,err)<(best5[1],best5[0])): best5=rec
        if err<=.02 and (best_shape2 is None or (shape,loss,err)<(best_shape2[2],best_shape2[1],best_shape2[0])): best_shape2=rec
        if err<=.05 and (best_shape5 is None or (shape,loss,err)<(best_shape5[2],best_shape5[1],best_shape5[0])): best_shape5=rec
    print('CLASS',k,'target',round(100*target,2),'n',len(present))
    for label,rec in [('CLOSEST',best_close),('LOSS_WITHIN_2PP',best2),('SHAPE_WITHIN_2PP',best_shape2),('SHAPE_WITHIN_5PP',best_shape5)]:
        if rec is None: continue
        err,loss,shape,ab,acts=rec
        print(label,'actual',round(100*ab,2),'delta',round(100*(ab-target),2),'loss',round(loss,5),'shape',round(shape,5))
        print(' ', ' | '.join(f'{c}={"CHECK" if q==0 else "MIX" if q==.5 else "BET"}' for c,q in zip(present,acts)))
