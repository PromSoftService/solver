#!/usr/bin/env python3
from collections import defaultdict
from analyze_cfg002_compare import load,newagg,add,finish,RCHR

def p(x): return round(100*x,1)
def emit(k,z): print(k,'FCR',p(z['fold']),p(z['call']),p(z['raise']),'loss',round(z['loss_F'],4),round(z['loss_C'],4),round(z['loss_R'],4),'best',z['best_pure'],round(z['best_loss'],4),'w',round(z['weight'],1))
def main():
 _,rows=load('CFG002'); d=defaultdict(newagg)
 for r in rows:
  if r['fx']['made'] not in ('High underpair','Weak pocket pair'): continue
  pr=r['fx']['pocket_rank']; mid=r['fx']['mid']
  add(d[(r['bc'],r['fx']['made'],RCHR[mid],RCHR[pr],r['fx']['sd'] or 'noSD')],r)
 print('UNDERPAIR_BEGIN')
 for k,a in d.items():
  z=finish(a)
  if z['weight']>=100: emit(k,z)
 print('UNDERPAIR_END')
if __name__=='__main__': main()
