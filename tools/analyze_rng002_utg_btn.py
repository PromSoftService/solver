#!/usr/bin/env python3
import csv
import glob
import itertools
import json
from collections import defaultdict

RANK = {r: i for i, r in enumerate('23456789TJQKA', start=2)}
STRAIGHTS = [
    {14,13,12,11,10}, {13,12,11,10,9}, {12,11,10,9,8},
    {11,10,9,8,7}, {10,9,8,7,6}, {9,8,7,6,5},
    {8,7,6,5,4}, {7,6,5,4,3}, {6,5,4,3,2}, {14,5,4,3,2},
]
DATA_GLOB = 'datasets/DS__RNG002__CFG003__NOD003__BRD001__RUN-*.csv'
BUCKETS = (
    'Two pair+', 'Overpair', 'Top pair', 'Second pair', 'Underpair',
    'Third pair', 'OESD', 'Gutshot', 'BDFD', 'X-high', 'Air'
)
ACTIVE_USER = {'Two pair+','Overpair','Top pair','Second pair','OESD','Gutshot','BDFD','X-high'}


def fnum(x):
    if x is None or x == '':
        return 0.0
    return float(str(x).replace(',', '.'))


def cards_board(board):
    return board.split()


def cards_hole(combo):
    return [combo[:2], combo[2:4]]


def ranks(cards):
    return [RANK[c[0]] for c in cards]


def suits(cards):
    return [c[1] for c in cards]


def has_straight(rs):
    u = set(rs)
    return any(w <= u for w in STRAIGHTS)


def straight_draw_kind(br, hr):
    u = set(br + hr)
    missing = set()
    for w in STRAIGHTS:
        if len(w & u) == 4:
            missing |= (w - u)
    if len(missing) >= 2:
        return 'OESD'
    if len(missing) == 1:
        return 'Gutshot'
    return None


def has_bdfd(board_cards, hole_cards):
    hs = suits(hole_cards)
    return hs[0] == hs[1] and hs[0] in suits(board_cards)


def board4(board):
    hi, mid, lo = sorted(ranks(cards_board(board)), reverse=True)
    if hi == 14 and mid == 13:
        return 'AKx'
    if hi == 13:
        return 'Kxx'
    if hi in (14, 12, 11):
        return '[A/Q/J]xx'
    return '[T-4]x'


def board6(board):
    hi, mid, lo = sorted(ranks(cards_board(board)), reverse=True)
    if hi == 14:
        return 'A[K-J]x' if mid >= 11 else 'A[T-2]x'
    if sum(r >= 10 for r in (hi, mid, lo)) >= 2:
        return 'BBx'
    if hi == 13:
        return 'K[9-2]x'
    if 8 <= hi <= 12:
        return '[Q-8]x'
    return '[7-4]x'


def hand_bucket(board, combo):
    bc = cards_board(board)
    hc = cards_hole(combo)
    br = ranks(bc)
    hr = ranks(hc)
    top, mid, low = sorted(br, reverse=True)
    counts = defaultdict(int)
    for r in br + hr:
        counts[r] += 1

    if has_straight(br + hr):
        return 'Two pair+'
    if max(counts.values()) >= 3:
        return 'Two pair+'
    if sum(v >= 2 for v in counts.values()) >= 2:
        return 'Two pair+'

    if hr[0] == hr[1]:
        if hr[0] > top:
            return 'Overpair'
        return 'Underpair'

    matched = [r for r in hr if r in br]
    if matched:
        m = max(matched)
        if m == top:
            return 'Top pair'
        if m == mid:
            return 'Second pair'
        return 'Third pair'

    sd = straight_draw_kind(br, hr)
    if sd == 'OESD':
        return 'OESD'
    if sd == 'Gutshot':
        return 'Gutshot'
    if has_bdfd(bc, hc):
        return 'BDFD'
    if max(hr) > top:
        return 'X-high'
    return 'Air'


