#!/usr/bin/env python3
from analyze_cfg002_compare import load, RCHR

PAIR_NORMAL = {'Overpair','High underpair','Top pair','Second pair','Third pair'}
FIRST3 = {'A[K-J]x','A[T-2]x','BBx'}

def old_bc(r):
    fx=r['fx']; hi,mid=fx['top'],fx['mid']
    if hi==14:
        return 'A[K-J]x' if mid>=11 else 'A[T-2]x'
    br=sorted([c[0] for c in r['board'].split()])
    # use numeric ranks through fx values instead
    if sum(1 for x in (fx['top'],fx['mid'],fx['low']) if x>=10)>=2:
        return 'BBx'
    if hi==13:
        return 'K[9-2]x'
    if 8<=hi<=12:
        return '[Q-8]x'
    return '[7-4]x'

def stats(rows, pred):
    xs=[r for r in rows if pred(r)]
    w=sum(r['w'] for r in xs)
    if not w: return None
    out={'w':w,'n':len(xs)}
    for a,k in [('F','lf'),('C','lc'),('R','lr')]:
        out['loss_'+a]=sum(r['w']*r[k] for r in xs)/w
        out['freq_'+a]=sum(r['w']*r[{'F':'fold','C':'call','R':'raise'}[a]] for r in xs)/w
        out['cover_'+a]=sum(r['w']*(r[k]<=0.02) for r in xs)/w
    out['best']=min('FCR', key=lambda a:out['loss_'+a])
    return out

def emit(name,z):
    print(name,
          'w',round(z['w'],1),'n',z['n'],
          'FCR',*(round(100*z['freq_'+a],1) for a in 'FCR'),
          'lossFCR',*(round(z['loss_'+a],4) for a in 'FCR'),
          'coverFCR',*(round(100*z['cover_'+a],1) for a in 'FCR'),
          'best',z['best'])

def chosen_loss(rows, action_fn, pred):
    w=0.0; q=0.0
    for r in rows:
        if not pred(r): continue
        a=action_fn(r)
        loss={'F':r['lf'],'C':r['lc'],'R':r['lr']}[a]
        w += r['w']; q += r['w']*loss
    return (q/w if w else 0.0,w,q)

def main():
    path,rows=load('CFG002')
    for r in rows: r['oldbc']=old_bc(r)
    totalw=sum(r['w'] for r in rows)
    print('USER_SIMPLIFY_BEGIN',path,'rows',len(rows),'totalw',round(totalw,1))

    emit('SECOND_PAIR_ALL', stats(rows, lambda r:r['fx']['made']=='Second pair'))
    for b in ('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x'):
        z=stats(rows, lambda r,b=b:r['oldbc']==b and r['fx']['made']=='Second pair')
        if z: emit('SECOND_PAIR_'+b,z)

    # BDFD only here means no direct straight draw; if a third pair also has a gutshot/OESD,
    # it belongs to the common pair+straight-draw Call bucket instead.
    pred_third_bdfd = lambda r: r['oldbc'] in FIRST3 and r['fx']['made']=='Third pair' and r['fx']['bdfd'] and not r['fx']['sd']
    emit('THIRD_PAIR_BDFD_FIRST3_NODIRECT', stats(rows,pred_third_bdfd))
    for b in ('A[K-J]x','A[T-2]x','BBx'):
        z=stats(rows, lambda r,b=b:r['oldbc']==b and r['fx']['made']=='Third pair' and r['fx']['bdfd'] and not r['fx']['sd'])
        if z: emit('THIRD_PAIR_BDFD_'+b,z)

    emit('WEAK_POCKET_ALL', stats(rows, lambda r:r['fx']['made']=='Weak pocket pair'))

    pred_pair_gs = lambda r: r['fx']['made'] in PAIR_NORMAL and r['fx']['sd']=='Gutshot'
    emit('NORMAL_PAIR_PLUS_GUTSHOT_ALL',stats(rows,pred_pair_gs))
    for b in ('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x'):
        z=stats(rows, lambda r,b=b:r['oldbc']==b and r['fx']['made'] in PAIR_NORMAL and r['fx']['sd']=='Gutshot')
        if z: emit('NORMAL_PAIR_PLUS_GUTSHOT_'+b,z)

    # User's broad overcards+draw category. Version CORE merges BDFD and/or gutshot;
    # version ANYDRAW additionally absorbs OESD.
    pred_oc_core = lambda r: r['fx']['made']=='High card' and r['fx']['two_over'] and (r['fx']['bdfd'] or r['fx']['sd']=='Gutshot')
    pred_oc_any  = lambda r: r['fx']['made']=='High card' and r['fx']['two_over'] and (r['fx']['bdfd'] or r['fx']['sd'] in ('Gutshot','OESD'))
    emit('TWO_OVERCARDS_PLUS_BDFD_OR_GUTSHOT',stats(rows,pred_oc_core))
    emit('TWO_OVERCARDS_PLUS_ANY_DRAW',stats(rows,pred_oc_any))
    for b in ('BBx','[Q-8]x','[7-4]x'):
        z=stats(rows, lambda r,b=b:r['oldbc']==b and pred_oc_any(r))
        if z: emit('TWO_OVERCARDS_PLUS_ANY_DRAW_'+b,z)

    # Proposed human policy changes, counted once per row by precedence:
    # weak pocket -> F; second pair -> C; third pair+BDFD/no direct on first3 -> F;
    # all other normal pair+gutshot -> C; two overcards+any draw -> C.
    def selected(r):
        fx=r['fx']
        return (fx['made']=='Weak pocket pair' or fx['made']=='Second pair' or
                pred_third_bdfd(r) or pred_pair_gs(r) or pred_oc_any(r))
    def action(r):
        fx=r['fx']
        if fx['made']=='Weak pocket pair': return 'F'
        if fx['made']=='Second pair': return 'C'
        if pred_third_bdfd(r): return 'F'
        if pred_pair_gs(r): return 'C'
        if pred_oc_any(r): return 'C'
        raise AssertionError
    avg,w,q=chosen_loss(rows,action,selected)
    print('PROPOSED_CHANGED_UNION','w',round(w,1),'avg_loss',round(avg,4),'full_range_contribution',round(q/totalw,4),'weight_share_pct',round(100*w/totalw,1))
    print('USER_SIMPLIFY_END')

if __name__=='__main__': main()
