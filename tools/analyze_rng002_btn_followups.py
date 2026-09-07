#!/usr/bin/env python3
import csv, glob, itertools, json
from collections import defaultdict

RANK={r:i for i,r in enumerate('23456789TJQKA',start=2)}
STRAIGHTS=[{14,13,12,11,10},{13,12,11,10,9},{12,11,10,9,8},{11,10,9,8,7},{10,9,8,7,6},{9,8,7,6,5},{8,7,6,5,4},{7,6,5,4,3},{6,5,4,3,2},{14,5,4,3,2}]
BUCKETS=('Two pair+','Overpair','Top pair','Second pair','Underpair','Third pair','OESD','Gutshot','BDFD','X-high','Air')
B4=('AKx','Kxx','[A/Q/J]xx','[T-4]x')
B6=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')

def f(x): return float(str(x or 0).replace(',','.'))
def bc(b): return b.split()
def hc(c): return [c[:2],c[2:4]]
def ranks(cs): return [RANK[x[0]] for x in cs]
def suits(cs): return [x[1] for x in cs]
def straight(rs):
    u=set(rs); return any(w<=u for w in STRAIGHTS)
def sd_kind(br,hr):
    u=set(br+hr); miss=set()
    for w in STRAIGHTS:
        if len(w&u)==4: miss |= w-u
    return 'OESD' if len(miss)>=2 else 'Gutshot' if len(miss)==1 else None
def bdfd(b,h):
    s=suits(h); return s[0]==s[1] and s[0] in suits(b)
def board4(b):
    hi,mid,lo=sorted(ranks(bc(b)),reverse=True)
    if hi==14 and mid==13:return 'AKx'
    if hi==13:return 'Kxx'
    if hi in (14,12,11):return '[A/Q/J]xx'
    return '[T-4]x'
def board6(b):
    hi,mid,lo=sorted(ranks(bc(b)),reverse=True)
    if hi==14:return 'A[K-J]x' if mid>=11 else 'A[T-2]x'
    if sum(x>=10 for x in (hi,mid,lo))>=2:return 'BBx'
    if hi==13:return 'K[9-2]x'
    if 8<=hi<=12:return '[Q-8]x'
    return '[7-4]x'
def hand_bucket(board,combo):
    b=bc(board); h=hc(combo); br=ranks(b); hr=ranks(h); top,mid,low=sorted(br,reverse=True)
    cnt=defaultdict(int)
    for r in br+hr:cnt[r]+=1
    if straight(br+hr) or max(cnt.values())>=3 or sum(v>=2 for v in cnt.values())>=2:return 'Two pair+'
    if hr[0]==hr[1]: return 'Overpair' if hr[0]>top else 'Underpair'
    m=[r for r in hr if r in br]
    if m:
        x=max(m); return 'Top pair' if x==top else 'Second pair' if x==mid else 'Third pair'
    sd=sd_kind(br,hr)
    if sd:return sd
    if bdfd(b,h):return 'BDFD'
    if max(hr)>top:return 'X-high'
    return 'Air'

def latest(pattern):
    fs=sorted(glob.glob(pattern))
    if not fs:raise SystemExit('missing '+pattern)
    return fs[-1]
def load4(path,node):
    rows=[]
    with open(path,encoding='utf-8-sig',newline='') as fh:
        for x in csv.DictReader(fh):
            r={'board':x['board'],'combo':x['combo'],'w':f(x['reach_probability'])}
            r['b4']=board4(r['board']);r['b6']=board6(r['board']);r['hb']=hand_bucket(r['board'],r['combo'])
            if node=='NOD005':
                r.update(bet=f(x['bet_frequency']),check=f(x['check_frequency']),lb=f(x['loss_if_bet_btn']),lx=f(x['loss_if_check_btn']))
            else:
                r.update(F=f(x['fold_frequency']),C=f(x['call_frequency']),R=f(x['raise_frequency']),lF=f(x['loss_if_fold_btn']),lC=f(x['loss_if_call_btn']),lR=f(x['loss_if_raise_btn']))
            rows.append(r)
    return rows

