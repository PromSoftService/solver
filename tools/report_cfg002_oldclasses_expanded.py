#!/usr/bin/env python3
from collections import defaultdict
from analyze_cfg002_compare import load, add, finish, aggregate, RCHR, RANK, EPS

BCS=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')

def old_bc(r):
    f=r['fx']; hi,mid=f['top'],f['mid']
    if hi==14:
        return 'A[K-J]x' if mid>=11 else 'A[T-2]x'
    if hi>=10 and mid>=10:
        return 'BBx'
    if hi==13:
        return 'K[9-2]x'
    if 8<=hi<=12:
        return '[Q-8]x'
    return '[7-4]x'

def p(x): return round(100*x,1)
def line(k,z):
    print(k,'FCR',p(z['fold']),p(z['call']),p(z['raise']),
          'loss',round(z['loss_F'],4),round(z['loss_C'],4),round(z['loss_R'],4),
          'best',z['best_pure'],round(z['best_loss'],4),'cover',p(z['best_cover']),'w',round(z['weight'],1))

def kicker_rank(r):
    k=r['fx']['kicker']
    return RANK[k] if k else 0

def pair_mod(r):
    f=r['fx']
    if f['sd']: return f['sd'] + ('+BDFD' if f['bdfd'] else '')
    if f['bdfd']: return 'BDFD'
    if f['bdsd_paths']: return 'BDSD'
    return 'none'

def board_stats(rows):
    pb=defaultdict(lambda: {'w':0.0,'f':0.0,'c':0.0,'r':0.0})
    for r in rows:
        b=pb[r['board']]; w=r['w']; b['w']+=w; b['f']+=w*r['fold']; b['c']+=w*r['call']; b['r']+=w*r['raise']
    out=defaultdict(lambda:[0,0.0,0.0,0.0])
    boardmap={r['board']:r['obc'] for r in rows}
    for board,a in pb.items():
        w=a['w'] or 1.0; q=out[boardmap[board]]; q[0]+=1; q[1]+=a['f']/w; q[2]+=a['c']/w; q[3]+=a['r']/w
    for bc in BCS:
        n,f,c,rr=out[bc]
        print('BOARD',bc,'SDF/C/R',round(100*(c+rr)/n,1),round(100*c/n,1),round(100*rr/n,1),'boards',n)

def main():
    path,rows=load('CFG002')
    for r in rows: r['obc']=old_bc(r)
    print('OLD_EXPANDED_BEGIN',path,len(rows),'EPS',EPS)
    board_stats(rows)

    print('MADE')
    made=aggregate(rows, lambda r:(r['obc'],r['fx']['made']))
    for b in BCS:
        for m in ('Set/Trips','Two pair','Straight','Overpair','Top pair','High underpair','Weak pocket pair'):
            k=str((b,m))
            if k in made: line(k,made[k])

    print('SECOND_PAIR')
    sp=[r for r in rows if r['fx']['made']=='Second pair']
    d=aggregate(sp,lambda r:(r['obc'], 'BDFD' if r['fx']['bdfd'] else 'noBDFD', 'direct' if r['fx']['sd'] else 'noDirect', 'goodK' if kicker_rank(r)>=10 else 'weakK'))
    for k,z in d.items(): line(k,z)

    print('THIRD_PAIR')
    tp=[r for r in rows if r['fx']['made']=='Third pair']
    d=aggregate(tp,lambda r:(r['obc'], 'BDFD' if r['fx']['bdfd'] else 'noBDFD', 'direct' if r['fx']['sd'] else 'noDirect', 'goodK' if kicker_rank(r)>=10 else 'weakK'))
    for k,z in d.items(): line(k,z)

    print('HIGH_UNDERPAIR_GAP')
    hu=[r for r in rows if r['fx']['made']=='High underpair']
    # distance from middle board card: 1=closest to middle; larger = closer to top
    d=aggregate(hu,lambda r:(r['obc'], r['fx']['pocket_rank']-r['fx']['mid'], 'direct' if r['fx']['sd'] else 'noDirect'))
    for k,z in d.items(): line(k,z)

    print('WEAK_POCKET_DRAW')
    wp=[r for r in rows if r['fx']['made']=='Weak pocket pair']
    d=aggregate(wp,lambda r:(r['obc'], r['fx']['sd'] or 'noDirect'))
    for k,z in d.items(): line(k,z)

    print('HIGHCARD_OESD')
    hc=[r for r in rows if r['fx']['made']=='High card' and r['fx']['sd']=='OESD']
    d=aggregate(hc,lambda r:(r['obc'],'BDFD' if r['fx']['bdfd'] else 'noBDFD', int(r['fx']['two_over']) + int(r['fx']['one_or_more_over'] and not r['fx']['two_over'])))
    for k,z in d.items(): line(k,z)

    print('HIGHCARD_GUTSHOT')
    hc=[r for r in rows if r['fx']['made']=='High card' and r['fx']['sd']=='Gutshot']
    def overs(r):
        hr=[RANK[r['combo'][0]],RANK[r['combo'][2]]]; top=r['fx']['top']; return sum(x>top for x in hr)
    d=aggregate(hc,lambda r:(r['obc'],overs(r),'BDFD' if r['fx']['bdfd'] else 'noBDFD'))
    for k,z in d.items(): line(k,z)

    print('HIGHCARD_EXACT')
    hc=[r for r in rows if r['fx']['made']=='High card' and not r['fx']['sd'] and r['fx']['hole'] in ('AK','AQ','AJ','AT','KQ','KJ')]
    d=aggregate(hc,lambda r:(r['obc'],r['fx']['hole'],'BDFD' if r['fx']['bdfd'] else ('BDSD' if r['fx']['bdsd_paths'] else 'none')))
    for k,z in d.items(): line(k,z)
    print('OLD_EXPANDED_END')

if __name__=='__main__': main()
