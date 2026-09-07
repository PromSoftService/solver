#!/usr/bin/env python3
import itertools, json
from collections import defaultdict
import analyze_rng002_utg_response as u
import analyze_rng002_btn_followups as a


def P(A): return {q: float(q == A) for q in 'FCR'}
def mix(F=0., R=0.): return {'F': F, 'C': 1.0 - F - R, 'R': R}


def g4(x):
    c = x['b6']
    if c == 'A[K-J]x': return 'A[K-J]x'
    if c in ('A[T-2]x', 'BBx'): return 'A[T-2]x+BBx'
    if c == 'K[9-2]x': return 'K[9-2]x'
    return '[Q-8]x+[7-4]x'


def g3(x):
    c = x['b6']
    if c == 'A[K-J]x': return 'A[K-J]x'
    if c in ('A[T-2]x', 'BBx'): return 'A[T-2]x+BBx'
    return 'K-low'


def agg(rows, group):
    d = defaultdict(lambda: defaultdict(float))
    for x in rows:
        z = d[group(x)]; w = x['w']; z['w'] += w
        for q in 'FCR': z[q] += w * x[q]
    return {c: {'w': z['w'], **{q: z[q]/z['w'] for q in 'FCR'}} for c,z in d.items()}


def eval_rows(rows, group, rule):
    d = defaultdict(lambda: defaultdict(float)); tot = defaultdict(float)
    for x in rows:
        c = group(x); p = rule(x); z = d[c]; w = x['w']; z['w'] += w
        for q in 'FCR':
            z['s'+q] += w*x[q]; z['c'+q] += w*p[q]
        z['reg'] += w*sum(p[q]*x['l'+q] for q in 'FCR')
    out = {}
    for c,z in d.items():
        W=z['w']; out[c]={'w':W,'reg':z['reg']/W}
        for q in 'FCR':
            out[c]['solver'+q]=z['s'+q]/W; out[c]['cand'+q]=z['c'+q]/W
        tot['w']+=W; tot['reg']+=z['reg']
        for q in 'FCR': tot['s'+q]+=z['s'+q]; tot['c'+q]+=z['c'+q]
    W=tot['w']; ov={'reg':tot['reg']/W}
    for q in 'FCR': ov['solver'+q]=tot['s'+q]/W; ov['cand'+q]=tot['c'+q]/W
    return {'by':out,'overall':ov}


def rule4(mid_bdfd0_fold=.5, mid_bdfd1_fold=1., mid_under9_fold=0.,
          qlow_x2_fold=.5, qlow_bdfd1_fold=0.,
          mid_raise=.25, k_raise=.5, qlow_raise=.5):
    def rule(x):
        c=g4(x); h=x['detail']
        if c=='A[K-J]x':
            if h in ('Air','BDFD 0OC','Underpair 9-'): return P('F')
            return P('C')
        if c=='A[T-2]x+BBx':
            if h in ('Air','X-high 1OC'): return P('F')
            if h=='BDFD 0OC': return mix(F=mid_bdfd0_fold)
            if h=='BDFD 1OC': return mix(F=mid_bdfd1_fold)
            if h=='Underpair 9-': return mix(F=mid_under9_fold)
            if h in ('Two pair+','OESD'): return mix(R=mid_raise)
            return P('C')
        if c=='K[9-2]x':
            if h in ('Air','X-high 1OC'): return P('F')
            if h in ('Two pair+','OESD','Gutshot','Top pair','Overpair'): return mix(R=k_raise)
            return P('C')
        # Q8 + 7-4
        if h in ('Air','X-high 1OC','BDFD 0OC'): return P('F')
        if h=='X-high 2OC': return mix(F=qlow_x2_fold)
        if h=='BDFD 1OC': return mix(F=qlow_bdfd1_fold)
        if h in ('Two pair+','OESD'): return mix(R=qlow_raise)
        return P('C')
    return rule


