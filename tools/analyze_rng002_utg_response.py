#!/usr/bin/env python3
import csv,glob,json
from collections import defaultdict
import analyze_rng002_btn_followups as a
import analyze_rng002_btn_refine as r
import evaluate_btn_final_candidates as e

def load():
    p=sorted(glob.glob('datasets/DS__RNG002__CFG003__NOD006__BRD001__RUN-*.csv'))[-1]; out=[]
    with open(p,encoding='utf-8-sig',newline='') as fh:
      for x in csv.DictReader(fh):
        q={'board':x['board'],'combo':x['combo'],'w':a.f(x['reach_probability']),
           'F':a.f(x['fold_frequency']),'C':a.f(x['call_frequency']),'R':a.f(x['raise_frequency']),
           'lF':a.f(x['loss_if_fold_utg']),'lC':a.f(x['loss_if_call_utg']),'lR':a.f(x['loss_if_raise_utg'])}
        q['b4']=a.board4(q['board']); q['b6']=a.board6(q['board']); q['hb']=a.hand_bucket(q['board'],q['combo'])
        q['b3']='AKx' if q['b4']=='AKx' else '[T-4]x' if q['b4']=='[T-4]x' else '[K/A/Q/J]xx'
        q['detail']=r.detail_bucket(q); out.append(q)
    return p,out

def agg(rows,key):
    d=defaultdict(lambda:[0.,0.,0.,0.])
    for x in rows:
      z=d[x[key]]; w=x['w']; z[0]+=w; z[1]+=w*x['F']; z[2]+=w*x['C']; z[3]+=w*x['R']
    return {k:{'w':z[0],'F':z[1]/z[0],'C':z[2]/z[0],'R':z[3]/z[0]} for k,z in d.items()}

def cells(rows,key):
    d=defaultdict(lambda:[0.]*7)
    for x in rows:
      z=d[(x[key],x['detail'])]; w=x['w']; z[0]+=w
      for i,A in enumerate('FCR',1): z[i]+=w*x[A]; z[i+3]+=w*x['l'+A]
    o={}
    for (c,h),z in d.items():
      w=z[0]; o.setdefault(c,{})[h]={'w':w,'F':z[1]/w,'C':z[2]/w,'R':z[3]/w,'lF':z[4]/w,'lC':z[5]/w,'lR':z[6]/w}
    return o

def ev(rows,key,rule):
    d=defaultdict(lambda:defaultdict(float)); t=defaultdict(float)
    for x in rows:
      p=rule(x); z=d[x[key]]; w=x['w']; z['w']+=w
      for A in 'FCR': z['s'+A]+=w*x[A]; z['c'+A]+=w*p[A]
      z['reg']+=w*sum(p[A]*x['l'+A] for A in 'FCR')
    out={}
    for c,z in d.items():
      w=z['w']; q={'w':w,'reg':z['reg']/w}
      for A in 'FCR': q['s'+A]=z['s'+A]/w; q['c'+A]=z['c'+A]/w
      out[c]=q; t['w']+=w; t['reg']+=z['reg']
      for A in 'FCR': t['s'+A]+=z['s'+A]; t['c'+A]+=z['c'+A]
    W=t['w']; ov={'reg':t['reg']/W}
    for A in 'FCR': ov['s'+A]=t['s'+A]/W; ov['c'+A]=t['c'+A]/W
    return {'by':out,'overall':ov}

def pure(A): return {q:float(q==A) for q in 'FCR'}
def noraise(x):
    d=x['detail']; c=x['b6']
    if d=='Air' or d=='BDFD 0OC' or d=='X-high 1OC': return pure('F')
    if d=='Underpair 9-' and c=='A[K-J]x': return pure('F')
    return pure('C')

def main():
    p,x=load(); result={'dataset':p,'rows':len(x),'b6':agg(x,'b6'),'b4':agg(x,'b4'),'b3':agg(x,'b3'),
      'cells6':cells(x,'b6'),'cells3':cells(x,'b3'),
      'BB33_transfer':ev(x,'b6',e.response_same_as_bb33),'noraise_baseline':ev(x,'b6',noraise)}
    print('UTG_RESPONSE_BEGIN'); print(json.dumps(a.rnd(result),ensure_ascii=False,separators=(',',':'))); print('UTG_RESPONSE_END')
if __name__=='__main__': main()
