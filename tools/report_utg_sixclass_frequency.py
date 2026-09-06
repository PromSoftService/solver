#!/usr/bin/env python3
import csv, glob
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
def nearest(v,vals): return min(vals,key=lambda q:(abs(q-v),-q))
SCHEMES={
    'PURE': lambda v: 1.0 if v>=.5 else 0.0,
    'MIX50': lambda v: nearest(v,(0,.5,1)),
    'THRESH_30_70': lambda v: 1.0 if v>=.70 else (0.0 if v<=.30 else .5),
    'QUARTERS': lambda v: nearest(v,(0,.25,.5,.75,1)),
}

p=sorted(glob.glob('datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-*.csv'))[-1]
rows=[]; cells=defaultdict(lambda:[0.,0.,0.,0.]); boards=defaultdict(lambda:defaultdict(lambda:[0.,0.]))
with open(p,encoding='utf-8-sig',newline='') as fh:
    for x in csv.DictReader(fh):
        fx=features(x['board'],x['combo']); k=bc(fx); c=cat(fx)
        w=f(x['reach_probability']); bf=f(x['bet_frequency']); lb=f(x['loss_if_bet_utg']); lx=f(x['loss_if_check_utg'])
        rows.append((k,c,w,bf,lb,lx))
        a=cells[(k,c)]; a[0]+=w; a[1]+=w*bf; a[2]+=w*lb; a[3]+=w*lx
        z=boards[k][x['board']]; z[0]+=w; z[1]+=w*bf

print('UTG_SIXCLASS_FREQUENCY',p)
print('BOARD_SUMMARY')
for k in BCS:
    vals=[100*wb/w for w,wb in boards[k].values()]
    tw=sum(w for w,wb in boards[k].values()); tb=sum(wb for w,wb in boards[k].values())
    mean=100*tb/tw
    mae=sum(abs(v-mean) for v in vals)/len(vals)
    print(k,'n',len(vals),'freq',f'{mean:.1f}','min',f'{min(vals):.1f}','max',f'{max(vals):.1f}','MAE',f'{mae:.1f}')
print('CELL_FREQ lossB lossX')
for c in CATS:
    print(c,' | '.join((f'{k}={100*cells[(k,c)][1]/cells[(k,c)][0]:.1f}/{cells[(k,c)][2]/cells[(k,c)][0]:.4f}/{cells[(k,c)][3]/cells[(k,c)][0]:.4f}' if cells[(k,c)][0] else f'{k}=--') for k in BCS))

for name,fn in SCHEMES.items():
    probs={(k,c):fn(wb/w) for (k,c),(w,wb,lb,lx) in cells.items() if w>0}
    per=defaultdict(lambda:[0.,0.,0.,0.]); TW=TB=TA=TL=0.
    for k,c,w,bf,lb,lx in rows:
        q=probs[(k,c)]
        TW+=w; TB+=w*bf; TA+=w*q; TL+=w*(q*lb+(1-q)*lx)
        z=per[k]; z[0]+=w; z[1]+=w*bf; z[2]+=w*q; z[3]+=w*(q*lb+(1-q)*lx)
    print('SCHEME',name,'ALL target',f'{100*TB/TW:.1f}','actual',f'{100*TA/TW:.1f}','delta',f'{100*(TA-TB)/TW:+.1f}','local_loss',f'{TL/TW:.4f}')
    for k in BCS:
        w,t,a,l=per[k]
        print(' ',k,'target',f'{100*t/w:.1f}','actual',f'{100*a/w:.1f}','delta',f'{100*(a-t)/w:+.1f}','loss',f'{l/w:.4f}')
    print('MATRIX',name)
    for c in CATS:
        print(' ',c,' | '.join((f'{k}={int(round(100*probs[(k,c)]))}' if cells[(k,c)][0] else f'{k}=--') for k in BCS))
