#!/usr/bin/env python3
import csv, glob, json
from collections import defaultdict
import analyze_strategy as a

RCHAR={v:k for k,v in a.RANK.items()}

def rs_label(combo):
    hc=a.cards_from_combo(combo)
    return ''.join(sorted((hc[0][0],hc[1][0]),key=lambda x:a.RANK[x],reverse=True))

def made_detail(board,combo):
    bc=a.cards_from_board(board); hc=a.cards_from_combo(combo)
    br=a.ranks(bc); hr=a.ranks(hc); allr=br+hr
    if a.has_straight(allr): return 'Straight'
    counts=defaultdict(int)
    for r in allr: counts[r]+=1
    if max(counts.values())>=3: return 'Set/Trips'
    if sum(v>=2 for v in counts.values())>=2: return 'Two pair'
    return None

def bdsd_count(board,combo):
    br=a.ranks(a.cards_from_board(board)); hr=a.ranks(a.cards_from_combo(combo))
    u=set(br+hr); hc=set(hr)-set(br)
    return sum(1 for w in a.STRAIGHTS if len(w & u)==3 and len(w-u)==2 and (w & hc))

def load():
    p=sorted(glob.glob('datasets/DS__RNG001__CFG001__BRD001__RUN-*.csv'))[-1]
    out=[]
    with open(p,encoding='utf-8-sig',newline='') as f:
        for x in csv.DictReader(f):
            r={'board':x['board'],'combo':x['combo'],'w':a.fnum(x['reach_probability']),
               'fold':a.fnum(x['fold_frequency']),'call':a.fnum(x['call_frequency']),'raise':a.fnum(x['raise_frequency']),
               'lf':a.fnum(x['loss_if_fold_bb']),'lc':a.fnum(x['loss_if_call_bb']),'lr':a.fnum(x['loss_if_raise_bb'])}
            r['bc']=a.board_class(r['board']); r['cat']=a.hand_category(r['board'],r['combo']); out.append(r)
    return out

def main():
    rows=load(); weak=defaultdict(a.newagg); draws=defaultdict(a.newagg); strong=defaultdict(a.newagg); dbl=defaultdict(a.newagg); high=defaultdict(a.newagg)
    for r in rows:
        bc_cards=a.cards_from_board(r['board']); hc=a.cards_from_combo(r['combo']); br=a.ranks(bc_cards)
        if r['cat']=='Weak pair':
            mid=sorted(br,reverse=True)[1]
            a.add(weak[(r['bc'],RCHAR[mid])],r,r['w'])
        if r['cat'] in ('Gutshot','OESD/8-out'):
            a.add(draws[(r['cat'],'BDFD' if a.has_bdfd(bc_cards,hc) else 'noBDFD',r['bc'])],r,r['w'])
        md=made_detail(r['board'],r['combo'])
        if md: a.add(strong[(md,r['bc'])],r,r['w'])
        if r['cat']=='BDFD + BDSD':
            n=bdsd_count(r['board'],r['combo']); bucket='3+' if n>=3 else str(n)
            a.add(dbl[(bucket,r['bc'])],r,r['w'])
        if md is None and r['cat'] not in ('Two pair+','Overpair','High underpair','Weak pair','Top pair','Second pair','Third pair','Gutshot','OESD/8-out','Overcards + BDFD','BDFD + BDSD','BDFD only'):
            rs=rs_label(r['combo'])
            if rs in ('AK','AQ','AJ','AT','A9','A8','KQ','KJ','KT','QJ','QT','JT'):
                a.add(high[(rs,r['bc'])],r,r['w'])
    res={
      'weak_pair_by_middle_rank':{f'{bc}|mid={mid}':a.finish(v) for (bc,mid),v in weak.items()},
      'direct_draw_by_bdfd':{f'{cat}|{bd}|{bc}':a.finish(v) for (cat,bd,bc),v in draws.items()},
      'strong_made_detail':{f'{md}|{bc}':a.finish(v) for (md,bc),v in strong.items()},
      'double_backdoor_by_paths':{f'paths={n}|{bc}':a.finish(v) for (n,bc),v in dbl.items()},
      'bare_highcards':{f'{rs}|{bc}':a.finish(v) for (rs,bc),v in high.items()},
    }
    print('TARGETED_JSON_BEGIN'); print(json.dumps(res,ensure_ascii=False,separators=(',',':'))); print('TARGETED_JSON_END')

if __name__=='__main__': main()
