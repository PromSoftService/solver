#!/usr/bin/env python3
import csv, glob, json, os
from collections import defaultdict

RANK = {r:i for i,r in enumerate('23456789TJQKA', start=2)}
RCHR = {v:k for k,v in RANK.items()}
STRAIGHTS = [
    {14,13,12,11,10}, {13,12,11,10,9}, {12,11,10,9,8},
    {11,10,9,8,7}, {10,9,8,7,6}, {9,8,7,6,5},
    {8,7,6,5,4}, {7,6,5,4,3}, {6,5,4,3,2}, {14,5,4,3,2}
]
EPS = 0.02
ACTIONS = ('F','C','R')


def fnum(s):
    if s is None or s == '': return 0.0
    return float(str(s).replace(',', '.'))

def bc(board): return board.split()
def hc(combo): return [combo[:2], combo[2:4]]
def ranks(cards): return [RANK[c[0]] for c in cards]
def suits(cards): return [c[1] for c in cards]

def board_class(board):
    hi, mid, lo = sorted(ranks(bc(board)), reverse=True)
    if hi == 14:
        return 'ABx' if mid >= 10 else 'Axx'
    if sum(1 for r in (hi,mid,lo) if r >= 10) >= 2:
        return 'BBx'
    if hi == 13:
        return 'Kxx'
    if 8 <= hi <= 12:
        return '[Q-8]x'
    return '[7-4]x'

def has_straight(rs):
    u=set(rs)
    return any(w <= u for w in STRAIGHTS)

def straight_draw_kind(br, hr):
    u=set(br+hr); missing=set()
    for w in STRAIGHTS:
        if len(w & u)==4: missing |= (w-u)
    if len(missing)>=2: return 'OESD'
    if len(missing)==1: return 'Gutshot'
    return None

def bdsd_paths(br,hr):
    u=set(br+hr); hole_contrib=set(hr)-set(br); n=0
    if not hole_contrib: return 0
    for w in STRAIGHTS:
        if len(w & u)==3 and len(w-u)==2 and (w & hole_contrib): n += 1
    return n

def has_bdfd(board_cards,hole_cards):
    hs=suits(hole_cards)
    return hs[0]==hs[1] and hs[0] in suits(board_cards)

def features(board, combo):
    board_cards=bc(board); hole_cards=hc(combo)
    br=ranks(board_cards); hr=ranks(hole_cards)
    top,mid,low=sorted(br, reverse=True)
    counts=defaultdict(int)
    for r in br+hr: counts[r]+=1
    straight=has_straight(br+hr)
    if straight:
        made='Straight'
    elif max(counts.values())>=3:
        made='Set/Trips'
    elif sum(v>=2 for v in counts.values())>=2:
        made='Two pair'
    elif hr[0]==hr[1]:
        pr=hr[0]
        if pr>top: made='Overpair'
        elif pr>mid: made='High underpair'
        elif pr<mid: made='Weak pocket pair'
        else: made='Pocket pair other'
    else:
        matched=[r for r in hr if r in br]
        if matched:
            m=max(matched)
            made='Top pair' if m==top else 'Second pair' if m==mid else 'Third pair'
        else:
            made='High card'
    sd=None if straight else straight_draw_kind(br,hr)
    bdfd=has_bdfd(board_cards,hole_cards)
    paths=bdsd_paths(br,hr)
    rs=''.join(sorted((hole_cards[0][0],hole_cards[1][0]), key=lambda x:RANK[x], reverse=True))
    kicker=None
    if made in ('Top pair','Second pair','Third pair'):
        pair_rank = top if made=='Top pair' else mid if made=='Second pair' else low
        other = hr[1] if hr[0]==pair_rank else hr[0]
        kicker=RCHR[other]
    draw_bits=[]
    if sd: draw_bits.append(sd)
    if bdfd: draw_bits.append('BDFD')
    if paths and not sd: draw_bits.append('BDSD')
    draw=' + '.join(draw_bits) if draw_bits else 'no draw'
    return {
        'made':made, 'sd':sd, 'bdfd':bdfd, 'bdsd_paths':paths, 'draw':draw,
        'hole':rs, 'kicker':kicker, 'top':top, 'mid':mid, 'low':low,
        'two_over': min(hr)>top, 'one_or_more_over': max(hr)>top,
        'pocket_rank': hr[0] if hr[0]==hr[1] else None,
    }

def newagg():
    return {'w':0.0,'f':0.0,'c':0.0,'r':0.0,'lf':0.0,'lc':0.0,'lr':0.0,'okf':0.0,'okc':0.0,'okr':0.0,'rows':0}
def add(a,row):
    w=row['w']; a['w']+=w; a['rows']+=1
    a['f']+=w*row['fold']; a['c']+=w*row['call']; a['r']+=w*row['raise']
    a['lf']+=w*row['lf']; a['lc']+=w*row['lc']; a['lr']+=w*row['lr']
    a['okf']+=w*(row['lf']<=EPS); a['okc']+=w*(row['lc']<=EPS); a['okr']+=w*(row['lr']<=EPS)
