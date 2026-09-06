#!/usr/bin/env python3
from collections import defaultdict
from analyze_cfg002_compare import load, newagg, add, finish, RCHR

EPS=0.02
BCS=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')
PAIR_MADE=('Overpair','High underpair','Weak pocket pair','Top pair','Second pair','Third pair')


def old_bc(r):
    f=r['fx']; hi,mid=f['top'],f['mid']
    if hi==14: return 'A[K-J]x' if mid>=11 else 'A[T-2]x'
    if sum(1 for x in (f['top'],f['mid'],f['low']) if x>=10)>=2: return 'BBx'
    if hi==13: return 'K[9-2]x'
    if 8<=hi<=12: return '[Q-8]x'
    return '[7-4]x'

def agg(rows,keyfn,flt=lambda r:True,minw=0):
    d=defaultdict(newagg)
    for r in rows:
        if flt(r): add(d[keyfn(r)],r)
    return {k:finish(v) for k,v in d.items() if v['w']>=minw}

def pct(x): return round(100*x,1)
def pr(k,z):
    print(k,'FCR',pct(z['fold']),pct(z['call']),pct(z['raise']),
          'loss',round(z['loss_F'],4),round(z['loss_C'],4),round(z['loss_R'],4),
          'cover',pct(z['cover_F']),pct(z['cover_C']),pct(z['cover_R']),
          'best',z['best_pure'],round(z['best_loss'],4),'w',round(z['weight'],1))

def kicker_bucket(r):
    k=r['fx']['kicker']
    if not k: return None
    return 'T+' if r['fx']['kicker'] and r['fx']['kicker'] in 'TJQKA' else '9-'

def main():
    path,rows=load('CFG002')
    for r in rows: r['oldbc']=old_bc(r)
    print('PAIRDRAW_OVERCARDS_BEGIN',path,len(rows),'EPS',EPS)

    # Baseline all pair categories by old board class.
    print('PAIR_BASE')
    d=agg(rows,lambda r:(r['oldbc'],r['fx']['made']),lambda r:r['fx']['made'] in PAIR_MADE)
    for b in BCS:
        for m in PAIR_MADE:
            if (b,m) in d: pr((b,m),d[(b,m)])

    # Every pair type + OESD and combined pair+OESD.
    print('PAIR_OESD')
    d=agg(rows,lambda r:(r['oldbc'],r['fx']['made']),lambda r:r['fx']['made'] in PAIR_MADE and r['fx']['sd']=='OESD',minw=50)
    dc=agg(rows,lambda r:r['oldbc'],lambda r:r['fx']['made'] in PAIR_MADE and r['fx']['sd']=='OESD',minw=50)
    for b in BCS:
        for m in PAIR_MADE:
            if (b,m) in d: pr((b,m),d[(b,m)])
        if b in dc: pr((b,'ALL PAIR+OESD'),dc[b])

    # Every pair type + gutshot and combined pair+gutshot.
    print('PAIR_GUTSHOT')
    d=agg(rows,lambda r:(r['oldbc'],r['fx']['made']),lambda r:r['fx']['made'] in PAIR_MADE and r['fx']['sd']=='Gutshot',minw=50)
    dc=agg(rows,lambda r:r['oldbc'],lambda r:r['fx']['made'] in PAIR_MADE and r['fx']['sd']=='Gutshot',minw=50)
    for b in BCS:
        for m in PAIR_MADE:
            if (b,m) in d: pr((b,m),d[(b,m)])
        if b in dc: pr((b,'ALL PAIR+GUTSHOT'),dc[b])

    # Second pair simplification, including kicker split and draw modifiers.
    print('SECOND_PAIR_SIMPLIFY')
    d=agg(rows,lambda r:r['oldbc'],lambda r:r['fx']['made']=='Second pair')
    dk=agg(rows,lambda r:(r['oldbc'],kicker_bucket(r)),lambda r:r['fx']['made']=='Second pair')
    dmod=agg(rows,lambda r:(r['oldbc'], 'OESD' if r['fx']['sd']=='OESD' else 'Gutshot' if r['fx']['sd']=='Gutshot' else 'BDFD' if r['fx']['bdfd'] else 'plain'),lambda r:r['fx']['made']=='Second pair')
    for b in BCS:
        if b in d: pr((b,'ALL SECOND PAIR'),d[b])
        for kb in ('T+','9-'):
            if (b,kb) in dk: pr((b,'SECOND',kb),dk[(b,kb)])
        for mod in ('plain','BDFD','Gutshot','OESD'):
            if (b,mod) in dmod: pr((b,'SECOND',mod),dmod[(b,mod)])

    # Two overcards first, with gutshot/BDFD as modifiers. High-card only, no made pair.
    print('TWO_OVERCARDS')
    def omod(r):
        sd=r['fx']['sd']; bd=r['fx']['bdfd']
        if sd=='OESD' and bd: return 'OESD+BDFD'
        if sd=='OESD': return 'OESD'
        if sd=='Gutshot' and bd: return 'Gutshot+BDFD'
        if sd=='Gutshot': return 'Gutshot'
        if bd: return 'BDFD'
        return 'plain'
    d=agg(rows,lambda r:(r['oldbc'],omod(r)),lambda r:r['fx']['made']=='High card' and r['fx']['two_over'],minw=50)
    dt=agg(rows,lambda r:r['oldbc'],lambda r:r['fx']['made']=='High card' and r['fx']['two_over'],minw=50)
    for b in BCS:
        if b in dt: pr((b,'ALL 2OC'),dt[b])
        for mod in ('plain','BDFD','Gutshot','Gutshot+BDFD','OESD','OESD+BDFD'):
            if (b,mod) in d: pr((b,'2OC',mod),d[(b,mod)])

    # One overcard too, to see whether a generic overcard category is useful.
    print('ONE_OVERCARD')
    d=agg(rows,lambda r:(r['oldbc'],omod(r)),lambda r:r['fx']['made']=='High card' and (not r['fx']['two_over']) and r['fx']['one_or_more_over'],minw=100)
    dt=agg(rows,lambda r:r['oldbc'],lambda r:r['fx']['made']=='High card' and (not r['fx']['two_over']) and r['fx']['one_or_more_over'],minw=100)
    for b in BCS:
        if b in dt: pr((b,'ALL 1OC'),dt[b])
        for mod in ('plain','BDFD','Gutshot','Gutshot+BDFD','OESD','OESD+BDFD'):
            if (b,mod) in d: pr((b,'1OC',mod),d[(b,mod)])

    print('PAIRDRAW_OVERCARDS_END')

if __name__=='__main__': main()
