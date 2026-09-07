#!/usr/bin/env python3
import json
from collections import defaultdict
import analyze_rng002_btn_followups as a
import analyze_rng002_btn_refine as r


STAB_FAMILIAR_POOL={'Two pair+','Overpair','Top pair','Second pair','OESD','Gutshot','BDFD','X-high'}


def stab_rule(x):
    c=x['b4'];h=x['hb']
    if c=='[T-4]x': return .75
    pool={'Two pair+','Overpair','Top pair','Second pair','OESD','Gutshot','BDFD'}
    if h not in pool:return 0.
    if c=='AKx' and h=='BDFD':return 0.
    if c=='AKx':return .75
    return 1.

def stab_same6_rule(x):
    if x['hb'] not in STAB_FAMILIAR_POOL:return 0.
    rates={'A[K-J]x':.70,'A[T-2]x':.85,'BBx':.75,'K[9-2]x':.80,'[Q-8]x':.90,'[7-4]x':.85}
    return rates[x['b6']]

def stab_same6_tens_rule(x):
    # Same familiar six classes + same hand pool, with only 70/80/90% randomizers.
    if x['hb'] not in STAB_FAMILIAR_POOL:return 0.
    rates={'A[K-J]x':.70,'A[T-2]x':.90,'BBx':.70,'K[9-2]x':.80,'[Q-8]x':.90,'[7-4]x':.90}
    return rates[x['b6']]

def eval_stab(rows, rule=stab_rule, class_key='b4', classes=None):
    if classes is None: classes=a.B4
    by={c:{'w':0.,'sb':0.,'cb':0.,'reg':0.} for c in classes}
    for x in rows:
        z=by[x[class_key]];w=x['w'];p=rule(x);z['w']+=w;z['sb']+=w*x['bet'];z['cb']+=w*p;z['reg']+=w*(p*x['lb']+(1-p)*x['lx'])
    out={};tot={'w':0.,'sb':0.,'cb':0.,'reg':0.}
    for c,z in by.items():
        w=z['w'];out[c]={'solver':z['sb']/w,'cand':z['cb']/w,'diff':(z['cb']-z['sb'])/w,'reg':z['reg']/w}
        for k in tot:tot[k]+=z[k]
    w=tot['w'];ov={'solver':tot['sb']/w,'cand':tot['cb']/w,'diff':(tot['cb']-tot['sb'])/w,'reg':tot['reg']/w}
    return {'by':out,'overall':ov}

def response_rule(x):
    c=x['b4'];hb=x['hb'];d=r.detail_bucket(x)
    pf=0.
    if hb=='Air':pf=1.
    elif c in ('AKx','Kxx','[A/Q/J]xx') and d=='BDFD 0OC':pf=1.
    elif c=='[A/Q/J]xx' and d=='BDFD 1OC':pf=.50
    elif d=='X-high 1OC':pf=1.
    elif c=='AKx' and d=='Underpair 9-':pf=.75
    if pf>0:return {'F':pf,'C':1-pf,'R':0.}
    pr=0.
    if c in ('AKx','Kxx') and hb=='Two pair+':pr=1.
    elif c=='[A/Q/J]xx' and hb in ('Two pair+','OESD','Gutshot'):pr=.40
    elif c=='[T-4]x' and hb in ('OESD','Gutshot'):pr=1.
    return {'F':0.,'C':1-pr,'R':pr}


def bdsd_paths(br,hr):
    u=set(br+hr); hole_contrib=set(hr)-set(br); n=0
    if not hole_contrib:return 0
    for w in a.STRAIGHTS:
        if len(w & u)==3 and len(w-u)==2 and (w & hole_contrib):n+=1
    return n

