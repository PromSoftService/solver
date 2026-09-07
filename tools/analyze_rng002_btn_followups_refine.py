#!/usr/bin/env python3
import csv, glob, itertools, json
from collections import defaultdict

RANK={r:i for i,r in enumerate('23456789TJQKA',start=2)}
STRAIGHTS=[{14,13,12,11,10},{13,12,11,10,9},{12,11,10,9,8},{11,10,9,8,7},{10,9,8,7,6},{9,8,7,6,5},{8,7,6,5,4},{7,6,5,4,3},{6,5,4,3,2},{14,5,4,3,2}]
B6=('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')
HANDS=('Straight','Set','Two pair','Overpair','Top pair','Second pair','Third pair','Underpair','OESD','Gutshot','BDFD','X-high','Air')


def f(x): return float(str(x or 0).replace(',','.'))
def bc(b): return b.split()
def hc(c): return [c[:2],c[2:4]]
def ranks(cs): return [RANK[x[0]] for x in cs]
def suits(cs): return [x[1] for x in cs]
def is_straight(rs):
    u=set(rs); return any(w<=u for w in STRAIGHTS)
def sd_kind(br,hr):
    u=set(br+hr); miss=set()
    for w in STRAIGHTS:
        if len(w&u)==4: miss |= w-u
    return 'OESD' if len(miss)>=2 else 'Gutshot' if len(miss)==1 else None
def bdfd(b,h):
    s=suits(h); return s[0]==s[1] and s[0] in suits(b)
def board6(board):
    hi,mid,lo=sorted(ranks(bc(board)),reverse=True)
    if hi==14:return 'A[K-J]x' if mid>=11 else 'A[T-2]x'
    if sum(x>=10 for x in (hi,mid,lo))>=2:return 'BBx'
    if hi==13:return 'K[9-2]x'
    if 8<=hi<=12:return '[Q-8]x'
    return '[7-4]x'
def hand_bucket(board,combo):
    b=bc(board); h=hc(combo); br=ranks(b); hr=ranks(h); top,mid,low=sorted(br,reverse=True)
    cnt=defaultdict(int)
    for r in br+hr: cnt[r]+=1
    if is_straight(br+hr): return 'Straight'
    if max(cnt.values())>=3: return 'Set'
    if sum(v>=2 for v in cnt.values())>=2: return 'Two pair'
    if hr[0]==hr[1]: return 'Overpair' if hr[0]>top else 'Underpair'
    matched=[r for r in hr if r in br]
    if matched:
        x=max(matched)
        return 'Top pair' if x==top else 'Second pair' if x==mid else 'Third pair'
    sd=sd_kind(br,hr)
    if sd: return sd
    if bdfd(b,h): return 'BDFD'
    if max(hr)>top: return 'X-high'
    return 'Air'


def latest(pattern):
    xs=sorted(glob.glob(pattern))
    if not xs: raise SystemExit('missing '+pattern)
    return xs[-1]
def load(path,node):
    rows=[]
    with open(path,encoding='utf-8-sig',newline='') as fh:
        for x in csv.DictReader(fh):
            r={'board':x['board'],'combo':x['combo'],'w':f(x['reach_probability'])}
            r['b6']=board6(r['board']); r['hb']=hand_bucket(r['board'],r['combo'])
            if node=='NOD005':
                r.update(B=f(x['bet_frequency']),X=f(x['check_frequency']),lB=f(x['loss_if_bet_btn']),lX=f(x['loss_if_check_btn']))
            else:
                r.update(F=f(x['fold_frequency']),C=f(x['call_frequency']),R=f(x['raise_frequency']),lF=f(x['loss_if_fold_btn']),lC=f(x['loss_if_call_btn']),lR=f(x['loss_if_raise_btn']))
            rows.append(r)
    return rows


def agg_solver(rows,node):
    d=defaultdict(lambda: defaultdict(float))
    for r in rows:
        z=d[r['b6']]; z['w']+=r['w']
        for a in ('B','X') if node=='NOD005' else ('F','C','R'):
            z[a]+=r['w']*r[a]
    out={}
    for c in B6:
        z=d[c]; w=z['w']
        out[c]={'w':w}
        for a in ('B','X') if node=='NOD005' else ('F','C','R'):
            out[c][a]=z[a]/w
    return out

def cells(rows,node):
    d=defaultdict(lambda: defaultdict(float))
    for r in rows:
        z=d[(r['b6'],r['hb'])]; z['w']+=r['w']
        if node=='NOD005':
            for a in ('B','X'):
                z[a]+=r['w']*r[a]; z['l'+a]+=r['w']*r['l'+a]
        else:
            for a in ('F','C','R'):
                z[a]+=r['w']*r[a]; z['l'+a]+=r['w']*r['l'+a]
    out={}
    for (c,h),z in d.items():
        w=z['w']; q={'w':w}
        for a in ('B','X') if node=='NOD005' else ('F','C','R'):
            q[a]=z[a]/w; q['l'+a]=z['l'+a]/w
        out.setdefault(c,{})[h]=q
    return out


