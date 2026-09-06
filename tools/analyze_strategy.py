#!/usr/bin/env python3
import csv, glob, json, os
from collections import defaultdict

RANK = {r:i for i,r in enumerate('23456789TJQKA', start=2)}
STRAIGHTS = [
    {14,13,12,11,10}, {13,12,11,10,9}, {12,11,10,9,8},
    {11,10,9,8,7}, {10,9,8,7,6}, {9,8,7,6,5},
    {8,7,6,5,4}, {7,6,5,4,3}, {6,5,4,3,2}, {14,5,4,3,2}
]
EPS = 0.02


def fnum(s):
    if s is None or s == '': return 0.0
    return float(str(s).replace(',', '.'))

def cards_from_board(board): return board.split()
def cards_from_combo(combo): return [combo[:2], combo[2:4]]
def ranks(cards): return [RANK[c[0]] for c in cards]
def suits(cards): return [c[1] for c in cards]

def board_class(board):
    hi, mid, lo = sorted(ranks(cards_from_board(board)), reverse=True)
    if hi == 14:
        return 'A[K-J]x' if mid >= 11 else 'A[T-2]x'
    if sum(1 for r in (hi,mid,lo) if r >= 10) >= 2:
        return 'BBx'
    if hi == 13:
        return 'K[9-2]x'
    if 8 <= hi <= 12:
        return '[Q-8]x'
    gaps = (hi-mid-1)+(mid-lo-1)
    return '[7-4]x con' if gaps <= 1 else '[7-4]x dis'

def has_straight(rs):
    u=set(rs)
    return any(w <= u for w in STRAIGHTS)

def straight_draw_kind(br, hr):
    u=set(br+hr); missing=set()
    for w in STRAIGHTS:
        if len(w & u)==4: missing |= (w-u)
    if len(missing)>=2: return 'OESD/8-out'
    if len(missing)==1: return 'Gutshot'
    return None

def has_bdsd(br, hr):
    u=set(br+hr); hole_contrib=set(hr)-set(br)
    if not hole_contrib: return False
    for w in STRAIGHTS:
        if len(w & u)==3 and len(w-u)==2 and (w & hole_contrib): return True
    return False

def has_bdfd(bc,hc):
    hs=suits(hc)
    return hs[0]==hs[1] and hs[0] in suits(bc)

def hand_category(board, combo):
    bc=cards_from_board(board); hc=cards_from_combo(combo)
    br=ranks(bc); hr=ranks(hc)
    counts=defaultdict(int)
    for r in br+hr: counts[r]+=1
    if has_straight(br+hr) or max(counts.values())>=3 or sum(v>=2 for v in counts.values())>=2:
        return 'Two pair+'
    top,mid,low=sorted(br,reverse=True)
    if hr[0]==hr[1]:
        pr=hr[0]
        if pr>top: return 'Overpair'
        if pr>mid: return 'High underpair'
        if pr<mid: return 'Weak pair'
    matched=[r for r in hr if r in br]
    if matched:
        m=max(matched)
        if m==top: return 'Top pair'
        if m==mid: return 'Second pair'
        return 'Third pair'
    sd=straight_draw_kind(br,hr)
    if sd: return sd
    bdfd=has_bdfd(bc,hc); bdsd=has_bdsd(br,hr); two_over=min(hr)>top
    if two_over and bdfd: return 'Overcards + BDFD'
    if bdfd and bdsd: return 'BDFD + BDSD'
    if bdfd: return 'BDFD only'
    if bdsd: return 'BDSD only'
    rs=''.join(sorted((hc[0][0],hc[1][0]), key=lambda x:RANK[x], reverse=True))
    if rs=='AK': return 'Bare AK'
    if rs=='AQ': return 'Bare AQ'
    return 'Air / Nothing'

def newagg():
    return {'w':0.0,'f':0.0,'c':0.0,'r':0.0,'lf':0.0,'lc':0.0,'lr':0.0,'okf':0.0,'okc':0.0,'okr':0.0,'rows':0}
def add(a,row,w):
    a['w']+=w; a['f']+=w*row['fold']; a['c']+=w*row['call']; a['r']+=w*row['raise']
    a['lf']+=w*row['lf']; a['lc']+=w*row['lc']; a['lr']+=w*row['lr']
    a['okf']+=w*(row['lf']<=EPS); a['okc']+=w*(row['lc']<=EPS); a['okr']+=w*(row['lr']<=EPS); a['rows']+=1
def finish(a):
    w=a['w'] or 1.0
    return {'weight':a['w'],'rows':a['rows'],'fold':a['f']/w,'call':a['c']/w,'raise':a['r']/w,'sdf':(a['c']+a['r'])/w,
            'loss_F':a['lf']/w,'loss_C':a['lc']/w,'loss_R':a['lr']/w,
            'cover_F_002':a['okf']/w,'cover_C_002':a['okc']/w,'cover_R_002':a['okr']/w}

