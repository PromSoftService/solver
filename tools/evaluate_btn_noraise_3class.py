#!/usr/bin/env python3
import json
from collections import defaultdict
import analyze_rng002_btn_followups as a
import analyze_rng002_btn_refine as r


def c3(x):
    if x['b4'] == 'AKx':
        return 'AKx'
    if x['b4'] == '[T-4]x':
        return '[T-4]x'
    return '[K/A/Q/J]xx'


def detail_cells(rows):
    d = defaultdict(lambda: defaultdict(float))
    for x in rows:
        z = d[(c3(x), r.detail_bucket(x))]
        w = x['w']
        z['w'] += w
        for q in 'FCR':
            z[q] += w * x[q]
            z['l' + q] += w * x['l' + q]
    out = {}
    for (cls, hand), z in d.items():
        w = z['w']
        out.setdefault(cls, {})[hand] = {
            'w': w,
            'solverF': z['F'] / w,
            'solverC': z['C'] / w,
            'solverR': z['R'] / w,
            'lossF': z['lF'] / w,
            'lossC': z['lC'] / w,
            'lossR': z['lR'] / w,
        }
    return out


def solver_by3(rows):
    d = defaultdict(lambda: defaultdict(float))
    for x in rows:
        z = d[c3(x)]
        z['w'] += x['w']
        for q in 'FCR':
            z[q] += x['w'] * x[q]
    return {
        cls: {
            'w': z['w'],
            'F': z['F'] / z['w'],
            'C': z['C'] / z['w'],
            'R': z['R'] / z['w'],
        }
        for cls, z in d.items()
    }


def rule(x, middle_bdfd1=.5, ak_under9=.75):
    cls = c3(x)
    d = r.detail_bucket(x)
    if cls == '[T-4]x':
        pf = 0.0
    elif cls == '[K/A/Q/J]xx':
        if d in ('Air', 'X-high 1OC', 'BDFD 0OC'):
            pf = 1.0
        elif d == 'BDFD 1OC':
            pf = middle_bdfd1
        else:
            pf = 0.0
    else:  # AKx
        if d in ('Air', 'X-high 1OC', 'BDFD 0OC'):
            pf = 1.0
        elif d == 'Underpair 9-':
            pf = ak_under9
        else:
            pf = 0.0
    return {'F': pf, 'C': 1.0 - pf, 'R': 0.0}


def evaluate(rows, middle_bdfd1=.5, ak_under9=.75):
    by = defaultdict(lambda: defaultdict(float))
    for x in rows:
        cls = c3(x)
        p = rule(x, middle_bdfd1, ak_under9)
        z = by[cls]
        w = x['w']
        z['w'] += w
        for q in 'FCR':
            z['s' + q] += w * x[q]
            z['c' + q] += w * p[q]
        z['reg'] += w * sum(p[q] * x['l' + q] for q in 'FCR')
    out = {}
    tot = defaultdict(float)
    for cls, z in by.items():
        w = z['w']
        out[cls] = {'w': w, 'reg': z['reg'] / w}
        for q in 'FCR':
            out[cls]['solver' + q] = z['s' + q] / w
            out[cls]['cand' + q] = z['c' + q] / w
            out[cls]['diff' + q] = (z['c' + q] - z['s' + q]) / w
        tot['w'] += w
        tot['reg'] += z['reg']
        for q in 'FCR':
            tot['s' + q] += z['s' + q]
            tot['c' + q] += z['c' + q]
    W = tot['w']
    overall = {'reg': tot['reg'] / W}
    for q in 'FCR':
        overall['solver' + q] = tot['s' + q] / W
        overall['cand' + q] = tot['c' + q] / W
        overall['diff' + q] = (tot['c' + q] - tot['s' + q]) / W
    return {'by': out, 'overall': overall}


def main():
    p = a.latest('datasets/DS__RNG002__CFG003__NOD004__BRD001__RUN-*.csv')
    rows = a.load4(p, 'NOD004')
    candidates = {}
    for m in (0, .25, .5, .75, 1):
        for u in (0, .25, .5, .75, 1):
            key = f'm{int(m*100)}_u{int(u*100)}'
            candidates[key] = evaluate(rows, m, u)
    ranked = sorted(candidates.items(), key=lambda kv: (
        kv[1]['overall']['reg'],
        abs(kv[1]['by']['AKx']['diffF']) + abs(kv[1]['by']['[K/A/Q/J]xx']['diffF']),
    ))
    result = {
        'dataset': p,
        'solver_by3': solver_by3(rows),
        'detail_cells': detail_cells(rows),
        'top_candidates': [{
            'name': name,
            'middle_bdfd1_fold': int(name.split('_')[0][1:]) / 100,
            'ak_under9_fold': int(name.split('_')[1][1:]) / 100,
            'metrics': metrics,
        } for name, metrics in ranked[:10]],
        'simple_candidates': {
            'no_extra_mixes': evaluate(rows, 0, 0),
            'middle50_ak75': evaluate(rows, .5, .75),
            'middle50_ak50': evaluate(rows, .5, .5),
            'middle0_ak75': evaluate(rows, 0, .75),
            'middle100_ak100': evaluate(rows, 1, 1),
        },
    }
    print('BTN_NORAISE_3CLASS_BEGIN')
    print(json.dumps(a.rnd(result), ensure_ascii=False, separators=(',', ':')))
    print('BTN_NORAISE_3CLASS_END')


if __name__ == '__main__':
    main()
