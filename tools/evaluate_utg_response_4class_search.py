#!/usr/bin/env python3
import itertools,json
from collections import defaultdict
import analyze_rng002_utg_response as u
import analyze_rng002_btn_followups as a

def P(A):return {q:float(q==A) for q in 'FCR'}
def mix(F=0.,R=0.):return {'F':F,'C':1-F-R,'R':R}
def grp(x):
 c=x['b6']
 if c=='A[K-J]x':return 'HIGH'
 if c in ('A[T-2]x','BBx'):return 'MID'
 if c=='K[9-2]x':return 'K'
 return 'QLOW'
def cells(rows):
 d=defaultdict(lambda:defaultdict(float))
 for x in rows:
  z=d[(grp(x),x['detail'])];w=x['w'];z['w']+=w
  for q in 'FCR':z[q]+=w*x[q];z['l'+q]+=w*x['l'+q]
 o={}
 for (g,h),z in d.items():
  W=z['w'];v={'w':W}
  for q in 'FCR':v[q]=z[q]/W;v['l'+q]=z['l'+q]/W
  o.setdefault(g,{})[h]=v
 return o
def ev(hs,rule):
 W=sum(v['w'] for v in hs.values());S={q:0. for q in 'FCR'};C={q:0. for q in 'FCR'};reg=0.
 for h,v in hs.items():
  p=rule(h);w=v['w']
  for q in 'FCR':S[q]+=w*v[q];C[q]+=w*p[q]
  reg+=w*sum(p[q]*v['l'+q] for q in 'FCR')
 S={q:S[q]/W for q in 'FCR'};C={q:C[q]/W for q in 'FCR'}
 return {'w':W,'reg':reg/W,'solver':S,'cand':C,'maxerr':max(abs(C[q]-S[q]) for q in 'FCR')}
def high(h):return P('F') if h in ('Air','BDFD 0OC','Underpair 9-') else P('C')
def mid(h):
 if h in ('Air','X-high 1OC','BDFD 0OC','BDFD 1OC'):return P('F')
 if h=='Two pair+':return P('R')
 return P('C')
KPOOLS={
 'BROAD':{'Two pair+','OESD','Gutshot','Top pair','Overpair','Second pair','Third pair'},
 'NO23':{'Two pair+','OESD','Gutshot','Top pair','Overpair'},
 'DRAWS_VALUE':{'Two pair+','OESD','Gutshot'},
 'TP_OESD':{'Two pair+','OESD'},}
QPOOLS={
 'TP_OESD_TOP_OVP':{'Two pair+','OESD','Top pair','Overpair'},
 'BROAD':{'Two pair+','OESD','Gutshot','Top pair','Overpair'},
 'TP_OESD_GS':{'Two pair+','OESD','Gutshot'},
 'TP_OESD':{'Two pair+','OESD'},}
def krule(b0,b1,pool,rr):
 rp=KPOOLS[pool]
 def r(h):
  if h in ('Air','X-high 1OC'):return P('F')
  if h=='BDFD 0OC':return mix(F=b0)
  if h=='BDFD 1OC':return mix(F=b1)
  if h in rp:return mix(R=rr)
  return P('C')
 return r
def qrule(x2,b0,b1,pool,rr):
 rp=QPOOLS[pool]
 def r(h):
  if h in ('Air','X-high 1OC'):return P('F')
  if h=='X-high 2OC':return mix(F=x2)
  if h=='BDFD 0OC':return mix(F=b0)
  if h=='BDFD 1OC':return mix(F=b1)
  if h in rp:return mix(R=rr)
  return P('C')
 return r
def search(hs,kind,tol=.03):
 out=[]
 if kind=='K':
  it=itertools.product((0,.5,1),(0,.25,.5,1),KPOOLS,(0,.25,.4,.5,.6,.75,1))
  for b0,b1,pool,rr in it:
   m=ev(hs,krule(b0,b1,pool,rr));
   if m['maxerr']<=tol:out.append((m['reg'],{'bdfd0_fold':b0,'bdfd1_fold':b1,'raise_pool':pool,'raise_rate':rr},m))
 else:
  it=itertools.product((0,.25,.5,.75,1),(0,.5,1),(0,.25,.5,1),QPOOLS,(0,.25,.4,.5,.6,.75,1))
  for x2,b0,b1,pool,rr in it:
   m=ev(hs,qrule(x2,b0,b1,pool,rr));
   if m['maxerr']<=tol:out.append((m['reg'],{'xhigh2_fold':x2,'bdfd0_fold':b0,'bdfd1_fold':b1,'raise_pool':pool,'raise_rate':rr},m))
 out.sort(key=lambda z:(z[0],z[2]['maxerr']));return [{'params':p,'metrics':m} for _,p,m in out[:10]]
def package(ms):
 W=sum(m['w'] for m in ms);o={'reg':sum(m['w']*m['reg'] for m in ms)/W}
 for q in 'FCR':
  o['solver'+q]=sum(m['w']*m['solver'][q] for m in ms)/W;o['cand'+q]=sum(m['w']*m['cand'][q] for m in ms)/W
 return o
def main():
 p,rows=u.load();cc=cells(rows);H=ev(cc['HIGH'],high);M=ev(cc['MID'],mid);out={'dataset':p,'high':H,'mid':M}
 for tol in (.03,.05,.075):
  ks=search(cc['K'],'K',tol);qs=search(cc['QLOW'],'Q',tol);z={'K':ks,'QLOW':qs}
  if ks and qs:z['package']=package([H,M,ks[0]['metrics'],qs[0]['metrics']])
  out[str(tol)]=z
 print('UTG_RESPONSE_4CLASS_BEGIN');print(json.dumps(a.rnd(out),ensure_ascii=False,separators=(',',':')));print('UTG_RESPONSE_4CLASS_END')
if __name__=='__main__':main()