def load_rows():
    files = sorted(glob.glob(DATA_GLOB))
    if not files:
        raise SystemExit('RNG002 CFG003 NOD003 BRD001 dataset not found')
    path = files[-1]
    rows = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        for x in csv.DictReader(f):
            row = {
                'board': x['board'],
                'combo': x['combo'],
                'w': fnum(x['reach_probability']),
                'bet': fnum(x['bet_frequency']),
                'check': fnum(x['check_frequency']),
                'ev_bet': fnum(x['ev_bet_utg']),
                'ev_check': fnum(x['ev_check_utg']),
                'mixed_ev': fnum(x['mixed_ev_utg']),
                'lb': fnum(x['loss_if_bet_utg']),
                'lc': fnum(x['loss_if_check_utg']),
            }
            row['b4'] = board4(row['board'])
            row['b6'] = board6(row['board'])
            row['hb'] = hand_bucket(row['board'], row['combo'])
            rows.append(row)
    return path, rows


def summarize(rows, class_key, candidate=None):
    d = defaultdict(lambda: {'w':0.0,'sb':0.0,'cb':0.0,'reg':0.0,'eqgap':0.0,'rows':0})
    for r in rows:
        k = r[class_key] if class_key else 'OVERALL'
        z = d[k]
        w = r['w']
        p = candidate(r) if candidate else 0.0
        cev = p*r['ev_bet'] + (1-p)*r['ev_check']
        reg = p*r['lb'] + (1-p)*r['lc']
        z['w'] += w
        z['sb'] += w*r['bet']
        z['cb'] += w*p
        z['reg'] += w*reg
        z['eqgap'] += w*(r['mixed_ev'] - cev)
        z['rows'] += 1
    out = {}
    for k,z in d.items():
        w = z['w'] or 1.0
        out[k] = {
            'weight': z['w'], 'rows': z['rows'],
            'solver_bet': z['sb']/w,
            'candidate_bet': z['cb']/w if candidate else None,
            'frequency_diff': (z['cb']-z['sb'])/w if candidate else None,
            'local_regret_bb': z['reg']/w if candidate else None,
            'mixed_ev_gap_bb': z['eqgap']/w if candidate else None,
        }
    return out


def board_average(rows, class_key, candidate=None):
    per_board = defaultdict(lambda: {'w':0.0,'sb':0.0,'cb':0.0})
    board_class = {}
    for r in rows:
        z = per_board[r['board']]
        w = r['w']
        p = candidate(r) if candidate else 0.0
        z['w'] += w
        z['sb'] += w*r['bet']
        z['cb'] += w*p
        board_class[r['board']] = r[class_key]
    d = defaultdict(lambda: {'n':0,'sb':0.0,'cb':0.0})
    for b,z in per_board.items():
        if z['w'] <= 0:
            continue
        q = d[board_class[b]]
        q['n'] += 1
        q['sb'] += z['sb']/z['w']
        q['cb'] += z['cb']/z['w']
    return {k:{'boards':v['n'],'solver_bet':v['sb']/v['n'],
               'candidate_bet':v['cb']/v['n'] if candidate else None}
            for k,v in d.items()}


def user_candidate(r):
    if r['hb'] not in ACTIVE_USER:
        return 0.0
    if r['b4'] in ('AKx','Kxx'):
        return 0.80
    if r['b4'] == '[A/Q/J]xx':
        return 0.40
    return 0.0


def aggregate_cells(rows, class_key):
    cells = defaultdict(lambda: {'w':0.0,'sb':0.0,'lc':0.0,'lb':0.0})
    for r in rows:
        z = cells[(r[class_key], r['hb'])]
        w = r['w']
        z['w'] += w
        z['sb'] += w*r['bet']
        z['lc'] += w*r['lc']
        z['lb'] += w*r['lb']
    return cells


def class_order(class_key):
    if class_key == 'b4':
        return ('Kxx','AKx','[A/Q/J]xx','[T-4]x')
    return ('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')


def cell_table(rows, class_key):
    cells = aggregate_cells(rows, class_key)
    out = {}
    for c in class_order(class_key):
        out[c] = {}
        for hb in BUCKETS:
            z = cells.get((c,hb))
            if not z or z['w'] <= 0:
                continue
            w=z['w']
            out[c][hb] = {
                'share_weight': w,
                'solver_bet': z['sb']/w,
                'loss_check': z['lc']/w,
                'loss_bet': z['lb']/w,
            }
    return out


