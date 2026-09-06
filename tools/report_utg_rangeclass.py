#!/usr/bin/env python3
import csv,glob
from collections import defaultdict
from analyze_cfg002_compare import features
BCS=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')
def f(s): return float(str(s).replace(',','.'))
def bc(r):
 x=r['fx']; h,m=x['top'],x['mid']
 if h==14:return 'A[K-J]x' if m>=11 else 'A[T-2]x'
 if sum(v>=10 for v in (x['top'],x['mid'],x['low']))>=2:return 'BBx'
 if h==13:return 'K[9-2]x'
 if 8<=h<=12:return '[Q-8]x'
 return '[7-4]x'
p=sorted(glob.glob('datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-*.csv'))[-1]
a=defaultdict(lambda:[0,0,0,0,0])
with open(p,encoding='utf-8-sig',newline='') as fh:
 for x in csv.DictReader(fh):
  r={'fx':features(x['board'],x['combo'])}; k=bc(r); w=f(x['reach_probability']); a[k][0]+=w; a[k][1]+=w*f(x['check_frequency']); a[k][2]+=w*f(x['bet_frequency']); a[k][3]+=w*f(x['loss_if_check_utg']); a[k][4]+=w*f(x['loss_if_bet_utg'])
print('RANGE_CLASS')
for k in BCS:
 w,x,b,lx,lb=a[k]; print(k,'XB',round(100*x/w,1),round(100*b/w,1),'lossX',round(lx/w,4),'lossB',round(lb/w,4),'w',round(w,1))
