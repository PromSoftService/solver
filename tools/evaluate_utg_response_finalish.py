#!/usr/bin/env python3
import json
import analyze_rng002_utg_response as u
import analyze_rng002_btn_followups as a

def P(A): return {q:float(q==A) for q in 'FCR'}
def mix(F=0.,R=0.): return {'F':F,'R':R,'C':1-F-R}
RAISE_POOL={'Two pair+','Overpair','Top pair','OESD','Gutshot'}

def rule(c,h, qfold=.75, lfold=.80, bbfold=.25, at_bdfd_fold=.50, low_raise=.50, mid_raise=1.0):
    # Fold layer.
    if c=='A[K-J]x':
        if h in ('Air','BDFD 0OC','Underpair 9-'): return P('F')
    elif c=='A[T-2]x':
        if h=='Air': return P('F')
        if h=='BDFD 0OC': return mix(F=at_bdfd_fold)
    elif c=='BBx':
        if h in ('Air','BDFD 0OC','BDFD 1OC','X-high 1OC'): return P('F')
        if h=='Underpair 9-': return mix(F=bbfold)
    elif c=='K[9-2]x':
        if h in ('Air','X-high 1OC'): return P('F')
    elif c=='[Q-8]x':
        if h in ('Air','X-high 1OC','BDFD 0OC'): return P('F')
        if h=='X-high 2OC': return mix(F=qfold)
    elif c=='[7-4]x':
        if h in ('Air','X-high 1OC','BDFD 0OC'): return P('F')
        if h=='X-high 2OC': return mix(F=lfold)
    # Raise layer.
    if c=='A[K-J]x': return P('C')
    if c in ('A[T-2]x','BBx'):
        return mix(R=mid_raise) if h=='Two pair+' else P('C')
    if h in RAISE_POOL:
        return mix(R=low_raise)
    return P('C')

def eval_cells(cc,fn):
    by={}; T={k:0. for k in ('w','reg','sF','sC','sR','cF','cC','cR')}
    for c,hs in cc.items():
        z={k:0. for k in T}
        for h,v in hs.items():
            p=fn(c,h); w=v['w']; z['w']+=w
            for A in 'FCR': z['s'+A]+=w*v[A]; z['c'+A]+=w*p[A]
            z['reg']+=w*sum(p[A]*v['l'+A] for A in 'FCR')
        W=z['w']; by[c]={'w':W,'reg':z['reg']/W}
        for A in 'FCR': by[c]['s'+A]=z['s'+A]/W; by[c]['c'+A]=z['c'+A]/W
        for k in T:T[k]+=z[k]
    W=T['w']; ov={'reg':T['reg']/W}
    for A in 'FCR':ov['s'+A]=T['s'+A]/W;ov['c'+A]=T['c'+A]/W
    return {'by':by,'overall':ov}

def main():
    p,rows=u.load(); cc=u.cells(rows,'b6')
    variants={
      'preferred': lambda c,h: rule(c,h),
      'low_raise_40': lambda c,h: rule(c,h,low_raise=.40),
      'low_raise_60': lambda c,h: rule(c,h,low_raise=.60),
      'mid_raise_50': lambda c,h: rule(c,h,mid_raise=.50),
      'no_mid_raise': lambda c,h: rule(c,h,mid_raise=0),
      'q50_l75': lambda c,h: rule(c,h,qfold=.50,lfold=.75),
      'q75_l75': lambda c,h: rule(c,h,qfold=.75,lfold=.75),
      'det_folds': lambda c,h: rule(c,h,qfold=1,lfold=1,bbfold=0,at_bdfd_fold=1),
    }
    out={k:eval_cells(cc,v) for k,v in variants.items()}
    print('UTG_RESPONSE_FINALISH_BEGIN');print(json.dumps(a.rnd(out),ensure_ascii=False,separators=(',',':')));print('UTG_RESPONSE_FINALISH_END')
if __name__=='__main__':main()
