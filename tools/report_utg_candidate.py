#!/usr/bin/env python3
import csv,glob
from collections import defaultdict
from analyze_cfg002_compare import features
BCS=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')
def f(s):return float(str(s).replace(',','.'))
def bc(fx):
 h,m=fx['top'],fx['mid']
 if h==14:return 'A[K-J]x' if m>=11 else 'A[T-2]x'
 if sum(v>=10 for v in (fx['top'],fx['mid'],fx['low']))>=2:return 'BBx'
 if h==13:return 'K[9-2]x'
 if 8<=h<=12:return '[Q-8]x'
 return '[7-4]x'
def act(k,fx):
 if k in ('A[K-J]x','BBx'): return 'B'
 if k=='[7-4]x': return 'X'
 if k=='K[9-2]x': return 'X' if fx['made']=='Top pair' else 'B'
 if k=='A[T-2]x':
  if fx['made']=='Top pair': return 'X'
  if fx['made']=='High card' and fx['sd'] is None and not fx['bdfd']: return 'X'
  return 'B'
 if k=='[Q-8]x':
  if fx['made']=='High card' and fx['sd'] is None and (fx['two_over'] or fx['bdfd']): return 'X'
  return 'B'
 raise AssertionError(k)
p=sorted(glob.glob('datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-*.csv'))[-1]
a=defaultdict(lambda:[0,0,0,0])
with open(p,encoding='utf-8-sig',newline='') as fh:
 for x in csv.DictReader(fh):
  fx=features(x['board'],x['combo']); k=bc(fx); w=f(x['reach_probability']); z=act(k,fx); a[k][0]+=w; a[k][1]+=w*(z=='B'); a[k][2]+=w*(f(x['loss_if_bet_utg']) if z=='B' else f(x['loss_if_check_utg'])); a[k][3]+=w*(min(f(x['loss_if_bet_utg']),f(x['loss_if_check_utg'])))
print('CANDIDATE')
TW=TL=0
for k in BCS:
 w,b,l,best=a[k]; print(k,'bet',round(100*b/w,1),'selected_loss',round(l/w,4),'best_pure_per_combo_floor',round(best/w,4),'w',round(w,1)); TW+=w;TL+=l
print('ALL selected_loss',round(TL/TW,4))
