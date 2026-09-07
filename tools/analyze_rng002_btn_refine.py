#!/usr/bin/env python3
import json
from collections import defaultdict
import analyze_rng002_btn_followups as a


def detail_bucket(r):
    h=a.hc(r['combo']); hr=a.ranks(h); br=a.ranks(a.bc(r['board'])); top=max(br)
    hb=r['hb']
    if hb=='Underpair':
        pr=hr[0]
        return 'Underpair T+' if pr>=10 else 'Underpair 9-'
    if hb in ('BDFD','X-high','Air'):
        n=sum(x>top for x in hr)
        if hb=='BDFD': return f'BDFD {n}OC'
        if hb=='X-high': return f'X-high {n}OC'
        return 'Air'
    return hb


def refined_cells(rows):
    d=defaultdict(lambda:[0.,0.,0.,0.,0.,0.,0.])
    for r in rows:
        k=(r['b4'],detail_bucket(r)); z=d[k]; w=r['w']
        z[0]+=w;z[1]+=w*r['F'];z[2]+=w*r['C'];z[3]+=w*r['R'];z[4]+=w*r['lF'];z[5]+=w*r['lC'];z[6]+=w*r['lR']
    out={}
    for (c,h),z in d.items():
        out.setdefault(c,{})[h]={'w':z[0],'F':z[1]/z[0],'C':z[2]/z[0],'R':z[3]/z[0],
                                 'lossF':z[4]/z[0],'lossC':z[5]/z[0],'lossR':z[6]/z[0],
                                 'best':min('FCR',key=lambda x:{'F':z[4],'C':z[5],'R':z[6]}[x])}
    return out


def eval_response(rows, rule):
    by=defaultdict(lambda:{'w':0.,'sF':0.,'sC':0.,'sR':0.,'cF':0.,'cC':0.,'cR':0.,'reg':0.})
    for r in rows:
        probs=rule(r)
        z=by[r['b4']];w=r['w'];z['w']+=w
        for x in 'FCR':z['s'+x]+=w*r[x];z['c'+x]+=w*probs[x]
        z['reg']+=w*(probs['F']*r['lF']+probs['C']*r['lC']+probs['R']*r['lR'])
    out={};tot=defaultdict(float)
    for c,z in by.items():
        w=z['w'];q={'w':w,'reg':z['reg']/w}
        for x in 'FCR':q['solver'+x]=z['s'+x]/w;q['cand'+x]=z['c'+x]/w;q['diff'+x]=q['cand'+x]-q['solver'+x]
        out[c]=q;tot['w']+=w;tot['reg']+=z['reg']
        for x in 'FCR':tot['s'+x]+=z['s'+x];tot['c'+x]+=z['c'+x]
    W=tot['w'];ov={'reg':tot['reg']/W}
    for x in 'FCR':ov['solver'+x]=tot['s'+x]/W;ov['cand'+x]=tot['c'+x]/W;ov['diff'+x]=ov['cand'+x]-ov['solver'+x]
    return {'by':out,'overall':ov}


def response_evfirst(r):
    # Human-readable EV-first baseline from broad cells: fold only obvious air/backdoors,
    # call almost all showdown/draw hands, and use a small selective raise pool.
    c=r['b4']; hb=r['hb']; d=detail_bucket(r)
    if hb=='Air': return {'F':1.,'C':0.,'R':0.}
    if c=='AKx' and hb=='BDFD': return {'F':1.,'C':0.,'R':0.}
    if c=='Kxx' and hb=='X-high': return {'F':1.,'C':0.,'R':0.}
    # Raise pool mirrors the aggregate cells where raising is cheap/best; use solver-like modest rates.
    p=0.
    if c in ('AKx','Kxx') and hb=='Two pair+':p=.25
    elif c=='[A/Q/J]xx' and hb in ('OESD','Gutshot','Two pair+'):p=.10
    elif c=='[T-4]x' and hb in ('OESD','Gutshot'):p=.25
    return {'F':0.,'C':1-p,'R':p}


def response_refined_best(r, rcells):
    b=detail_bucket(r);act=rcells[r['b4']][b]['best']
    return {x:1. if x==act else 0. for x in 'FCR'}


def eval_stab_pool(cells,solver,active,grid=(0,.25,.5,.75,1),tol=.08):
    import itertools
    best=None
    for rv in itertools.product(grid,repeat=4):
        by={};TW=SB=CB=RG=0.;ok=True
        for c,p in zip(a.B4,rv):
            cc=cells[c];W=sum(z['w'] for z in cc.values())
            cb=sum(z['w']*(p if h in active else 0.) for h,z in cc.items())/W
            reg=sum(z['w']*((p*z['lossB']+(1-p)*z['lossX']) if h in active else z['lossX']) for h,z in cc.items())/W
            sb=solver[c]['bet'];dif=cb-sb
            if abs(dif)>tol:ok=False;break
            by[c]={'solver':sb,'cand':cb,'diff':dif,'reg':reg};TW+=W;SB+=W*sb;CB+=W*cb;RG+=W*reg
        if not ok:continue
        ov={'solver':SB/TW,'cand':CB/TW,'diff':(CB-SB)/TW,'reg':RG/TW}
        key=(ov['reg'],sum(abs(q['diff']) for q in by.values()))
        if best is None or key<best[0]:best=(key,dict(zip(a.B4,rv)),by,ov)
    if not best:return None
    return {'active':sorted(active),'rates':best[1],'by':best[2],'overall':best[3]}


def main():
    p4=a.latest('datasets/DS__RNG002__CFG003__NOD004__BRD001__RUN-*.csv'); p5=a.latest('datasets/DS__RNG002__CFG003__NOD005__BRD001__RUN-*.csv')
    r4=a.load4(p4,'NOD004');r5=a.load4(p5,'NOD005')
    rc=refined_cells(r4); c5=a.cells5(r5); s5=a.agg_bet(r5,'b4')
    pools={
      'pairplus_draws':{'Two pair+','Overpair','Top pair','Second pair','Third pair','Underpair','OESD','Gutshot','BDFD'},
      'made2plus_draws':{'Two pair+','Overpair','Top pair','Second pair','Third pair','OESD','Gutshot','BDFD'},
      'value_directdraw':{'Two pair+','Overpair','Top pair','Second pair','OESD','Gutshot','BDFD'},
      'strong_directdraw':{'Two pair+','Overpair','Top pair','Second pair','OESD','Gutshot'},
    }
    res={'NOD004_refined_cells':rc,
         'NOD004_evfirst':eval_response(r4,response_evfirst),
         'NOD004_refined_best':eval_response(r4,lambda r:response_refined_best(r,rc)),
         'NOD005_natural':{k:eval_stab_pool(c5,s5,v) for k,v in pools.items()}}
    print('BTN_REFINE_REPORT_BEGIN')
    print(json.dumps(a.rnd(res),ensure_ascii=False,separators=(',',':')))
    print('BTN_REFINE_REPORT_END')
if __name__=='__main__':main()
