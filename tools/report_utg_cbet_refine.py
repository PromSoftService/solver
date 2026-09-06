#!/usr/bin/env python3
import csv, glob
from collections import defaultdict
from analyze_cfg002_compare import features

EPS=0.02
BCS=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')


def fnum(s): return float(str(s).replace(',','.')) if s not in (None,'') else 0.0

def bclass(r):
    f=r['fx']; hi,mid=f['top'],f['mid']
    if hi==14: return 'A[K-J]x' if mid>=11 else 'A[T-2]x'
    if sum(1 for x in (f['top'],f['mid'],f['low']) if x>=10)>=2: return 'BBx'
    if hi==13: return 'K[9-2]x'
    if 8<=hi<=12: return '[Q-8]x'
    return '[7-4]x'

def load():
    fs=sorted(glob.glob('datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-*.csv'))
    if not fs: raise SystemExit('UTG dataset not found')
    p=fs[-1]; rows=[]
    with open(p,encoding='utf-8-sig',newline='') as f:
        for x in csv.DictReader(f):
            r={'board':x['board'],'combo':x['combo'],'w':fnum(x['reach_probability']),
               'x':fnum(x['check_frequency']),'b':fnum(x['bet_frequency']),
               'lx':fnum(x['loss_if_check_utg']),'lb':fnum(x['loss_if_bet_utg'])}
            r['fx']=features(r['board'],r['combo']); r['bc']=bclass(r); rows.append(r)
    return p,rows

def newagg(): return {'w':0,'x':0,'b':0,'lx':0,'lb':0,'okx':0,'okb':0,'n':0}
def add(a,r):
    w=r['w']; a['w']+=w; a['n']+=1; a['x']+=w*r['x']; a['b']+=w*r['b']; a['lx']+=w*r['lx']; a['lb']+=w*r['lb']; a['okx']+=w*(r['lx']<=EPS); a['okb']+=w*(r['lb']<=EPS)
def fin(a):
    w=a['w'] or 1
    z={k:a[k]/w for k in ('x','b','lx','lb','okx','okb')}; z['w']=a['w']; z['n']=a['n']; z['best']='B' if z['lb']<z['lx'] else 'X'; return z
def agg(rows,key,flt=lambda r:True,minw=0):
    d=defaultdict(newagg)
    for r in rows:
        if flt(r): add(d[key(r)],r)
    return {k:fin(v) for k,v in d.items() if v['w']>=minw}
def pr(k,z): print(k,'XB',round(100*z['x'],1),round(100*z['b'],1),'lossXB',round(z['lx'],4),round(z['lb'],4),'coverXB',round(100*z['okx'],1),round(100*z['okb'],1),'best',z['best'],'w',round(z['w'],1))

def ocn(r):
    if r['fx']['two_over']: return '2OC'
    if r['fx']['one_or_more_over']: return '1OC'
    return '0OC'

def mod(r):
    sd=r['fx']['sd']; bd=r['fx']['bdfd']; bs=bool(r['fx']['bdsd_paths'])
    if sd=='OESD': return 'OESD+BDFD' if bd else 'OESD'
    if sd=='Gutshot': return 'Gutshot+BDFD' if bd else 'Gutshot'
    if bd: return 'BDFD'
    if bs: return 'BDSD'
    return 'plain'

def main():
    path,rows=load(); print('UTG_CBET_REFINE_BEGIN',path,len(rows),'EPS',EPS)
    # Board-level average cbet frequencies within six established board classes.
    pb=defaultdict(newagg)
    for r in rows:add(pb[r['board']],r)
    tmp=defaultdict(list)
    for board,a in pb.items():
        z=fin(a); bc=next(r['bc'] for r in rows if r['board']==board); tmp[bc].append(z)
    print('BOARD_FREQ')
    for bc in BCS:
        zs=tmp[bc]; print(bc,'boards',len(zs),'bet_avg',round(100*sum(z['b'] for z in zs)/len(zs),1),'bet_minmax',round(100*min(z['b'] for z in zs),1),round(100*max(z['b'] for z in zs),1))

    print('MADE_BASE')
    made=('Straight','Set/Trips','Two pair','Overpair','High underpair','Weak pocket pair','Top pair','Second pair','Third pair','High card')
    d=agg(rows,lambda r:(r['bc'],r['fx']['made']))
    for bc in BCS:
        for m in made:
            if (bc,m) in d: pr((bc,m),d[(bc,m)])

    print('PAIR_DRAW')
    pairs=('Overpair','High underpair','Weak pocket pair','Top pair','Second pair','Third pair')
    d=agg(rows,lambda r:(r['bc'],r['fx']['made'],mod(r)),lambda r:r['fx']['made'] in pairs,minw=100)
    for bc in BCS:
        for m in pairs:
            for md in ('plain','BDFD','BDSD','Gutshot','Gutshot+BDFD','OESD','OESD+BDFD'):
                if (bc,m,md) in d: pr((bc,m,md),d[(bc,m,md)])

    print('HIGHCARD_DRAW')
    d=agg(rows,lambda r:(r['bc'],ocn(r),mod(r)),lambda r:r['fx']['made']=='High card',minw=100)
    for bc in BCS:
        for oc in ('2OC','1OC','0OC'):
            for md in ('plain','BDFD','BDSD','Gutshot','Gutshot+BDFD','OESD','OESD+BDFD'):
                if (bc,oc,md) in d: pr((bc,oc,md),d[(bc,oc,md)])

    print('BROAD_CANDIDATES')
    filters={
      'Any pair':lambda r:r['fx']['made'] in pairs,
      'Weak pocket':lambda r:r['fx']['made']=='Weak pocket pair',
      'OESD no pair':lambda r:r['fx']['made']=='High card' and r['fx']['sd']=='OESD',
      'Gutshot no pair':lambda r:r['fx']['made']=='High card' and r['fx']['sd']=='Gutshot',
      'BDFD only no pair':lambda r:r['fx']['made']=='High card' and not r['fx']['sd'] and r['fx']['bdfd'],
      'Air no pair':lambda r:r['fx']['made']=='High card' and not r['fx']['sd'] and not r['fx']['bdfd'],
      '2OC+draw':lambda r:r['fx']['made']=='High card' and r['fx']['two_over'] and (r['fx']['sd'] or r['fx']['bdfd']),
      '2OC plain':lambda r:r['fx']['made']=='High card' and r['fx']['two_over'] and not r['fx']['sd'] and not r['fx']['bdfd'],
    }
    for name,flt in filters.items():
        print('CAND',name); d=agg(rows,lambda r:r['bc'],flt,minw=100)
        for bc in BCS:
            if bc in d: pr((bc,name),d[bc])
    print('UTG_CBET_REFINE_END')
if __name__=='__main__': main()