def agg_bet(rows,key):
    d=defaultdict(lambda:[0.,0.])
    for r in rows:d[r[key]][0]+=r['w'];d[r[key]][1]+=r['w']*r['bet']
    return {k:{'w':v[0],'bet':v[1]/v[0]} for k,v in d.items()}
def agg_fcr(rows,key):
    d=defaultdict(lambda:[0.,0.,0.,0.])
    for r in rows:
        z=d[r[key]];z[0]+=r['w'];z[1]+=r['w']*r['F'];z[2]+=r['w']*r['C'];z[3]+=r['w']*r['R']
    return {k:{'w':v[0],'F':v[1]/v[0],'C':v[2]/v[0],'R':v[3]/v[0]} for k,v in d.items()}
def cells5(rows):
    d=defaultdict(lambda:[0.,0.,0.,0.])
    for r in rows:
        z=d[(r['b4'],r['hb'])];z[0]+=r['w'];z[1]+=r['w']*r['bet'];z[2]+=r['w']*r['lx'];z[3]+=r['w']*r['lb']
    out={}
    for (c,h),z in d.items():out.setdefault(c,{})[h]={'w':z[0],'bet':z[1]/z[0],'lossX':z[2]/z[0],'lossB':z[3]/z[0]}
    return out
def cells4(rows):
    d=defaultdict(lambda:[0.,0.,0.,0.,0.,0.,0.])
    for r in rows:
        z=d[(r['b4'],r['hb'])];z[0]+=r['w'];z[1]+=r['w']*r['F'];z[2]+=r['w']*r['C'];z[3]+=r['w']*r['R'];z[4]+=r['w']*r['lF'];z[5]+=r['w']*r['lC'];z[6]+=r['w']*r['lR']
    out={}
    for (c,h),z in d.items():out.setdefault(c,{})[h]={'w':z[0],'F':z[1]/z[0],'C':z[2]/z[0],'R':z[3]/z[0],'lossF':z[4]/z[0],'lossC':z[5]/z[0],'lossR':z[6]/z[0]}
    return out

def search_stab(cells, solver_b4):
    # Same active hand pool across all four classes; one randomizer rate per class.
    grids=(0,.25,.5,.75,1)
    best=None; feasible=0
    for mask in range(1<<len(BUCKETS)):
        active={BUCKETS[i] for i in range(len(BUCKETS)) if mask>>i&1}
        # class pool shares and pure-loss endpoints
        cls={}
        for c in B4:
            W=sum(v['w'] for v in cells.get(c,{}).values())
            pw=sum(v['w'] for h,v in cells.get(c,{}).items() if h in active)/W if W else 0
            # regret if rate p applied to active, check elsewhere = base + p*slope
            base=sum(v['w']*v['lossX'] for v in cells.get(c,{}).values())/W if W else 0
            slope=sum(v['w']*(v['lossB']-v['lossX']) for h,v in cells.get(c,{}).items() if h in active)/W if W else 0
            cls[c]=(W,pw,base,slope)
        for rv in itertools.product(grids,repeat=4):
            by={};tw=tb=ts=tr=0.; ok=True
            for c,p in zip(B4,rv):
                W,pw,base,slope=cls[c]; cb=p*pw; sb=solver_b4[c]['bet']; diff=cb-sb
                if abs(diff)>.05:ok=False;break
                reg=base+p*slope
                by[c]={'solver':sb,'cand':cb,'diff':diff,'reg':reg}
                tw+=W;tb+=W*cb;ts+=W*sb;tr+=W*reg
            if not ok:continue
            od=(tb-ts)/tw
            if abs(od)>.03:continue
            feasible+=1
            key=(tr/tw,sum(abs(z['diff']) for z in by.values()),len(active),sum(rv))
            if best is None or key<best[0]:best=(key,active,dict(zip(B4,rv)),by,{'solver':ts/tw,'cand':tb/tw,'diff':od,'reg':tr/tw})
    if not best:return {'feasible':0}
    _,a,r,b,o=best
    return {'feasible':feasible,'active':sorted(a),'rates':r,'by':b,'overall':o}

