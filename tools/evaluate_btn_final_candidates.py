#!/usr/bin/env python3
import json
import analyze_rng002_btn_followups as a
import analyze_rng002_btn_refine as r


def stab_rule(x):
    c=x['b4'];h=x['hb']
    if c=='[T-4]x': return .75
    pool={'Two pair+','Overpair','Top pair','Second pair','OESD','Gutshot','BDFD'}
    if h not in pool:return 0.
    if c=='AKx' and h=='BDFD':return 0.
    if c=='AKx':return .75
    return 1.

def stab_same6_rule(x):
    # Reuse exactly the familiar UTG-vs-BB c-bet hand pool and familiar six flop classes.
    pool={'Two pair+','Overpair','Top pair','Second pair','OESD','Gutshot','BDFD','X-high'}
    if x['hb'] not in pool:return 0.
    rates={
      'A[K-J]x':.70,
      'A[T-2]x':.85,
      'BBx':.75,
      'K[9-2]x':.80,
      '[Q-8]x':.90,
      '[7-4]x':.85,
    }
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
    # Fold layer.
    pf=0.
    if hb=='Air':pf=1.
    elif c in ('AKx','Kxx','[A/Q/J]xx') and d=='BDFD 0OC':pf=1.
    elif c=='[A/Q/J]xx' and d=='BDFD 1OC':pf=.50
    elif d=='X-high 1OC':pf=1.
    elif c=='AKx' and d=='Underpair 9-':pf=.75
    if pf>0:return {'F':pf,'C':1-pf,'R':0.}
    # Raise layer among hands that continue.
    pr=0.
    if c in ('AKx','Kxx') and hb=='Two pair+':pr=1.
    elif c=='[A/Q/J]xx' and hb in ('Two pair+','OESD','Gutshot'):pr=.40
    elif c=='[T-4]x' and hb in ('OESD','Gutshot'):pr=1.
    return {'F':0.,'C':1-pr,'R':pr}

def main():
    p4=a.latest('datasets/DS__RNG002__CFG003__NOD004__BRD001__RUN-*.csv');p5=a.latest('datasets/DS__RNG002__CFG003__NOD005__BRD001__RUN-*.csv')
    x4=a.load4(p4,'NOD004');x5=a.load4(p5,'NOD005')
    result={
      'NOD004_final':r.eval_response(x4,response_rule),
      'NOD005_final':eval_stab(x5),
      'NOD005_same6_familiar_pool':eval_stab(x5,stab_same6_rule,'b6',a.B6),
    }
    print('BTN_FINAL_CANDIDATES_BEGIN');print(json.dumps(a.rnd(result),ensure_ascii=False,separators=(',',':')));print('BTN_FINAL_CANDIDATES_END')
if __name__=='__main__':main()