def finish(a):
    w=a['w'] or 1.0
    z={'weight':a['w'],'rows':a['rows'],'fold':a['f']/w,'call':a['c']/w,'raise':a['r']/w,
       'loss_F':a['lf']/w,'loss_C':a['lc']/w,'loss_R':a['lr']/w,
       'cover_F':a['okf']/w,'cover_C':a['okc']/w,'cover_R':a['okr']/w}
    best=min(ACTIONS,key=lambda x:z['loss_'+x])
    z['best_pure']=best; z['best_loss']=z['loss_'+best]; z['best_cover']=z['cover_'+best]
    return z

def load(cfg):
    files=sorted(glob.glob(f'datasets/DS__RNG001__{cfg}__BRD001__RUN-*.csv'))
    if not files: raise SystemExit(f'{cfg} dataset not found')
    path=files[-1]; rows=[]
    with open(path,encoding='utf-8-sig',newline='') as f:
        for x in csv.DictReader(f):
            row={'board':x['board'],'combo':x['combo'],'w':fnum(x['reach_probability']),
                 'fold':fnum(x['fold_frequency']),'call':fnum(x['call_frequency']),'raise':fnum(x['raise_frequency']),
                 'lf':fnum(x['loss_if_fold_bb']),'lc':fnum(x['loss_if_call_bb']),'lr':fnum(x['loss_if_raise_bb'])}
            row['bc']=board_class(row['board']); row['fx']=features(row['board'],row['combo']); rows.append(row)
    return path,rows

def board_stats(rows):
    pb=defaultdict(newagg)
    for r in rows: add(pb[r['board']],r)
    tmp=defaultdict(lambda:{'n':0,'f':0.0,'c':0.0,'r':0.0})
    for b,a in pb.items():
        z=finish(a); q=tmp[board_class(b)]; q['n']+=1; q['f']+=z['fold']; q['c']+=z['call']; q['r']+=z['raise']
    out={}
    for k,q in tmp.items():
        n=q['n']; out[k]={'boards':n,'fold':q['f']/n,'call':q['c']/n,'raise':q['r']/n,'sdf':(q['c']+q['r'])/n}
    return out

def aggregate(rows, keyfn, min_weight=0):
    d=defaultdict(newagg)
    for r in rows: add(d[keyfn(r)],r)
    out={}
    for k,a in d.items():
        if a['w']>=min_weight: out[str(k)]=finish(a)
    return out

def analyze_cfg002(rows):
    core=aggregate(rows, lambda r:r['fx']['made'])
    made_by_board=aggregate(rows, lambda r:(r['bc'],r['fx']['made']))
    made_draw=aggregate(rows, lambda r:(r['bc'],r['fx']['made'],r['fx']['draw']), min_weight=250)
    pair_kicker=aggregate(rows, lambda r:(r['bc'],r['fx']['made'],r['fx']['kicker'],r['fx']['draw']), min_weight=250)
    weak_by_mid=aggregate([r for r in rows if r['fx']['made']=='Weak pocket pair'],
                          lambda r:(r['bc'],RCHR[r['fx']['mid']]))
    highcard=aggregate([r for r in rows if r['fx']['made']=='High card'],
                       lambda r:(r['bc'],r['fx']['hole'],r['fx']['draw']), min_weight=250)
    draw_only=aggregate([r for r in rows if r['fx']['made']=='High card' and r['fx']['sd']],
                        lambda r:(r['bc'],r['fx']['sd'],'BDFD' if r['fx']['bdfd'] else 'noBDFD'))
    backdoor=aggregate([r for r in rows if r['fx']['made']=='High card' and not r['fx']['sd']],
                       lambda r:(r['bc'],'BDFD' if r['fx']['bdfd'] else 'noBDFD',
                                 'BDSD' if r['fx']['bdsd_paths'] else 'noBDSD'), min_weight=250)
    # Flag coarse groups that are not safely pure at the 0.02bb criterion.
    needs_split={}
    for k,z in core.items():
        if z['best_loss']>EPS or z['best_cover']<0.80:
            needs_split[k]=z
    return {'core':core,'made_by_board':made_by_board,'made_draw':made_draw,
            'pair_kicker_detail':pair_kicker,'weak_pair_by_middle':weak_by_mid,
            'highcard_detail':highcard,'direct_draw_detail':draw_only,
            'backdoor_detail':backdoor,'coarse_categories_needing_split':needs_split}

def main():
    p1,r1=load('CFG001'); p2,r2=load('CFG002')
    result={
      'epsilon_bb':EPS,
      'datasets':{'CFG001':p1,'CFG002':p2},
      'rows':{'CFG001':len(r1),'CFG002':len(r2)},
      'board_stats':{'CFG001':board_stats(r1),'CFG002':board_stats(r2)},
      'cfg002':analyze_cfg002(r2),
    }
    os.makedirs('analysis',exist_ok=True)
    with open('analysis/CFG002_strategy_analysis.json','w',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
    print('CFG002_REPORT_BEGIN')
    print(json.dumps(result,ensure_ascii=False,separators=(',',':')))
    print('CFG002_REPORT_END')

if __name__=='__main__': main()