def main():
    files=sorted(glob.glob('datasets/DS__RNG001__CFG001__BRD001__RUN-*.csv'))
    if not files: raise SystemExit('dataset not found')
    path=files[-1]; rows=[]
    with open(path,encoding='utf-8-sig',newline='') as f:
        for x in csv.DictReader(f):
            row={'board':x['board'],'combo':x['combo'],'w':fnum(x['reach_probability']),
                 'fold':fnum(x['fold_frequency']),'call':fnum(x['call_frequency']),'raise':fnum(x['raise_frequency']),
                 'lf':fnum(x['loss_if_fold_bb']),'lc':fnum(x['loss_if_call_bb']),'lr':fnum(x['loss_if_raise_bb'])}
            row['bc']=board_class(row['board']); row['cat']=hand_category(row['board'],row['combo']); rows.append(row)

    per_board={}
    for row in rows: add(per_board.setdefault(row['board'],newagg()),row,row['w'])
    bcm=defaultdict(lambda:{'n':0,'f':0.0,'c':0.0,'r':0.0})
    for b,a in per_board.items():
        z=finish(a); q=bcm[board_class(b)]; q['n']+=1; q['f']+=z['fold']; q['c']+=z['call']; q['r']+=z['raise']
    board_stats={}
    for bc,q in bcm.items():
        n=q['n']; board_stats[bc]={'boards':n,'fold':q['f']/n,'call':q['c']/n,'raise':q['r']/n,'sdf':(q['c']+q['r'])/n}
    low=[v for k,v in board_stats.items() if k.startswith('[7-4]x')]
    if low:
        n=sum(v['boards'] for v in low); m={'boards':n}
        for key in ('fold','call','raise','sdf'): m[key]=sum(v[key]*v['boards'] for v in low)/n
        board_stats['[7-4]x merged']=m

    agg=defaultdict(newagg); total=defaultdict(newagg); special=defaultdict(newagg)
    for row in rows:
        add(agg[(row['bc'],row['cat'])],row,row['w']); add(total[row['cat']],row,row['w'])
        hc=cards_from_combo(row['combo']); rs=''.join(sorted((hc[0][0],hc[1][0]),key=lambda x:RANK[x],reverse=True))
        if rs in ('AK','AQ','AJ','KQ') and row['cat'] in ('Bare AK','Bare AQ','Air / Nothing','BDSD only','BDFD only','BDFD + BDSD','Overcards + BDFD'):
            add(special[(row['bc'],rs,row['cat'])],row,row['w'])
    cat_by={}
    for (bc,cat),a in agg.items(): cat_by.setdefault(cat,{})[bc]=finish(a)

    def policy(row):
        c=row['cat']; b=row['bc']
        if c=='Two pair+': return 'R'
        if c in ('Overpair','High underpair','Top pair','Second pair','Third pair'): return 'C'
        if c=='Weak pair': return 'F' if b in ('A[K-J]x','A[T-2]x','BBx') else 'C'
        if c in ('OESD/8-out','Gutshot','BDFD + BDSD'): return 'R'
        if c in ('Air / Nothing','Bare AK','Bare AQ','BDFD only','BDSD only'): return 'F'
        return None
    p_loss=p_w=p_ok=0.0; rule=defaultdict(newagg)
    for row in rows:
        act=policy(row)
        if not act: continue
        loss=row['lf'] if act=='F' else row['lc'] if act=='C' else row['lr']
        p_loss+=row['w']*loss; p_w+=row['w']; p_ok+=row['w']*(loss<=EPS); add(rule[(row['cat'],act)],row,row['w'])
    rules={}
    for (cat,act),a in rule.items():
        z=finish(a); z['policy_action']=act; z['policy_loss']=z['loss_'+act]; rules[f'{cat}->{act}']=z
    result={'dataset':path,'rows':len(rows),'boards':len(per_board),'epsilon_bb':EPS,'board_stats':board_stats,
            'category_totals':{k:finish(v) for k,v in total.items()},'category_by_board_class':cat_by,
            'special_highcards':{f'{bc}|{rs}|{cat}':finish(a) for (bc,rs,cat),a in special.items()},
            'policy_summary':{'weighted_mean_loss_bb':p_loss/p_w,'coverage_within_0.02':p_ok/p_w,'assigned_weight':p_w},'policy_rules':rules}
    os.makedirs('analysis',exist_ok=True); out='analysis/BRD001_strategy_analysis.json'
    with open(out,'w',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2)
    print('SUMMARY_JSON_BEGIN'); print(json.dumps(result,ensure_ascii=False,separators=(',',':'))); print('SUMMARY_JSON_END')

if __name__=='__main__': main()
