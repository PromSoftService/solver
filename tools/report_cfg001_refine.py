#!/usr/bin/env python3
from collections import defaultdict
from analyze_cfg002_compare import load, newagg, add, finish

EPS=0.02
BCS=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')


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


def omod(r):
    sd=r['fx']['sd']; bd=r['fx']['bdfd']
    if sd=='OESD' and bd: return 'OESD+BDFD'
    if sd=='OESD': return 'OESD'
    if sd=='Gutshot' and bd: return 'Gutshot+BDFD'
    if sd=='Gutshot': return 'Gutshot'
    if bd: return 'BDFD'
    if r['fx']['bdsd_paths']: return 'BDSD'
    return 'plain'


def main():
    path,rows=load('CFG001')
    for r in rows: r['oldbc']=old_bc(r)
    print('CFG001_REFINE_BEGIN',path,len(rows),'EPS',EPS)

    # Made/pair baseline by requested board class.
    print('PAIR_BASE')
    pairm=('Overpair','High underpair','Weak pocket pair','Top pair','Second pair','Third pair')
    d=agg(rows,lambda r:(r['oldbc'],r['fx']['made']),lambda r:r['fx']['made'] in pairm)
    for b in BCS:
        for m in pairm:
            if (b,m) in d: pr((b,m),d[(b,m)])

    # Weak pocket pair, all draw modifiers, to see if one row is enough.
    print('WEAK_PAIR_MODS')
    d=agg(rows,lambda r:(r['oldbc'],omod(r)),lambda r:r['fx']['made']=='Weak pocket pair',minw=25)
    dt=agg(rows,lambda r:r['oldbc'],lambda r:r['fx']['made']=='Weak pocket pair')
    for b in BCS:
        if b in dt: pr((b,'ALL WEAK'),dt[b])
        for mod in ('plain','BDFD','BDSD','Gutshot','Gutshot+BDFD','OESD','OESD+BDFD'):
            if (b,mod) in d: pr((b,'WEAK',mod),d[(b,mod)])

    # High-card 2 overcards with modifier-first structure.
    print('TWO_OVERCARDS')
    d=agg(rows,lambda r:(r['oldbc'],omod(r)),lambda r:r['fx']['made']=='High card' and r['fx']['two_over'],minw=25)
    dt=agg(rows,lambda r:r['oldbc'],lambda r:r['fx']['made']=='High card' and r['fx']['two_over'],minw=25)
    for b in BCS:
        if b in dt: pr((b,'ALL 2OC'),dt[b])
        for mod in ('plain','BDFD','BDSD','Gutshot','Gutshot+BDFD','OESD','OESD+BDFD'):
            if (b,mod) in d: pr((b,'2OC',mod),d[(b,mod)])

    # Candidate broad merge: 2OC + any useful draw (BDFD/Gutshot/OESD), excluding plain/BDSD-only.
    print('TWO_OVERCARDS_MERGES')
    useful=lambda r:r['fx']['made']=='High card' and r['fx']['two_over'] and (r['fx']['bdfd'] or r['fx']['sd'] in ('Gutshot','OESD'))
    d=agg(rows,lambda r:r['oldbc'],useful,minw=25)
    da=agg(rows,lambda r:'ALL',useful,minw=25)
    for b in BCS:
        if b in d: pr((b,'2OC+ANYDRAW'),d[b])
    if 'ALL' in da: pr(('ALL','2OC+ANYDRAW'),da['ALL'])

    # High-card direct draws split by overcard count and BDFD.
    print('DIRECT_DRAWS')
    def ocn(r):
        if r['fx']['two_over']: return '2OC'
        if r['fx']['one_or_more_over']: return '1OC'
        return '0OC'
    d=agg(rows,lambda r:(r['oldbc'],r['fx']['sd'],ocn(r),'BDFD' if r['fx']['bdfd'] else 'noBDFD'),
          lambda r:r['fx']['made']=='High card' and r['fx']['sd'] in ('Gutshot','OESD'),minw=25)
    for b in BCS:
        for sd in ('OESD','Gutshot'):
            for oc in ('2OC','1OC','0OC'):
                for bd in ('BDFD','noBDFD'):
                    if (b,sd,oc,bd) in d: pr((b,sd,oc,bd),d[(b,sd,oc,bd)])

    # Existing broad direct draw rows, excluding made pairs.
    print('BROAD_DRAW_ROWS')
    filters={
      'OESD_no_pair': lambda r:r['fx']['made']=='High card' and r['fx']['sd']=='OESD',
      'Gutshot+BDFD_no_pair': lambda r:r['fx']['made']=='High card' and r['fx']['sd']=='Gutshot' and r['fx']['bdfd'],
      'Gutshot_noBDFD_no_pair': lambda r:r['fx']['made']=='High card' and r['fx']['sd']=='Gutshot' and not r['fx']['bdfd'],
    }
    for name,flt in filters.items():
        d=agg(rows,lambda r:r['oldbc'],flt,minw=25)
        for b in BCS:
            if b in d: pr((b,name),d[b])

    # Bare AK/AQ/AJ, no direct draw, no BDFD, high-card only.
    print('BROADWAY_BARE')
    def bare_hole(r,h):
        return r['fx']['made']=='High card' and r['fx']['hole']==h and not r['fx']['sd'] and not r['fx']['bdfd']
    for h in ('AK','AQ','AJ','AT','KQ','KJ'):
        d=agg(rows,lambda r:r['oldbc'],lambda r,h=h:bare_hole(r,h),minw=25)
        for b in BCS:
            if b in d: pr((b,h,'bare'),d[b])

    # Candidate merge of bare AK/AQ/AJ into overcard count / strong ace rows.
    print('STRONG_ACE_HIGH')
    d=agg(rows,lambda r:r['oldbc'],lambda r:r['fx']['made']=='High card' and r['fx']['hole'] in ('AK','AQ','AJ') and not r['fx']['sd'] and not r['fx']['bdfd'],minw=25)
    for b in BCS:
        if b in d: pr((b,'AK/AQ/AJ bare'),d[b])

    print('CFG001_REFINE_END')

if __name__=='__main__': main()
