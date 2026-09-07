"""Bounded action-map search, not a poker solver. No new hand classes.
MILP establishes a feasible map under explicit diagnostic budgets; greedy
region merging then reduces rules. Global optimality of the human strategy
is NOT claimed. All budgets are analyst screening choices, not BR bounds.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp, linprog
from scipy.sparse import csr_matrix
from core import *

BUDGET = dict(overall_regret=.04, class_regret=.10, frequency_pp=10., diagnostic_frequency_pp=15.,
              tail_over_05=.025, tail_over_10=.0075, major_cell_share=.02, major_cell_regret=.20,
              raise_retention=.5, raise_group_retention=.4)
LOGICAL_ROWS = ((0,), (1,2), (3,4,5,6), (7,8,9,10,11), (12,13,14))


def options(acts, mixed):
    p=list(np.eye(len(acts))); labels=list(acts)
    if mixed:
        pairs=[(0,1)] if acts=='XB' else [(0,1),(1,2)]
        for i,j in pairs:
            for t in ((.5,.75) if acts=='XB' else (.5,.75,.25)):
                a=np.zeros(len(acts)); a[i]=1-t; a[j]=t
                p.append(a); labels.append(f'{acts[j]}{int(t*100)}')
    return np.array(p),labels


def build(ds, grid, mixed):
    acts=ds[0]['actions']; assert all(d['actions']==acts for d in ds)
    op,labels=options(acts,mixed); ags=[aggregate(d,grid) for d in ds]
    n=len(ags[0]['w']); k=len(op); rows=[]; low=[]; high=[]; titles=[]
    ub=np.ones((n,k)); c=np.zeros((n,k))
    def add(arr,lo=-np.inf,hi=np.inf,title=''):
        rows.append(np.asarray(arr).reshape(n*k)); low.append(lo); high.append(hi); titles.append(title)
    for i in range(n):
        a=np.zeros((n,k));a[i]=1;add(a,1,1,'one action per cell')
    if acts=='FCR':
        for i in range(n):
            if i%len(HANDS) in (0,1,2): ub[i,op[:,0]>0]=0
    for d,ag in zip(ds,ags):
        W=d['w'].sum(); c+=(ag['loss']@op.T)/W/len(ds)
        add(ag['loss']@op.T/W,hi=BUDGET['overall_regret'],title=d['study']+' overall regret')
        add(ag['bad05']@op.T/W,hi=BUDGET['tail_over_05'],title=d['study']+' costly action mass >0.5bb')
        add(ag['bad10']@op.T/W,hi=BUDGET['tail_over_10'],title=d['study']+' costly action mass >1bb')
        for a in range(len(acts)):
            target=ag['freq'][:,a].sum()/W
            add(ag['w'][:,None]*op[:,a]/W,target-.08,target+.08,d['study']+' overall '+acts[a])
        # A frequency match may not erase an entire value/draw group.
        comp_groups=((0,), (1,2), (3,4,5,6), (7,8,9), (10,11), (12,13,14))
        for hs in comp_groups:
            cells=np.isin(np.arange(n)%len(HANDS),hs);mass=ag['w'][cells].sum()
            if mass/W<.025: continue
            target=ag['freq'][cells].sum(axis=0)/mass
            for a in range(len(acts)):
                lo=target[a]-.35; hi=target[a]+.35
                if acts=='FCR' and a in (1,2) and ag['freq'][:,2].sum()/W<.10:
                    lo=-np.inf;hi=np.inf
                add((ag['w']*cells)[:,None]*op[:,a]/mass,lo,hi,
                    d['study']+' composition '+str(hs)+' '+acts[a])
        # Candidate classes plus an independent, unchanged four-class diagnostic.
        for ref,tol in ((grid,.10),('four',.15)):
            names=sorted(set(board_class(b,ref) for b in d['board']))
            for name in names:
                mask=np.array([board_class(b,ref)==name for b in d['board']]); mass=d['w'][mask].sum()
                if mass/W<.01: continue
                cw=np.bincount(ag['ci'][mask],weights=d['w'][mask],minlength=n)
                cl=np.stack([np.bincount(ag['ci'][mask],weights=d['w'][mask]*d['loss'][mask,a],minlength=n) for a in range(len(acts))],axis=1)
                target=d['w'][mask]@d['freq'][mask]/mass
                add(cl@op.T/mass,hi=BUDGET['class_regret'],title=f"{d['study']} {ref} {name} regret")
                for a in range(len(acts)):
                    bottom=target[a]-tol
                    if acts[a]=='R' and target[a]>=.10: bottom=max(bottom,BUDGET['raise_retention']*target[a])
                    add(cw[:,None]*op[:,a]/mass,bottom,target[a]+tol,f"{d['study']} {ref} {name} {acts[a]}")
        if acts=='FCR':
            for group in ('made','unmade'):
                cells=np.array([(i%len(HANDS)<7)==(group=='made') for i in range(n)])
                target=ag['freq'][cells,2].sum()/W
                if target>=.015:
                    add((ag['w']*cells)[:,None]*op[:,2]/W,lo=BUDGET['raise_group_retention']*target,title=d['study']+' raise '+group)
        for i in range(n):
            if ag['w'][i]/W>=BUDGET['major_cell_share']:
                avg=ag['loss'][i]@op.T/ag['w'][i]
                ub[i,avg>BUDGET['major_cell_regret']]=0
    c+=((op>0).sum(axis=1)>1)[None,:]*.0002/n
    return dict(ds=ds,grid=grid,mixed=mixed,acts=acts,options=op,labels=labels,ags=ags,n=n,k=k,
                A=csr_matrix(np.stack(rows)),lb=np.array(low),ub=np.array(high),bound=ub,c=c.ravel(),constraint_titles=titles)


def relax(problem):
    A=problem['A'];lo=problem['lb'];hi=problem['ub'];eq=lo==hi
    from scipy.sparse import vstack
    less=np.isfinite(hi)&~eq;greater=np.isfinite(lo)&~eq
    res=linprog(problem['c'],A_ub=vstack((A[less],-A[greater])),b_ub=np.r_[hi[less],-lo[greater]],
                A_eq=A[eq],b_eq=lo[eq],bounds=list(zip(np.zeros_like(problem['bound'].ravel()),problem['bound'].ravel())),method='highs')
    return {'status':int(res.status),'feasible':bool(res.success),'message':res.message,
            'interpretation':'LP infeasible proves only incompatibility with stated screening budgets; never adaptive exploitability.'}


def complexity(sel, problem):
    op=problem['options'];m=sel.reshape(-1,len(HANDS))
    live=np.sum([ag['w'] for ag in problem['ags']],axis=0).reshape(m.shape)>0
    edges_h=int(((m[1:]!=m[:-1]) & live[1:] & live[:-1]).sum())
    edges_v=0
    for rs in LOGICAL_ROWS:
        for l,r in zip(rs,rs[1:]): edges_v+=int(((m[:,l]!=m[:,r]) & live[:,l] & live[:,r]).sum())
    mix=int((((op[sel]>0).sum(axis=1)>1) & live.ravel()).sum())
    runs=sum(int(len(v)>0)+(int((v[1:]!=v[:-1]).sum()) if len(v)>0 else 0) for v in (m[i,live[i]] for i in range(len(m))))
    return dict(mix_cells=mix,horizontal_boundaries=edges_h,vertical_boundaries=edges_v,
                row_action_runs=runs,score=edges_h+edges_v+3*mix)


def fit(problem):
    res=milp(problem['c'],integrality=np.ones(problem['n']*problem['k']),
             bounds=Bounds(0,problem['bound'].ravel()),
             constraints=LinearConstraint(problem['A'],problem['lb'],problem['ub']),
             options={'time_limit':8.,'mip_rel_gap':.01})
    if res.x is None:return None,{'status':int(res.status),'message':res.message}
    sel=res.x.reshape(problem['n'],problem['k']).argmax(axis=1)
    if not valid(sel,problem):return None,{'status':int(res.status),'message':'No valid integer incumbent'}
    return sel,{'status':int(res.status),'message':res.message,'mip_gap':float(res.mip_gap)}


def vector(sel,p):return np.eye(p['k'])[sel].ravel()
def valid(sel,p):
    if np.any(p['bound'][np.arange(p['n']),sel]<.5):return False
    v=p['A']@vector(sel,p)
    return bool(np.all(v>=p['lb']-2e-7) and np.all(v<=p['ub']+2e-7))


def smooth(sel,p):
    """Deterministic feasible region merges. Never add a hand/flop category."""
    nc=p['n']//len(HANDS); nh=len(HANDS); current=sel.copy();score=complexity(current,p)['score'];history=[]
    regions=[]
    for width in range(nc,0,-1):
        for start in range(nc-width+1):
            cols=range(start,start+width)
            for group in ((0,1,2,3,4,5,6),(7,8,9,10,11),(12,13,14))+LOGICAL_ROWS:
                regions.append(np.array([c*nh+h for c in cols for h in group]))
            for h in range(nh):regions.append(np.array([c*nh+h for c in cols]))
    for repeat in range(3):
        changed=False
        for ix in regions:
            old=current[ix];best=None
            if len(set(old))==1: continue
            for act in range(p['k']):
                trial=current.copy();trial[ix]=act;sc=complexity(trial,p)['score']
                if sc>=score or not valid(trial,p): continue
                ev=float(p['c']@vector(trial,p));key=(sc,ev)
                if best is None or key<best[0]:best=(key,trial)
            if best is not None:
                before=score;current=best[1];score=best[0][0];changed=True
                history.append({'cells':ix.tolist(),'score_before':before,'score_after':score})
        if not changed:break
    return current,history


def summary(d,ag,sel,p):
    prob=p['options'][sel][ag['ci']];w=d['w'];W=w.sum()
    reg=(prob*d['loss']).sum(axis=1);base=(d['freq']*d['loss']).sum(axis=1)
    cand=w@prob/W;sf=w@d['freq']/W
    out={'solver':dict(zip(d['actions'],sf.tolist())),'human':dict(zip(d['actions'],cand.tolist())),
         'delta_pp':dict(zip(d['actions'],((cand-sf)*100).tolist())),
         'local_regret_bb':float(w@reg/W),'extra_loss_vs_mixed_bb':float(w@(reg-base)/W),
         'solver_local_regret_bb':float(w@base/W),
         'costly_action_mass_gt_05':float(w@((prob*(d['loss']>.5)).sum(axis=1))/W),
         'costly_action_mass_gt_10':float(w@((prob*(d['loss']>1)).sum(axis=1))/W),
         'max_positive_reach_combo_expected_regret_bb':float(reg[w>0].max()),'by_flop':{},'by_hand':{},'by_group':{}}
    for name,mask in ((c,ag['bi']==i) for i,c in enumerate(ag['classes'])):
        mass=w[mask].sum()
        out['by_flop'][name]={'share':float(mass/W),'solver':(w[mask]@d['freq'][mask]/mass).tolist(),
                              'human':(w[mask]@prob[mask]/mass).tolist(),'regret_bb':float(w[mask]@reg[mask]/mass)}
    for i,h in enumerate(HANDS):
        mask=d['hand']==i;mass=w[mask].sum()
        if mass>0:out['by_hand'][h]={'share':float(mass/W),'solver':(w[mask]@d['freq'][mask]/mass).tolist(),
                               'human':(w[mask]@prob[mask]/mass).tolist(),'regret_bb':float(w[mask]@reg[mask]/mass)}
    for group in dict.fromkeys(GROUPS):
        mask=np.isin(d['hand'],[i for i,g in enumerate(GROUPS) if g==group]);mass=w[mask].sum()
        if mass>0:out['by_group'][group]={'share':float(mass/W),'solver_action_mass':(w[mask]@d['freq'][mask]/W).tolist(),
                              'human_action_mass':(w[mask]@prob[mask]/W).tolist(),'regret_bb':float(w[mask]@reg[mask]/mass)}
    boardloss=[]
    for b in sorted(set(d['board'])):
        mask=d['board']==b;mass=w[mask].sum()
        if mass>0:boardloss.append({'board':b,'share':float(mass/W),'regret_bb':float(w[mask]@reg[mask]/mass)})
    out['worst_boards']=sorted(boardloss,key=lambda v:-v['regret_bb'])[:5]
    order=np.argsort(reg);cs=np.cumsum(w[order])/W
    out['weighted_regret_quantiles']={str(t):float(reg[order[min(np.searchsorted(cs,t),len(order)-1)]]) for t in (.5,.9,.95,.99)}
    return out


def evaluate_group(ds,grid,mixed,smoothing=True):
    p=build(ds,grid,mixed);rel=relax(p)
    result={'studies':[d['study'] for d in ds],'grid':grid,'mixed_allowed':mixed,'relaxation':rel}
    if not rel['feasible']:return result
    sel,stat=fit(p);result['integer_solve']=stat
    if sel is None:return result
    result['before_smoothing']=complexity(sel,p)
    history=[]
    if smoothing:sel,history=smooth(sel,p)
    result['complexity']=complexity(sel,p);result['region_merges']=len(history)
    result['classes']=p['ags'][0]['classes'];result['hands']=HANDS;result['options']=p['options'].tolist();result['labels']=p['labels']
    result['selected']=sel.reshape(-1,len(HANDS)).tolist()
    result['metrics']={d['study']:summary(d,ag,sel,p) for d,ag in zip(ds,p['ags'])}
    result['all_screening_gates_pass']=valid(sel,p)
    return result
