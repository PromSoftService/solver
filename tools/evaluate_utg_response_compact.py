#!/usr/bin/env python3
import itertools, json
from collections import defaultdict
import analyze_rng002_utg_response as u
import analyze_rng002_btn_followups as a


def P(A): return {q: float(q == A) for q in 'FCR'}
def mix(F=0., R=0.): return {'F': F, 'C': 1.0 - F - R, 'R': R}


def g4(x):
    c=x['b6']
    if c=='A[K-J]x': return 'A[K-J]x'
    if c in ('A[T-2]x','BBx'): return 'A[T-2]x+BBx'
    if c=='K[9-2]x': return 'K[9-2]x'
    return '[Q-8]x+[7-4]x'


def g3(x):
    c=x['b6']
    if c=='A[K-J]x': return 'A[K-J]x'
    if c in ('A[T-2]x','BBx'): return 'A[T-2]x+BBx'
    return 'K-low'


def build_cells(rows,group):
    d=defaultdict(lambda:defaultdict(float))
    for x in rows:
        z=d[(group(x),x['detail'])]; w=x['w']; z['w']+=w
        for q in 'FCR': z[q]+=w*x[q]; z['l'+q]+=w*x['l'+q]
    out={}
    for (c,h),z in d.items():
        W=z['w']; out.setdefault(c,{})[h]={'w':W}
        for q in 'FCR': out[c][h][q]=z[q]/W; out[c][h]['l'+q]=z['l'+q]/W
    return out


def agg_cells(cc):
    out={}
    for c,hs in cc.items():
        W=sum(v['w'] for v in hs.values()); q={'w':W}
        for a in 'FCR': q[a]=sum(v['w']*v[a] for v in hs.values())/W
        out[c]=q
    return out


def eval_cells(cc, rule):
    by={}; tot=defaultdict(float)
    for c,hs in cc.items():
        z=defaultdict(float)
        for h,v in hs.items():
            p=rule(c,h); w=v['w']; z['w']+=w
            for q in 'FCR': z['s'+q]+=w*v[q]; z['c'+q]+=w*p[q]
            z['reg']+=w*sum(p[q]*v['l'+q] for q in 'FCR')
        W=z['w']; by[c]={'w':W,'reg':z['reg']/W}
        for q in 'FCR': by[c]['solver'+q]=z['s'+q]/W; by[c]['cand'+q]=z['c'+q]/W
        for k,v in z.items(): tot[k]+=v
    W=tot['w']; ov={'reg':tot['reg']/W}
    for q in 'FCR': ov['solver'+q]=tot['s'+q]/W; ov['cand'+q]=tot['c'+q]/W
    return {'by':by,'overall':ov}


def rule4(mb0=.5,mb1=1.,mu9=0.,x2=.5,b1=0.,mr=.25,kr=.5,qr=.5):
    def r(c,h):
        if c=='A[K-J]x':
            return P('F') if h in ('Air','BDFD 0OC','Underpair 9-') else P('C')
        if c=='A[T-2]x+BBx':
            if h in ('Air','X-high 1OC'): return P('F')
            if h=='BDFD 0OC': return mix(F=mb0)
            if h=='BDFD 1OC': return mix(F=mb1)
            if h=='Underpair 9-': return mix(F=mu9)
            if h in ('Two pair+','OESD'): return mix(R=mr)
            return P('C')
        if c=='K[9-2]x':
            if h in ('Air','X-high 1OC'): return P('F')
            if h in ('Two pair+','OESD','Gutshot','Top pair','Overpair'): return mix(R=kr)
            return P('C')
        if h in ('Air','X-high 1OC','BDFD 0OC'): return P('F')
        if h=='X-high 2OC': return mix(F=x2)
        if h=='BDFD 1OC': return mix(F=b1)
        if h in ('Two pair+','OESD'): return mix(R=qr)
        return P('C')
    return r


def rule3(mb0=.5,mb1=1.,mu9=0.,x2=.5,lb0=.5,lb1=0.,mr=.25,lr=.5):
    def r(c,h):
        if c=='A[K-J]x':
            return P('F') if h in ('Air','BDFD 0OC','Underpair 9-') else P('C')
        if c=='A[T-2]x+BBx':
            if h in ('Air','X-high 1OC'): return P('F')
            if h=='BDFD 0OC': return mix(F=mb0)
            if h=='BDFD 1OC': return mix(F=mb1)
            if h=='Underpair 9-': return mix(F=mu9)
            if h in ('Two pair+','OESD'): return mix(R=mr)
            return P('C')
        if h in ('Air','X-high 1OC'): return P('F')
        if h=='BDFD 0OC': return mix(F=lb0)
        if h=='BDFD 1OC': return mix(F=lb1)
        if h=='X-high 2OC': return mix(F=x2)
        if h in ('Two pair+','OESD','Gutshot','Top pair','Overpair'): return mix(R=lr)
        return P('C')
    return r


def rank(cc, variants):
    out=[]
    for name,fn in variants:
        m=eval_cells(cc,fn); o=m['overall']; err=sum(abs(o['cand'+q]-o['solver'+q]) for q in 'FCR')
        out.append((o['reg'],err,name,m))
    out.sort(key=lambda z:(z[0],z[1]))
    return [{'name':n,'metrics':m} for _,_,n,m in out[:12]]


def main():
    p,rows=u.load(); c4=build_cells(rows,g4); c3=build_cells(rows,g3)
    v4=[]
    for vals in itertools.product((0,.5,1),(0,.5,1),(0,.25),(0,.5,.75,1),(0,.5),(0,.25,.5),(0,.5,1),(0,.5,1)):
        v4.append(('_'.join(map(str,vals)),rule4(*vals)))
    v3=[]
    for vals in itertools.product((0,.5,1),(0,.5,1),(0,.25),(0,.5,.75,1),(0,.5,1),(0,.5),(0,.25,.5),(0,.5,1)):
        v3.append(('_'.join(map(str,vals)),rule3(*vals)))
    result={
      'dataset':p,'solver_g4':agg_cells(c4),'solver_g3':agg_cells(c3),
      'g4_top':rank(c4,v4),'g3_top':rank(c3,v3),
      'named':{
        'g4_simple':eval_cells(c4,rule4(.5,1,0,.5,0,.25,.5,.5)),
        'g4_deterministic_folds':eval_cells(c4,rule4(1,1,0,1,0,.25,.5,.5)),
        'g4_minraise':eval_cells(c4,rule4(.5,1,0,.5,0,0,.5,.5)),
        'g3_simple':eval_cells(c3,rule3(.5,1,0,.5,.5,0,.25,.5)),
      }
    }
    print('UTG_RESPONSE_COMPACT_BEGIN');print(json.dumps(a.rnd(result),ensure_ascii=False,separators=(',',':')));print('UTG_RESPONSE_COMPACT_END')

if __name__=='__main__': main()
