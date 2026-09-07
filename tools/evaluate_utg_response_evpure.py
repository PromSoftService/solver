#!/usr/bin/env python3
import json
import analyze_rng002_utg_response as u
import analyze_rng002_btn_followups as a

def P(A): return {q:float(q==A) for q in 'FCR'}

def eval_cells(cc,chooser):
    by={};T={k:0. for k in ('w','reg','sF','sC','sR','cF','cC','cR')}
    mapping={}
    for c,hs in cc.items():
      z={k:0. for k in T};mapping[c]={}
      for h,v in hs.items():
        A=chooser(c,h,v);mapping[c][h]=A;p=P(A);w=v['w'];z['w']+=w
        for q in 'FCR':z['s'+q]+=w*v[q];z['c'+q]+=w*p[q]
        z['reg']+=w*v['l'+A]
      W=z['w'];by[c]={'w':W,'reg':z['reg']/W}
      for q in 'FCR':by[c]['s'+q]=z['s'+q]/W;by[c]['c'+q]=z['c'+q]/W
      for k in T:T[k]+=z[k]
    W=T['w'];ov={'reg':T['reg']/W}
    for q in 'FCR':ov['s'+q]=T['s'+q]/W;ov['c'+q]=T['c'+q]/W
    return {'mapping':mapping,'by':by,'overall':ov}

def best(c,h,v): return min('FCR',key=lambda q:v['l'+q])

def intuitive(c,h,v):
    # Keep EV-best folds, but normalize nonfold action structure for human use.
    if c=='A[K-J]x':
      return 'F' if h in ('Air','BDFD 0OC','Underpair 9-') else 'C'
    if c=='A[T-2]x':
      if h=='Air':return 'F'
      if h in ('Two pair+','OESD','Second pair','Third pair'):return 'R'
      return 'C'
    if c=='BBx':
      if h in ('Air','BDFD 0OC','BDFD 1OC','X-high 1OC'):return 'F'
      return 'C'
    if c=='K[9-2]x':
      if h in ('Air','X-high 1OC'):return 'F'
      if h in ('Two pair+','Overpair','Top pair','OESD','Gutshot','Second pair','Third pair'):return 'R'
      return 'C'
    if c=='[Q-8]x':
      if h in ('Air','X-high 1OC','BDFD 0OC'):return 'F'
      if h in ('Two pair+','OESD'):return 'R'
      return 'C'
    if c=='[7-4]x':
      if h in ('Air','X-high 1OC','BDFD 0OC'):return 'F'
      if h in ('Two pair+','OESD','Top pair'):return 'R'
      return 'C'
    return 'C'

def main():
 p,rows=u.load();cc=u.cells(rows,'b6');out={'pure_best':eval_cells(cc,best),'intuitive':eval_cells(cc,intuitive)}
 print('UTG_RESPONSE_EVPURE_BEGIN');print(json.dumps(a.rnd(out),ensure_ascii=False,separators=(',',':')));print('UTG_RESPONSE_EVPURE_END')
if __name__=='__main__':main()
