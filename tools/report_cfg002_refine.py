#!/usr/bin/env python3
from collections import defaultdict
from analyze_cfg002_compare import load, newagg, add, finish, RCHR

BCS=('ABx','Axx','BBx','Kxx','[Q-8]x','[7-4]x')

def p(x): return round(100*x,1)
def emit(k,z):
    print(k,'|FCR',p(z['fold']),p(z['call']),p(z['raise']),
          '|loss',round(z['loss_F'],4),round(z['loss_C'],4),round(z['loss_R'],4),
          '|best',z['best_pure'],round(z['best_loss'],4),'cover',p(z['best_cover']),'|w',round(z['weight'],1))

def agg(rows,keyfn,minw=100):
    d=defaultdict(newagg)
    for r in rows: add(d[keyfn(r)],r)
    return {k:finish(a) for k,a in d.items() if a['w']>=minw}

def main():
    path,rows=load('CFG002')
    print('REFINE_BEGIN'); print('DATA',path,len(rows))

    # High-card direct draws by number of overcards and BDFD.
    rr=[r for r in rows if r['fx']['made']=='High card' and r['fx']['sd']]
    d=agg(rr,lambda r:(r['bc'],r['fx']['sd'],2 if r['fx']['two_over'] else 1 if r['fx']['one_or_more_over'] else 0,'BDFD' if r['fx']['bdfd'] else 'noBDFD'))
    print('HC_DRAWS_BY_OVERS')
    for b in BCS:
      for sd in ('Gutshot','OESD'):
       for ov in (2,1,0):
        for bd in ('noBDFD','BDFD'):
         k=(b,sd,ov,bd)
         if k in d: emit(k,d[k])

    # High-card no-direct-draw by overs + backdoors.
    rr=[r for r in rows if r['fx']['made']=='High card' and not r['fx']['sd']]
    d=agg(rr,lambda r:(r['bc'],2 if r['fx']['two_over'] else 1 if r['fx']['one_or_more_over'] else 0,
                           'BDFD' if r['fx']['bdfd'] else 'noBDFD','BDSD' if r['fx']['bdsd_paths'] else 'noBDSD'))
    print('HC_BACKDOORS_BY_OVERS')
    for b in BCS:
     for ov in (2,1,0):
      for bd in ('noBDFD','BDFD'):
       for sd in ('noBDSD','BDSD'):
        k=(b,ov,bd,sd)
        if k in d: emit(k,d[k])

    # Pair categories split only by draw texture, independent of kicker.
    rr=[r for r in rows if r['fx']['made'] in ('Top pair','Second pair','Third pair')]
    d=agg(rr,lambda r:(r['bc'],r['fx']['made'],r['fx']['sd'] or 'noSD','BDFD' if r['fx']['bdfd'] else 'noBDFD'))
    print('PAIRS_BY_DRAW')
    for b in BCS:
     for m in ('Top pair','Second pair','Third pair'):
      for sd in ('noSD','Gutshot','OESD'):
       for bd in ('noBDFD','BDFD'):
        k=(b,m,sd,bd)
        if k in d: emit(k,d[k])

    # No-direct-draw pairs by broad kicker buckets.
    def kb(r):
        k=r['fx']['kicker']; kr=14 if k=='A' else 13 if k=='K' else 12 if k=='Q' else 11 if k=='J' else 10 if k=='T' else 9 if k=='9' else 0
        return 'A-K' if kr>=13 else 'Q-T' if kr>=10 else '9-' if kr==9 else '8-'
    rr=[r for r in rows if r['fx']['made'] in ('Top pair','Second pair','Third pair') and not r['fx']['sd']]
    d=agg(rr,lambda r:(r['bc'],r['fx']['made'],kb(r),'BDFD' if r['fx']['bdfd'] else 'noBDFD'))
    print('PAIRS_BY_KICKER')
    for b in BCS:
     for m in ('Top pair','Second pair','Third pair'):
      for kx in ('A-K','Q-T','9-','8-'):
       for bd in ('noBDFD','BDFD'):
        k=(b,m,kx,bd)
        if k in d: emit(k,d[k])

    # Pocket-pair classes by direct/backdoor draws.
    rr=[r for r in rows if r['fx']['made'] in ('High underpair','Weak pocket pair')]
    d=agg(rr,lambda r:(r['bc'],r['fx']['made'],r['fx']['sd'] or 'noSD','BDFD' if r['fx']['bdfd'] else 'noBDFD'))
    print('POCKET_BY_DRAW')
    for b in BCS:
     for m in ('High underpair','Weak pocket pair'):
      for sd in ('noSD','Gutshot','OESD'):
       for bd in ('noBDFD','BDFD'):
        k=(b,m,sd,bd)
        if k in d: emit(k,d[k])

    print('REFINE_END')
if __name__=='__main__': main()
