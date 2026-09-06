#!/usr/bin/env python3
import csv, glob, re
from collections import defaultdict
from analyze_cfg002_compare import features

CLASSES = [
    ('ABB', {'AKQ','AKJ','AKT','AQJ','AQT','AJT'}),
    ('A[K/Q]x', {f'A{b}{x}' for b in 'KQ' for x in '98765432'}),
    ('BBB', {'KQJ','KQT','KJT','QJT'}),
    ('BBx dis', {'KQ7','KJ4','KJ3','KT3','QJ5','QJ4','QT3','JT6','JT4'}),
    ('K/Qx dis', {'K97','K84','K73','K62','K52','Q95','Q84','Q73','Q62','Q52'}),
    ('A[J-T][9-5]', {f'A{b}{x}' for b in 'JT' for x in '98765'}),
    ('K/Qx con', {'K98','K87','K76','K65','K54','Q98','Q87','Q76','Q65','Q54','Q43'}),
    ('A[9-7]x', {f'A{b}{x}' for b in '987' for x in '65432' if 'AKQJT98765432'.index(x) > 'AKQJT98765432'.index(b)}),
    ('[J-8]x dis', {'J84','J73','J62','T74','T63','T52','964','953','842','832'}),
    ('A[J-T][4-2]', {f'A{b}{x}' for b in 'JT' for x in '432'}),
    ('[J-8]x con', {'JT8','J98','J87','T98','T87','T76','987','876','865'}),
    ('[7-4]x', {'765','754','743','742','654','643','642','632','543','532','432'}),
    ('A[6-2]', {'A65','A64','A63','A62','A54','A53','A52','A43','A42','A32'}),
]
CLASS_OF={flop:k for k,flops in CLASSES for flop in flops}
MERGED=[
    ('HIGH', ('ABB','A[K/Q]x','BBB','BBx dis')),
    ('BET75', ('K/Qx dis','A[J-T][9-5]','A[J-T][4-2]')),
    ('MID55', ('K/Qx con','A[9-7]x','[J-8]x dis')),
    ('CON47', ('[J-8]x con',)),
    ('A_LOW30', ('A[6-2]',)),
    ('LOW13', ('[7-4]x',)),
]
GROUP_OF={k:g for g,ks in MERGED for k in ks}
ORDER='AKQJT98765432'; VAL={r:13-i for i,r in enumerate(ORDER)}
def f(s): return float(str(s).replace(',','.'))
def sig(board):
    rs=re.findall(r'([2-9TJQKA])[cdhs]',board)
    return ''.join(sorted(rs,key=lambda r:VAL[r],reverse=True))
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
CATS=('Two pair+','Overpair','Underpair','Top pair','Second pair','Third pair','Weak pocket pair','OESD','Gutshot','BDFD','2 overcards','Air')
p=sorted(glob.glob('datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-*.csv'))[-1]
rows=[]; cells=defaultdict(lambda:[0.,0.,0.,0.])
with open(p,encoding='utf-8-sig',newline='') as fh:
    for x in csv.DictReader(fh):
        k=CLASS_OF.get(sig(x['board']))
        if k is None: continue
        g=GROUP_OF[k]; c=cat(features(x['board'],x['combo']))
        w=f(x['reach_probability']); bf=f(x['bet_frequency']); lb=f(x['loss_if_bet_utg']); lx=f(x['loss_if_check_utg'])
        rows.append((g,c,w,bf,lb,lx))
        a=cells[(g,c)]; a[0]+=w; a[1]+=w*bf; a[2]+=w*lb; a[3]+=w*lx

def nearest(v,vals): return min(vals,key=lambda q:(abs(q-v),-q))
SCHEMES={
 'PURE_NEAREST': lambda v: 1.0 if v>=.5 else 0.0,
 'MIX50_NEAREST': lambda v: nearest(v,(0,.5,1)),
 'QUARTERS': lambda v: nearest(v,(0,.25,.5,.75,1)),
 'MIX50_30_70': lambda v: 1.0 if v>=.70 else (0.0 if v<=.30 else .5),
}
print('FREQUENCY_AWARE_SIMPLIFICATION',p)
print('CELL_FREQS')
for c in CATS:
    print(c, ' | '.join(f'{g}={100*cells[(g,c)][1]/cells[(g,c)][0]:.1f}' if cells[(g,c)][0] else f'{g}=--' for g,_ in MERGED))
for name,fn in SCHEMES.items():
    probs={}
    for key,(w,wb,lb,lx) in cells.items(): probs[key]=fn(wb/w)
    totalw=targetb=actualb=loss=0.
    per=defaultdict(lambda:[0.,0.,0.,0.])
    for g,c,w,bf,lb,lx in rows:
        q=probs[(g,c)]
        totalw+=w; targetb+=w*bf; actualb+=w*q; loss+=w*(q*lb+(1-q)*lx)
        z=per[g]; z[0]+=w; z[1]+=w*bf; z[2]+=w*q; z[3]+=w*(q*lb+(1-q)*lx)
    print('SCHEME',name,'ALL target',f'{100*targetb/totalw:.1f}','actual',f'{100*actualb/totalw:.1f}','delta',f'{100*(actualb-targetb)/totalw:+.1f}','local_loss',f'{loss/totalw:.4f}')
    for g,_ in MERGED:
        w,t,a,l=per[g]; print(' ',g,'target',f'{100*t/w:.1f}','actual',f'{100*a/w:.1f}','delta',f'{100*(a-t)/w:+.1f}','loss',f'{l/w:.4f}')
    print('MATRIX',name)
    for c in CATS:
        vals=[]
        for g,_ in MERGED:
            if cells[(g,c)][0]==0: vals.append(f'{g}=--')
            else: vals.append(f'{g}={int(round(100*probs[(g,c)]))}')
        print(' ',c,' | '.join(vals))