def eval_stab_pool(cell,solver,pool,rates):
    by={}; TW=SB=CB=REG=0.
    for c in B6:
        cc=cell[c]; W=sum(z['w'] for z in cc.values()); p=rates[c]
        active_w=sum(z['w'] for h,z in cc.items() if h in pool)
        cand=p*active_w/W
        reg=sum(z['w']*((p*z['lB']+(1-p)*z['lX']) if h in pool else z['lX']) for h,z in cc.items())/W
        sb=solver[c]['B']; by[c]={'solver':sb,'cand':cand,'diff':cand-sb,'reg':reg,'pool_share':active_w/W,'rate':p}
        TW+=W; SB+=W*sb; CB+=W*cand; REG+=W*reg
    return by,{'solver':SB/TW,'cand':CB/TW,'diff':(CB-SB)/TW,'reg':REG/TW}

def best_rates_for_pool(cell,solver,pool,grid=(0,.25,.4,.5,.6,.75,1),tol=.05):
    rates={}; feasible=True
    for c in B6:
        cc=cell[c]; W=sum(z['w'] for z in cc.values()); aw=sum(z['w'] for h,z in cc.items() if h in pool)
        best=None
        for p in grid:
            cand=p*aw/W; diff=cand-solver[c]['B']
            reg=sum(z['w']*((p*z['lB']+(1-p)*z['lX']) if h in pool else z['lX']) for h,z in cc.items())/W
            ok=abs(diff)<=tol
            key=(0 if ok else 1, reg, abs(diff), p)
            if best is None or key<best[0]: best=(key,p,ok)
        rates[c]=best[1]; feasible &= best[2]
    by,ov=eval_stab_pool(cell,solver,pool,rates)
    return {'pool':sorted(pool,key=HANDS.index),'rates':rates,'by':by,'overall':ov,'all_classes_within_5pp':feasible}

def search_stab_pool(cell,solver):
    # Same hand pool across all six familiar flop classes; class randomizer may differ.
    best=None; feasible_count=0
    for mask in range(1<<len(HANDS)):
        pool={HANDS[i] for i in range(len(HANDS)) if (mask>>i)&1}
        q=best_rates_for_pool(cell,solver,pool)
        if not q['all_classes_within_5pp']: continue
        if abs(q['overall']['diff'])>.03: continue
        feasible_count+=1
        # Penalize odd/discontinuous pools after EV, then frequency error and pool complexity.
        weird=0
        order=['Straight','Set','Two pair','Overpair','Top pair','Second pair','Third pair','Underpair','OESD','Gutshot','BDFD','X-high','Air']
        bits=[h in pool for h in order]
        weird=sum(bits[i] and not bits[i-1] for i in range(1,len(bits)))
        key=(q['overall']['reg'],sum(abs(v['diff']) for v in q['by'].values()),weird,len(pool))
        if best is None or key<best[0]: best=(key,q)
    return {'feasible':feasible_count,'best':best[1] if best else None}


def response_probs_for(h,q_value,q_draw,u,b,x):
    if h in ('Straight','Set','Two pair'): return {'F':0,'C':1-q_value,'R':q_value}
    if h in ('Overpair','Top pair','Second pair','Third pair'): return {'F':0,'C':1,'R':0}
    if h in ('OESD','Gutshot'): return {'F':0,'C':1-q_draw,'R':q_draw}
    if h=='Underpair': return {'F':1-u,'C':u,'R':0}
    if h=='BDFD': return {'F':1-b,'C':b,'R':0}
    if h=='X-high': return {'F':1-x,'C':x,'R':0}
    return {'F':1,'C':0,'R':0}
def eval_response_class(cc,solver,q_value,q_draw,u,b,x):
    W=sum(z['w'] for z in cc.values()); cand={a:0. for a in 'FCR'}; reg=0.
    for h,z in cc.items():
        p=response_probs_for(h,q_value,q_draw,u,b,x)
        for a in 'FCR': cand[a]+=z['w']*p[a]
        reg+=z['w']*sum(p[a]*z['l'+a] for a in 'FCR')
    cand={a:cand[a]/W for a in 'FCR'}; reg/=W
    diff={a:cand[a]-solver[a] for a in 'FCR'}
    return cand,diff,reg