def search_response(cells, solver_b4):
    # Independent pure hand-bucket mapping per broad board class. Require each F/C/R frequency within 5pp.
    out={}; total={'w':0.,'F':0.,'C':0.,'R':0.,'reg':0.}
    for c in B4:
        cc=cells.get(c,{}); hbs=[h for h in BUCKETS if h in cc]; W=sum(cc[h]['w'] for h in hbs)
        best=None; feasible=0
        for acts in itertools.product('FCR',repeat=len(hbs)):
            cand={'F':0.,'C':0.,'R':0.}; reg=0.
            for h,a in zip(hbs,acts):
                z=cc[h];cand[a]+=z['w'];reg+=z['w']*z['loss'+a]
            cand={a:cand[a]/W for a in 'FCR'}
            dif={a:cand[a]-solver_b4[c][a] for a in 'FCR'}
            if max(abs(x) for x in dif.values())>.05:continue
            feasible+=1; reg/=W
            key=(reg,sum(abs(x) for x in dif.values()))
            if best is None or key<best[0]:best=(key,dict(zip(hbs,acts)),cand,dif,reg)
        if best is None:
            # Fall back to lowest-regret pure bucket map, no frequency constraint.
            for acts in itertools.product('FCR',repeat=len(hbs)):
                cand={'F':0.,'C':0.,'R':0.};reg=0.
                for h,a in zip(hbs,acts):
                    z=cc[h];cand[a]+=z['w'];reg+=z['w']*z['loss'+a]
                cand={a:cand[a]/W for a in 'FCR'};dif={a:cand[a]-solver_b4[c][a] for a in 'FCR'};reg/=W
                key=(reg,sum(abs(x) for x in dif.values()))
                if best is None or key<best[0]:best=(key,dict(zip(hbs,acts)),cand,dif,reg)
        _,mapping,cand,dif,reg=best
        out[c]={'feasible':feasible,'mapping':mapping,'solver':{a:solver_b4[c][a] for a in 'FCR'},'cand':cand,'diff':dif,'reg':reg,'w':W}
        total['w']+=W;total['reg']+=W*reg
        for a in 'FCR':total[a]+=W*cand[a]
    W=total['w']; overall={a:total[a]/W for a in 'FCR'};overall['reg']=total['reg']/W
    return {'by':out,'overall':overall}

def rnd(x):
    if isinstance(x,float):return round(x,6)
    if isinstance(x,dict):return {k:rnd(v) for k,v in x.items()}
    if isinstance(x,list):return [rnd(v) for v in x]
    return x

def main():
    p4=latest('datasets/DS__RNG002__CFG003__NOD004__BRD001__RUN-*.csv')
    p5=latest('datasets/DS__RNG002__CFG003__NOD005__BRD001__RUN-*.csv')
    r4=load4(p4,'NOD004');r5=load4(p5,'NOD005')
    s4b4=agg_fcr(r4,'b4');s5b4=agg_bet(r5,'b4')
    result={
      'datasets':{'NOD004':p4,'NOD005':p5},'rows':{'NOD004':len(r4),'NOD005':len(r5)},
      'NOD004':{'board4':s4b4,'board6':agg_fcr(r4,'b6'),'cells':cells4(r4)},
      'NOD005':{'board4':s5b4,'board6':agg_bet(r5,'b6'),'cells':cells5(r5)},
    }
    result['NOD004']['pure_bucket_search']=search_response(result['NOD004']['cells'],s4b4)
    result['NOD005']['same_pool_search']=search_stab(result['NOD005']['cells'],s5b4)
    print('BTN_FOLLOWUPS_REPORT_BEGIN')
    print(json.dumps(rnd(result),ensure_ascii=False,separators=(',',':')))
    print('BTN_FOLLOWUPS_REPORT_END')
if __name__=='__main__':main()
