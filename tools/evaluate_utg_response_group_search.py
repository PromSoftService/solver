#!/usr/bin/env python3
import itertools, json
from collections import defaultdict
import analyze_rng002_utg_response as u
import analyze_rng002_btn_followups as a


def P(A): return {q: float(q == A) for q in 'FCR'}
def mix(F=0.,R=0.): return {'F':F,'C':1-F-R,'R':R}

def group(x):
    c=x['b6']
    if c=='A[K-J]x': return 'HIGH'
    if c in ('A[T-2]x','BBx'): return 'MID'
    return 'LOW'

def cells(rows):
    d=defaultdict(lambda:defaultdict(float))
    for x in rows:
        z=d[(group(x),x['detail'])];w=x['w'];z['w']+=w
        for q in 'FCR':z[q]+=w*x[q];z['l'+q]+=w*x['l'+q]
    out={}
    for (g,h),z in d.items():
        W=z['w'];v={'w':W}
        for q in 'FCR':v[q]=z[q]/W;v['l'+q]=z['l'+q]/W
        out.setdefault(g,{})[h]=v
    return out

def eval_group(hs,rule):
    W=sum(v['w'] for v in hs.values());s={q:0. for q in 'FCR'};c={q:0. for q in 'FCR'};reg=0.
    for h,v in hs.items():
        p=rule(h);w=v['w']
        for q in 'FCR':s[q]+=w*v[q];c[q]+=w*p[q]
        reg+=w*sum(p[q]*v['l'+q] for q in 'FCR')
    s={q:s[q]/W for q in 'FCR'};c={q:c[q]/W for q in 'FCR'}
    return {'w':W,'reg':reg/W,'solver':s,'cand':c,'maxerr':max(abs(c[q]-s[q]) for q in 'FCR')}

def high_rule(h):
    return P('F') if h in ('Air','BDFD 0OC','Underpair 9-') else P('C')

MID_POOLS={
 'TP_OESD':{'Two pair+','OESD'},
 'TP_OESD_GS':{'Two pair+','OESD','Gutshot'},
 'TP':{'Two pair+'},
 'TP_OESD_GS_2P3P':{'Two pair+','OESD','Gutshot','Second pair','Third pair'},
}
LOW_POOLS={
 'TP_OESD':{'Two pair+','OESD'},
 'TP_OESD_GS':{'Two pair+','OESD','Gutshot'},
 'TP_OESD_TOP_OVP':{'Two pair+','OESD','Top pair','Overpair'},
 'BROAD':{'Two pair+','OESD','Gutshot','Top pair','Overpair'},
}

def mid_rule(b0,b1,u9,pool,rr):
    rp=MID_POOLS[pool]
    def r(h):
        if h in ('Air','X-high 1OC'):return P('F')
        if h=='BDFD 0OC':return mix(F=b0)
        if h=='BDFD 1OC':return mix(F=b1)
        if h=='Underpair 9-':return mix(F=u9)
        if h in rp:return mix(R=rr)
        return P('C')
    return r

def low_rule(x2,b0,b1,pool,rr):
    rp=LOW_POOLS[pool]
    def r(h):
        if h in ('Air','X-high 1OC'):return P('F')
        if h=='X-high 2OC':return mix(F=x2)
        if h=='BDFD 0OC':return mix(F=b0)
        if h=='BDFD 1OC':return mix(F=b1)
        if h in rp:return mix(R=rr)
        return P('C')
    return r

def search(hs,kind):
    out=[]
    if kind=='MID':
      for b0,b1,u9,pool,rr in itertools.product((0,.5,1),(0,.5,1),(0,.25),MID_POOLS,(0,.25,.4,.5,.6,.75,1)):
        name={'bdfd0_fold':b0,'bdfd1_fold':b1,'under9_fold':u9,'raise_pool':pool,'raise_rate':rr}
        m=eval_group(hs,mid_rule(b0,b1,u9,pool,rr));out.append((m['reg'],m['maxerr'],name,m))
    else:
      for x2,b0,b1,pool,rr in itertools.product((0,.25,.5,.75,1),(0,.5,1),(0,.25,.5,1),LOW_POOLS,(0,.25,.4,.5,.6,.75,1)):
        name={'xhigh2_fold':x2,'bdfd0_fold':b0,'bdfd1_fold':b1,'raise_pool':pool,'raise_rate':rr}
        m=eval_group(hs,low_rule(x2,b0,b1,pool,rr));out.append((m['reg'],m['maxerr'],name,m))
    res={}
    for tol in (.03,.05,.075,.10):
        q=[z for z in out if z[1]<=tol];q.sort(key=lambda z:(z[0],z[1]))
        res[str(tol)]=[{'params':n,'metrics':m} for _,_,n,m in q[:8]]
    out.sort(key=lambda z:(z[0],z[1]));res['ev_first']=[{'params':n,'metrics':m} for _,_,n,m in out[:5]]
    return res

def package(high,mid,low):
    W=high['w']+mid['w']+low['w'];o={'reg':0.}
    for m in (high,mid,low):o['reg']+=m['w']*m['reg']/W
    for q in 'FCR':
        o['solver'+q]=sum(m['w']*m['solver'][q] for m in (high,mid,low))/W
        o['cand'+q]=sum(m['w']*m['cand'][q] for m in (high,mid,low))/W
    return o

def main():
    p,rows=u.load();cc=cells(rows);hi=eval_group(cc['HIGH'],high_rule);ms=search(cc['MID'],'MID');ls=search(cc['LOW'],'LOW')
    packs={}
    for tol in ('0.03','0.05','0.075','0.1'):
        if ms[tol] and ls[tol]:
            m=ms[tol][0];l=ls[tol][0];packs[tol]={'mid':m['params'],'low':l['params'],'overall':package(hi,m['metrics'],l['metrics'])}
    out={'dataset':p,'high':hi,'mid_search':ms,'low_search':ls,'packages':packs}
    print('UTG_RESPONSE_GROUP_SEARCH_BEGIN');print(json.dumps(a.rnd(out),ensure_ascii=False,separators=(',',':')));print('UTG_RESPONSE_GROUP_SEARCH_END')
if __name__=='__main__':main()