def search_response_template(cell,solver):
    # Human template intentionally mirrors the BB-vs-cbet concept:
    # made pairs call; strong made/direct draws call-raise; pocket pairs/BDFD/X-high use board-class F/C mix; air folds.
    mixgrid=(0,.25,.5,.75,1)
    raisegrid=(0,.2,.25,.33,.5)
    best=None
    for qv in raisegrid:
      for qd in raisegrid:
        by={}; TW=REG=0.; sums={a:0. for a in 'FCR'}; feasible=True
        for c in B6:
            cc=cell[c]; W=sum(z['w'] for z in cc.values()); cbest=None
            for u,b,x in itertools.product(mixgrid,repeat=3):
                cand,diff,reg=eval_response_class(cc,solver[c],qv,qd,u,b,x)
                ok=max(abs(v) for v in diff.values())<=.05
                key=(0 if ok else 1,reg,sum(abs(v) for v in diff.values()),u+b+x)
                if cbest is None or key<cbest[0]: cbest=(key,u,b,x,cand,diff,reg,ok)
            _,u,b,x,cand,diff,reg,ok=cbest
            feasible &= ok
            by[c]={'solver':{a:solver[c][a] for a in 'FCR'},'cand':cand,'diff':diff,'reg':reg,'underpair_call':u,'bdfd_call':b,'xhigh_call':x}
            TW+=W; REG+=W*reg
            for a in 'FCR': sums[a]+=W*cand[a]
        ov={a:sums[a]/TW for a in 'FCR'}; ov['reg']=REG/TW
        if not feasible: continue
        solver_ov={a:sum(solver[c]['w']*solver[c][a] for c in B6)/sum(solver[c]['w'] for c in B6) for a in 'FCR'}
        ov['solver']=solver_ov; ov['diff']={a:ov[a]-solver_ov[a] for a in 'FCR'}
        key=(ov['reg'],sum(abs(v) for v in ov['diff'].values()),qv+qd)
        if best is None or key<best[0]: best=(key,{'value_raise':qv,'draw_raise':qd,'by':by,'overall':ov})
    return best[1] if best else None


def compact_cells(cell,node):
    out={}
    for c in B6:
        out[c]={}
        for h in HANDS:
            if h not in cell.get(c,{}): continue
            z=cell[c][h]
            if node=='NOD005': out[c][h]={'w':z['w'],'B':z['B'],'lX':z['lX'],'lB':z['lB']}
            else: out[c][h]={'w':z['w'],'F':z['F'],'C':z['C'],'R':z['R'],'lF':z['lF'],'lC':z['lC'],'lR':z['lR']}
    return out

def rnd(v):
    if isinstance(v,float): return round(v,6)
    if isinstance(v,dict): return {k:rnd(x) for k,x in v.items()}
    if isinstance(v,list): return [rnd(x) for x in v]
    return v


def main():
    p4=latest('datasets/DS__RNG002__CFG003__NOD004__BRD001__RUN-*.csv')
    p5=latest('datasets/DS__RNG002__CFG003__NOD005__BRD001__RUN-*.csv')
    r4=load(p4,'NOD004'); r5=load(p5,'NOD005')
    s4=agg_solver(r4,'NOD004'); s5=agg_solver(r5,'NOD005')
    c4=cells(r4,'NOD004'); c5=cells(r5,'NOD005')

    old_utg_bb_pool={'Straight','Set','Two pair','Overpair','Top pair','Second pair','OESD','Gutshot','BDFD','X-high'}
    current_pair_draw_pool={'Straight','Set','Two pair','Overpair','Top pair','Second pair','Third pair','Underpair','OESD','Gutshot','BDFD'}
    pair_draw_x_pool=current_pair_draw_pool|{'X-high'}
    all_except_air=set(HANDS)-{'Air'}

    stab_predefined={
      'same_as_old_UTG_vs_BB_cbet':best_rates_for_pool(c5,s5,old_utg_bb_pool),
      'pairplus_directdraw_BDFD':best_rates_for_pool(c5,s5,current_pair_draw_pool),
      'pairplus_directdraw_BDFD_Xhigh':best_rates_for_pool(c5,s5,pair_draw_x_pool),
      'everything_except_air':best_rates_for_pool(c5,s5,all_except_air),
    }
    result={
      'datasets':{'NOD004':p4,'NOD005':p5},'rows':{'NOD004':len(r4),'NOD005':len(r5)},
      'NOD004':{'solver_board6':s4,'template_search':search_response_template(c4,s4),'cells':compact_cells(c4,'NOD004')},
      'NOD005':{'solver_board6':s5,'predefined':stab_predefined,'exhaustive_same_pool':search_stab_pool(c5,s5),'cells':compact_cells(c5,'NOD005')},
    }
    print('BTN_FOLLOWUPS_REFINE_BEGIN')
    print(json.dumps(rnd(result),ensure_ascii=False,separators=(',',':')))
    print('BTN_FOLLOWUPS_REFINE_END')

if __name__=='__main__': main()