def response_same_as_bb33(x):
    b=a.bc(x['board']);h=a.hc(x['combo']);br=a.ranks(b);hr=a.ranks(h)
    top,mid,low=sorted(br,reverse=True)
    cnt=defaultdict(int)
    for v in br+hr:cnt[v]+=1
    if a.straight(br+hr):return {'F':0.,'C':0.,'R':1.}
    if max(cnt.values())>=3 or sum(v>=2 for v in cnt.values())>=2:return {'F':0.,'C':0.,'R':1.}
    if hr[0]==hr[1]:
        act='F' if hr[0]<mid and x['b6']=='A[K-J]x' else 'C'
        return {q:1. if q==act else 0. for q in 'FCR'}
    if any(v in br for v in hr):return {'F':0.,'C':1.,'R':0.}
    sd=a.sd_kind(br,hr);bd=a.bdfd(b,h);bdstraight=bdsd_paths(br,hr)>0;two_over=min(hr)>top
    hole=''.join(sorted((h[0][0],h[1][0]),key=lambda z:a.RANK[z],reverse=True))
    if two_over and (sd is not None or bd or bdstraight):return {'F':0.,'C':1.,'R':0.}
    if sd=='OESD':return {'F':0.,'C':0.,'R':1.}
    if sd=='Gutshot' and bd:return {'F':0.,'C':0.,'R':1.}
    if sd=='Gutshot':return {'F':0.,'C':1.,'R':0.}
    if hole in ('AK','AQ','AJ') and not bd and not bdstraight:return {'F':0.,'C':1.,'R':0.}
    if two_over and not bd and not bdstraight:
        act='F' if x['b6']=='[7-4]x' else 'C'
        return {q:1. if q==act else 0. for q in 'FCR'}
    return {'F':1.,'C':0.,'R':0.}


def eval_response_by6(rows,rule):
    by={c:{'w':0.,'sF':0.,'sC':0.,'sR':0.,'cF':0.,'cC':0.,'cR':0.,'reg':0.} for c in a.B6}
    for x in rows:
        p=rule(x);z=by[x['b6']];w=x['w'];z['w']+=w
        for q in 'FCR':z['s'+q]+=w*x[q];z['c'+q]+=w*p[q]
        z['reg']+=w*sum(p[q]*x['l'+q] for q in 'FCR')
    out={};tot=defaultdict(float)
    for c,z in by.items():
        w=z['w'];v={'w':w,'reg':z['reg']/w}
        for q in 'FCR':v['solver'+q]=z['s'+q]/w;v['cand'+q]=z['c'+q]/w;v['diff'+q]=v['cand'+q]-v['solver'+q]
        out[c]=v;tot['w']+=w;tot['reg']+=z['reg']
        for q in 'FCR':tot['s'+q]+=z['s'+q];tot['c'+q]+=z['c'+q]
    W=tot['w'];ov={'reg':tot['reg']/W}
    for q in 'FCR':ov['solver'+q]=tot['s'+q]/W;ov['cand'+q]=tot['c'+q]/W;ov['diff'+q]=ov['cand'+q]-ov['solver'+q]
    return {'by':out,'overall':ov}


def main():
    p4=a.latest('datasets/DS__RNG002__CFG003__NOD004__BRD001__RUN-*.csv');p5=a.latest('datasets/DS__RNG002__CFG003__NOD005__BRD001__RUN-*.csv')
    x4=a.load4(p4,'NOD004');x5=a.load4(p5,'NOD005')
    result={
      'NOD004_final':r.eval_response(x4,response_rule),
      'NOD004_same_as_BB33':eval_response_by6(x4,response_same_as_bb33),
      'NOD005_final':eval_stab(x5),
      'NOD005_same6_familiar_pool':eval_stab(x5,stab_same6_rule,'b6',a.B6),
      'NOD005_same6_tens':eval_stab(x5,stab_same6_tens_rule,'b6',a.B6),
    }
    print('BTN_FINAL_CANDIDATES_BEGIN');print(json.dumps(a.rnd(result),ensure_ascii=False,separators=(',',':')));print('BTN_FINAL_CANDIDATES_END')
if __name__=='__main__':main()
