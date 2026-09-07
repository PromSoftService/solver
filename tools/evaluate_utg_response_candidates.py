#!/usr/bin/env python3
import itertools,json
import analyze_rng002_utg_response as u
import analyze_rng002_btn_followups as a

def P(A): return {q:float(q==A) for q in 'FCR'}
def mix(F=0.,R=0.): return {'F':F,'R':R,'C':1-F-R}

def make_rule(x2q=.5,x2l=.75,midR=.25,lowD=.5,lowW=.25):
  def rule(c,h):
    if c=='A[K-J]x':
      if h in ('Air','BDFD 0OC','Underpair 9-'): return P('F')
    elif c in ('A[T-2]x','BBx'):
      if h in ('Air','BDFD 0OC','BDFD 1OC','X-high 1OC'): return P('F')
    else:
      if h in ('Air','BDFD 0OC','X-high 1OC'): return P('F')
      if h=='X-high 2OC': return mix(x2q if c=='[Q-8]x' else x2l if c=='[7-4]x' else 0.)
    if c=='A[K-J]x': return P('C')
    if c in ('A[T-2]x','BBx'):
      return mix(R=midR) if h=='Two pair+' else P('C')
    if h=='Two pair+': return P('R')
    if h=='OESD': return mix(R=lowD)
    if h in ('Gutshot','Overpair','Top pair','BDFD 2OC'): return mix(R=lowW)
    return P('C')
  return rule

def eval_cells(cc,solver,rule):
  by={}; tot={k:0. for k in ('w','reg','sF','sC','sR','cF','cC','cR')}
  for c,hs in cc.items():
    z={k:0. for k in tot}
    for h,v in hs.items():
      w=v['w']; p=rule(c,h); z['w']+=w
      for A in 'FCR': z['s'+A]+=w*v[A]; z['c'+A]+=w*p[A]
      z['reg']+=w*sum(p[A]*v['l'+A] for A in 'FCR')
    W=z['w']; by[c]={'w':W,'reg':z['reg']/W}
    for A in 'FCR': by[c]['s'+A]=z['s'+A]/W; by[c]['c'+A]=z['c'+A]/W
    for k in tot: tot[k]+=z[k]
  W=tot['w']; ov={'reg':tot['reg']/W}
  for A in 'FCR': ov['s'+A]=tot['s'+A]/W; ov['c'+A]=tot['c'+A]/W
  return {'by':by,'overall':ov}

def score(m):
  o=m['overall']; return o['reg'],sum(abs(o['c'+q]-o['s'+q]) for q in 'FCR')

def main():
  p,rows=u.load(); cc=u.cells(rows,'b6'); solver=u.agg(rows,'b6'); cand={}
  cand['simple']=eval_cells(cc,solver,make_rule())
  cand['minimal_raise']=eval_cells(cc,solver,make_rule(.5,.75,0.,.5,0.))
  cand['no_random_fold']=eval_cells(cc,solver,make_rule(1.,1.,.25,.5,.25))
  best=[]
  for xq,xl,mr,ld,lw in itertools.product((0,.5,.75,1),(0,.5,.75,1),(0,.25,.5),(0,.5,1),(0,.25,.5)):
    m=eval_cells(cc,solver,make_rule(xq,xl,mr,ld,lw)); o=m['overall']
    if max(abs(o['c'+q]-o['s'+q]) for q in 'FCR')>.06: continue
    best.append((score(m),[xq,xl,mr,ld,lw],m))
  best.sort(key=lambda z:z[0]); cand['best_grid']=[{'params':z[1],'metrics':z[2]} for z in best[:10]]
  print('UTG_RESPONSE_CANDIDATES_BEGIN');print(json.dumps(a.rnd(cand),ensure_ascii=False,separators=(',',':')));print('UTG_RESPONSE_CANDIDATES_END')
if __name__=='__main__':main()
