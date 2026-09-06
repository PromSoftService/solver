#!/usr/bin/env python3
import csv, glob, re
from collections import defaultdict
from analyze_cfg002_compare import features

# Exact representative flop lists used by poker_flop_trainer_v4_fixed.html.
CLASSES = [
    ('ABB', {'AKQ','AKJ','AKT','AQJ','AQT','AJT'}),
    ('A[K/Q]x', {f'A{b}{x}' for b in 'KQ' for x in '98765432'}),
    ('BBB', {'KQJ','KQT','KJT','QJT'}),
    ('BBx dis', {'KQ7','KJ4','KJ3','KT3','QJ5','QJ4','QT3','JT6','JT4'}),
    ('K/Qx dis', {'K97','K84','K73','K62','K52','Q95','Q84','Q73','Q62','Q52'}),
    ('A[J-T][9-5]', {f'A{b}{x}' for b in 'JT' for x in '98765'}),
    ('K/Qx con', {'K98','K87','K76','K65','K54','Q98','Q87','Q76','Q65','Q54','Q43'}),
    ('A[9-7]x', {f'A{b}{x}' for b in '987' for x in '65432' if 'AKQJT98765432'.index(x) > 'AKQJT98765432'.index(b)}),
    ('[J-8]x dis', {'J84','J73','J62','T74','T63','T52','964','953','842','832'}),
    ('A[J-T][4-2]', {f'A{b}{x}' for b in 'JT' for x in '432'}),
    ('[J-8]x con', {'JT8','J98','J87','T98','T87','T76','987','876','865'}),
    ('[7-4]x', {'765','754','743','742','654','643','642','632','543','532','432'}),
    ('A[6-2]', {'A65','A64','A63','A62','A54','A53','A52','A43','A42','A32'}),
]
CLASS_OF = {flop:k for k,flops in CLASSES for flop in flops}

ORDER='AKQJT98765432'
VAL={r:13-i for i,r in enumerate(ORDER)}
def f(s): return float(str(s).replace(',','.'))
def rank_sig(board):
    rs=re.findall(r'([2-9TJQKA])[cdhs]', board)
    return ''.join(sorted(rs,key=lambda r:VAL[r], reverse=True))

def hand_cat(fx):
    m=fx['made']
    if m=='Weak pocket pair': return 'Weak pair'
    if m=='Third pair': return '3-rd pair'
    if m=='Second pair': return '2-nd pair'
    if m=='Top pair': return 'Top pair'
    if m=='Overpair': return 'Overpair'
    if m!='High card': return None
    # Legacy trainer puts both OESD and gutshot into the row labelled Gutshot.
    if fx['sd'] in ('OESD','Gutshot'): return 'Gutshot'
    if fx['bdfd']: return 'BDFD'
    return 'Air'

p=sorted(glob.glob('datasets/DS__RNG001__CFG001__NOD002__BRD001__RUN-*.csv'))[-1]
agg=defaultdict(lambda:[0.0,0.0,0.0,0.0,0]) # w, wb, wlossB, wlossX, nrows
board=defaultdict(lambda:defaultdict(lambda:[0.0,0.0])) # class -> board -> w, wb
board_seen=defaultdict(set)
all_board=defaultdict(lambda:[0.0,0.0])
with open(p,encoding='utf-8-sig',newline='') as fh:
    for x in csv.DictReader(fh):
        sig=rank_sig(x['board']); k=CLASS_OF.get(sig)
        if k is None: continue
        w=f(x['reach_probability']); bf=f(x['bet_frequency']); lb=f(x['loss_if_bet_utg']); lx=f(x['loss_if_check_utg'])
        b=board[k][sig]; b[0]+=w; b[1]+=w*bf
        board_seen[k].add(sig)
        q=all_board[k]; q[0]+=w; q[1]+=w*bf
        fx=features(x['board'],x['combo']); c=hand_cat(fx)
        if c is None: continue
        a=agg[(k,c)]; a[0]+=w; a[1]+=w*bf; a[2]+=w*lb; a[3]+=w*lx; a[4]+=1

cats=['Weak pair','3-rd pair','2-nd pair','BDFD','Air','Top pair','Overpair','Gutshot']
print('UTG_OLD13_REANALYSIS')
print('dataset',p)
print('BOARD_CLASS_SUMMARY name n expected reachBet boardAvg min max')
for k,flops in CLASSES:
    vals=[100*wb/w for w,wb in board[k].values() if w]
    w,wb=all_board[k]
    print(k,'n',len(vals),'expected',len(flops),'reachBet',f'{100*wb/w:.1f}' if w else '--','boardAvg',f'{sum(vals)/len(vals):.1f}' if vals else '--','min',f'{min(vals):.1f}' if vals else '--','max',f'{max(vals):.1f}' if vals else '--')
print('CELL_SUMMARY: betPct/lossB/lossX/weight')
for c in cats:
    out=[]
    for k,_ in CLASSES:
        a=agg.get((k,c))
        if not a or a[0]==0:
            out.append(f'{k}=--')
        else:
            w,wb,lb,lx,n=a
            out.append(f'{k}={100*wb/w:.1f}/{lb/w:.4f}/{lx/w:.4f}/{w:.1f}')
    print(c,' | '.join(out))
