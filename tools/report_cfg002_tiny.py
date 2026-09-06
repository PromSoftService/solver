#!/usr/bin/env python3
from analyze_cfg002_compare import load, board_stats, analyze_cfg002, EPS

BCS=('ABx','Axx','BBx','Kxx','[Q-8]x','[7-4]x')
MADE=('Straight','Set/Trips','Two pair','Overpair','High underpair','Top pair','Second pair','Third pair','Weak pocket pair','High card')

def p(x): return round(100*x,1)
def line(k,z):
    print(k, '|FCR',p(z['fold']),p(z['call']),p(z['raise']),
          '|loss',round(z['loss_F'],4),round(z['loss_C'],4),round(z['loss_R'],4),
          '|best',z['best_pure'],round(z['best_loss'],4),'cover',p(z['best_cover']))

def main():
    _,r1=load('CFG001'); path,r2=load('CFG002'); a=analyze_cfg002(r2)
    print('TINY_BEGIN')
    print('DATA',path,'ROWS',len(r2),'EPS',EPS)
    s1,s2=board_stats(r1),board_stats(r2)
    print('BOARD')
    for b in BCS:
        x,y=s1[b],s2[b]
        print(b,'|33 SDF/C/R',p(x['sdf']),p(x['call']),p(x['raise']),'|75 SDF/C/R',p(y['sdf']),p(y['call']),p(y['raise']))
    print('CORE')
    for m in MADE:
        if m in a['core']: line(m,a['core'][m])
    print('MADE_BY_BOARD')
    for b in BCS:
        for m in ('Set/Trips','Two pair','Straight','Overpair','High underpair','Top pair','Second pair','Third pair','Weak pocket pair'):
            k=str((b,m))
            if k in a['made_by_board']: line(k,a['made_by_board'][k])
    print('WEAK_MIDDLE')
    for k,z in a['weak_pair_by_middle'].items(): line(k,z)
    print('DIRECT_DRAWS')
    for k,z in a['direct_draw_detail'].items(): line(k,z)
    print('BACKDOOR')
    for k,z in a['backdoor_detail'].items(): line(k,z)
    print('HIGHCARDS_SELECTED')
    for k,z in a['highcard_detail'].items():
        if any("'"+h+"'" in k for h in ('AK','AQ','AJ','KQ','KJ','AT')): line(k,z)
    print('PAIR_SPLITS')
    for k,z in a['pair_kicker_detail'].items():
        # only categories that challenge pure call materially
        if z['best_pure']!='C' or z['loss_C']>EPS or z['cover_C']<0.70:
            line(k,z)
    print('TINY_END')

if __name__=='__main__': main()
