#!/usr/bin/env python3
import csv, glob
from collections import defaultdict
from analyze_cfg002_compare import features

BCS=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')

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

B='BET'; X='CHECK'; M='MIX'
RULE={
'A[K-J]x':{
 'Two pair+':B,'Underpair':M,'Top pair':B,'Second pair':B,'Third pair':B,'Weak pocket pair':M,'OESD':B,'Gutshot':B,'BDFD':B,'Air':B},
'A[T-2]x':{
 'Two pair+':B,'Underpair':M,'Top pair':M,'Second pair':B,'Third pair':M,'Weak pocket pair':M,'OESD':B,'Gutshot':B,'BDFD':X,'Air':M},
'BBx':{
 'Two pair+':B,'Overpair':B,'Underpair':B,'Top pair':B,'Second pair':M,'Third pair':M,'Weak pocket pair':M,'OESD':B,'Gutshot':B,'BDFD':B,'Air':B},
'K[9-2]x':{
 'Two pair+':B,'Overpair':B,'Underpair':M,'Top pair':B,'Second pair':B,'Third pair':B,'Weak pocket pair':B,'OESD':B,'Gutshot':B,'BDFD':M,'Air':M},
'[Q-8]x':{
 'Two pair+':B,'Overpair':M,'Underpair':M,'Top pair':M,'Second pair':B,'Third pair':M,'Weak pocket pair':M,'OESD':B,'Gutshot':B,'BDFD':M,'2 overcards':M,'Air':M},
'[7-4]x':{
 'Two pair+':M,'Overpair':M,'Underpair':X,'Top pair':M,'Second pair':M,'Third pair':M,'Weak pocket pair':X,'OESD':M,'Gutshot':X,'BDFD':X,'2 overcards':X,'Air':X},
}
QP={B:1.,M:.5,X:0.}
p=sorted(glob.glob('datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-*.csv'))[-1]
a=defaultdict(lambda:[0.,0.,0.,0.]); TW=TB=TA=TL=0.
with open(p,encoding='utf-8-sig',newline='') as fh:
    for x in csv.DictReader(fh):
        fx=features(x['board'],x['combo']); k=bc(fx); c=cat(fx); w=f(x['reach_probability'])
        q=QP[RULE[k][c]]; bf=f(x['bet_frequency']); lb=f(x['loss_if_bet_utg']); lx=f(x['loss_if_check_utg'])
        z=a[k]; z[0]+=w; z[1]+=w*bf; z[2]+=w*q; z[3]+=w*(q*lb+(1-q)*lx)
        TW+=w; TB+=w*bf; TA+=w*q; TL+=w*(q*lb+(1-q)*lx)
print('HUMAN_CANDIDATE',p)
for k in BCS:
    w,t,q,l=a[k]; print(k,'solver',round(100*t/w,2),'human',round(100*q/w,2),'delta',round(100*(q-t)/w,2),'loss',round(l/w,5))
print('ALL solver',round(100*TB/TW,2),'human',round(100*TA/TW,2),'delta',round(100*(TA-TB)/TW,2),'loss',round(TL/TW,5))