def rule3(mid_bdfd0_fold=.5, mid_bdfd1_fold=1., mid_under9_fold=0.,
          low_x2_fold=.5, low_bdfd0_fold=.5, low_bdfd1_fold=0.,
          mid_raise=.25, low_raise=.5):
    def rule(x):
        c=g3(x); h=x['detail']
        if c=='A[K-J]x':
            if h in ('Air','BDFD 0OC','Underpair 9-'): return P('F')
            return P('C')
        if c=='A[T-2]x+BBx':
            if h in ('Air','X-high 1OC'): return P('F')
            if h=='BDFD 0OC': return mix(F=mid_bdfd0_fold)
            if h=='BDFD 1OC': return mix(F=mid_bdfd1_fold)
            if h=='Underpair 9-': return mix(F=mid_under9_fold)
            if h in ('Two pair+','OESD'): return mix(R=mid_raise)
            return P('C')
        if h in ('Air','X-high 1OC'): return P('F')
        if h=='BDFD 0OC': return mix(F=low_bdfd0_fold)
        if h=='BDFD 1OC': return mix(F=low_bdfd1_fold)
        if h=='X-high 2OC': return mix(F=low_x2_fold)
        if h in ('Two pair+','OESD','Gutshot','Top pair','Overpair'): return mix(R=low_raise)
        return P('C')
    return rule


def rank_variants(rows, group, variants):
    out=[]
    for name,fn in variants:
        m=eval_rows(rows,group,fn); o=m['overall']
        err=sum(abs(o['cand'+q]-o['solver'+q]) for q in 'FCR')
        out.append((o['reg'],err,name,m))
    out.sort(key=lambda z:(z[0],z[1]))
    return [{'name':n,'metrics':m} for _,_,n,m in out]


def main():
    p,rows=u.load()
    v4=[]
    for mb0,mb1,mu9,x2,b1,mr,kr,qr in itertools.product(
        (0,.5,1),(0,.5,1),(0,.25), (0,.5,.75,1),(0,.5), (0,.25,.5),(0,.5,1),(0,.5,1)):
        name=f'mb0{mb0}_mb1{mb1}_mu9{mu9}_x2{x2}_b1{b1}_mr{mr}_kr{kr}_qr{qr}'
        v4.append((name,rule4(mb0,mb1,mu9,x2,b1,mr,kr,qr)))
    v3=[]
    for mb0,mb1,mu9,x2,lb0,lb1,mr,lr in itertools.product(
        (0,.5,1),(0,.5,1),(0,.25),(0,.5,.75,1),(0,.5,1),(0,.5),(0,.25,.5),(0,.5,1)):
        name=f'mb0{mb0}_mb1{mb1}_mu9{mu9}_x2{x2}_lb0{lb0}_lb1{lb1}_mr{mr}_lr{lr}'
        v3.append((name,rule3(mb0,mb1,mu9,x2,lb0,lb1,mr,lr)))
    result={
      'dataset':p,
      'solver_g4':agg(rows,g4),
      'solver_g3':agg(rows,g3),
      'g4_top':rank_variants(rows,g4,v4)[:12],
      'g3_top':rank_variants(rows,g3,v3)[:12],
      'named':{
        'g4_simple':eval_rows(rows,g4,rule4(.5,1,0,.5,0,.25,.5,.5)),
        'g4_deterministic_folds':eval_rows(rows,g4,rule4(1,1,0,1,0,.25,.5,.5)),
        'g4_minraise':eval_rows(rows,g4,rule4(.5,1,0,.5,0,0,.5,.5)),
        'g3_simple':eval_rows(rows,g3,rule3(.5,1,0,.5,.5,0,.25,.5)),
      }
    }
    print('UTG_RESPONSE_COMPACT_BEGIN')
    print(json.dumps(a.rnd(result),ensure_ascii=False,separators=(',',':')))
    print('UTG_RESPONSE_COMPACT_END')

if __name__=='__main__': main()
