#!/usr/bin/env python3
import csv, glob
from collections import defaultdict
from analyze_cfg002_compare import features

BCS=('A[K-J]x','BBx','K[9-2]x','[Q-8]x','A[T-2]x','[7-4]x')

def f(s): return float(str(s).replace(',','.'))

def bc(fx):
    h,m=fx['top'],fx['mid']
    if h==14: return 'A[K-J]x' if m>=11 else 'A[T-2]x'
    if sum(v>=10 for v in (fx['top'],fx['mid'],fx['low']))>=2: return 'BBx'
    if h==13: return 'K[9-2]x'
    if 8<=h<=12: return '[Q-8]x'
    return '[7-4]x'

def cat(fx):
    m=fx['made']
    if m in ('Straight','Set/Trips','Two pair'): return 'Two pair+'
    if m=='Weak pocket pair': return 'Weak pocket pair'
    if fx['sd']=='OESD': return 'OESD'
    if m=='Overpair': return 'Overpair'
    if m=='High underpair': return 'Underpair'
    if m=='Top pair': return 'Top pair'
    if m=='Second pair': return 'Second pair'
    if m=='Third pair': return 'Third pair'
    if fx['sd']=='Gutshot': return 'Gutshot'
    if fx['bdfd']: return 'BDFD'
    if fx['two_over']: return '2 overcards'
    return 'Air'

def action(k,c):
    # Simplification target: BET by default. Keep only clearly bad BET cells as CHECK.
    if k=='[7-4]x' and c in ('Two pair+','Weak pocket pair','OESD'):
        return 'X'
    return 'B'

p=sorted(glob.glob('datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-*.csv'))[-1]
agg=defaultdict(lambda:[0.0,0.0,0.0,0.0,0.0]) # w, betfreq, lossB, lossX, selected
classes=defaultdict(lambda:[0.0,0.0,0.0]) # w, selected bet weight, selected loss
TW=TL=TB=0.0
with open(p,encoding='utf-8-sig',newline='') as fh:
    for x in csv.DictReader(fh):
        fx=features(x['board'],x['combo']); k=bc(fx); c=cat(fx); w=f(x['reach_probability'])
        lb=f(x['loss_if_bet_utg']); lx=f(x['loss_if_check_utg']); bf=f(x['bet_frequency'])
        z=action(k,c)
        a=agg[(k,c)]; a[0]+=w; a[1]+=w*bf; a[2]+=w*lb; a[3]+=w*lx; a[4]+=w*(lb if z=='B' else lx)
        q=classes[k]; q[0]+=w; q[1]+=w*(z=='B'); q[2]+=w*(lb if z=='B' else lx)
        TW+=w; TB+=w*(z=='B'); TL+=w*(lb if z=='B' else lx)

cats=('Two pair+','Overpair','Underpair','Top pair','Second pair','Third pair','Weak pocket pair','OESD','Gutshot','BDFD','2 overcards','Air')
print('UTG_RANGEBET_EXCEPTIONS')
print('dataset',p)
print('CELL_LOSSES lossB/lossX solverBetPct')
for c in cats:
    vals=[]
    for k in BCS:
        if (k,c) not in agg:
            vals.append(f'{k}=--')
            continue
        w,bf,lb,lx,sel=agg[(k,c)]
        vals.append(f'{k}={lb/w:.4f}/{lx/w:.4f}/{100*bf/w:.1f}')
    print(c,' | '.join(vals))
print('SELECTED_RULE')
for k in BCS:
    w,b,l=classes[k]
    print(k,'bet_pct',round(100*b/w,1),'loss',round(l/w,4),'w',round(w,1))
print('ALL bet_pct',round(100*TB/TW,1),'loss',round(TL/TW,4),'w',round(TW,1))