def package_metrics(cells, classes, active, rates):
    by = {}
    total = {'w':0.0,'sb':0.0,'cb':0.0,'reg':0.0}
    for c in classes:
        zc={'w':0.0,'sb':0.0,'cb':0.0,'reg':0.0}
        rate=rates[c]
        for hb in BUCKETS:
            z=cells.get((c,hb))
            if not z: continue
            p=rate if hb in active else 0.0
            zc['w'] += z['w']; zc['sb'] += z['sb']; zc['cb'] += z['w']*p
            zc['reg'] += (1-p)*z['lc'] + p*z['lb']
        w=zc['w'] or 1.0
        by[c]={'solver_bet':zc['sb']/w,'candidate_bet':zc['cb']/w,
               'frequency_diff':(zc['cb']-zc['sb'])/w,'local_regret_bb':zc['reg']/w,
               'weight':zc['w']}
        for k in total: total[k]+=zc[k]
    w=total['w'] or 1.0
    overall={'solver_bet':total['sb']/w,'candidate_bet':total['cb']/w,
             'frequency_diff':(total['cb']-total['sb'])/w,'local_regret_bb':total['reg']/w,
             'weight':total['w']}
    return by,overall


def search_same_shape(rows, class_key, grid, max_class_diff=0.05, max_overall_diff=0.03):
    cells=aggregate_cells(rows,class_key)
    classes=class_order(class_key)
    mandatory={'Two pair+','Overpair','Top pair'}
    forbidden={'Underpair','Third pair','Air'}
    optional=['Second pair','OESD','Gutshot','BDFD','X-high']
    best=None
    feasible=0
    for mask in range(1<<len(optional)):
        active=set(mandatory)
        for i,hb in enumerate(optional):
            if mask & (1<<i): active.add(hb)
        if active & forbidden: continue
        for rv in itertools.product(grid, repeat=len(classes)):
            rates=dict(zip(classes,rv))
            by,ov=package_metrics(cells,classes,active,rates)
            if abs(ov['frequency_diff']) > max_overall_diff: continue
            if any(abs(by[c]['frequency_diff']) > max_class_diff for c in classes): continue
            feasible += 1
            key=(ov['local_regret_bb'], sum(abs(by[c]['frequency_diff']) for c in classes), len(active), sum(rv))
            if best is None or key < best[0]:
                best=(key,active,rates,by,ov)
    if best is None:
        return {'feasible':0}
    _,active,rates,by,ov=best
    return {'feasible':feasible,'active':sorted(active),'rates':rates,'by_class':by,'overall':ov}


def eval_named_candidate(rows, name, fn, class_key='b4'):
    return {
        'name':name,
        'reach_weighted':summarize(rows,class_key,fn),
        'board_average':board_average(rows,class_key,fn),
        'overall':summarize(rows,None,fn)['OVERALL'],
    }


def round_report(x):
    if isinstance(x, dict): return {k:round_report(v) for k,v in x.items()}
    if isinstance(x, list): return [round_report(v) for v in x]
    if isinstance(x, float): return round(x,6)
    return x


def main():
    path,rows=load_rows()
    user=eval_named_candidate(rows,'USER_OLD',user_candidate,'b4')
    result={
        'dataset':path,
        'rows':len(rows),
        'definitions':{
            'X-high':'high-card hand with at least one overcard to the flop; direct draw/BDFD take precedence',
            'Air':'high-card hand with no OESD, gutshot, BDFD, or overcard',
            'Underpair':'all pocket pairs below the top flop card',
            'user_strategy_interpretation':'Strong/2nd/direct draw/BDFD/X-high use 80% on AKx/Kxx, 40% on [A/Q/J]xx, 0% on [T-4]x; Underpair/Third/Air always check.'
        },
        'solver_user4_reach':summarize(rows,'b4'),
        'solver_user4_board_average':board_average(rows,'b4'),
        'solver_alt6_reach':summarize(rows,'b6'),
        'solver_alt6_board_average':board_average(rows,'b6'),
        'user_candidate':user,
        'cells_user4':cell_table(rows,'b4'),
        'search_user4_50':search_same_shape(rows,'b4',(0.0,0.5,1.0),0.05,0.03),
        'search_user4_25':search_same_shape(rows,'b4',(0.0,0.25,0.5,0.75,1.0),0.05,0.03),
        'search_alt6_50':search_same_shape(rows,'b6',(0.0,0.5,1.0),0.05,0.03),
    }
    result=round_report(result)
    print('RNG002_UTG_BTN_REPORT_BEGIN')
    print(json.dumps(result,ensure_ascii=False,separators=(',',':')))
    print('RNG002_UTG_BTN_REPORT_END')


if __name__ == '__main__':
    main()
