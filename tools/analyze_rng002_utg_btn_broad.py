#!/usr/bin/env python3
import itertools
import json
from analyze_rng002_utg_btn import (
    BUCKETS, aggregate_cells, class_order, load_rows, package_metrics, round_report
)


def search(rows, class_key, grid, max_class_diff=0.05, max_overall_diff=0.03):
    cells = aggregate_cells(rows, class_key)
    classes = class_order(class_key)
    mandatory = {'Two pair+', 'Overpair', 'Top pair'}
    optional = ['Second pair','Underpair','Third pair','OESD','Gutshot','BDFD','X-high']
    best = None
    feasible = 0
    for mask in range(1 << len(optional)):
        active = set(mandatory)
        for i,hb in enumerate(optional):
            if mask & (1 << i):
                active.add(hb)
        for rv in itertools.product(grid, repeat=len(classes)):
            rates = dict(zip(classes, rv))
            by,ov = package_metrics(cells, classes, active, rates)
            if abs(ov['frequency_diff']) > max_overall_diff:
                continue
            if any(abs(by[c]['frequency_diff']) > max_class_diff for c in classes):
                continue
            feasible += 1
            key = (ov['local_regret_bb'], sum(abs(by[c]['frequency_diff']) for c in classes), len(active), sum(rv))
            if best is None or key < best[0]:
                best = (key, active, rates, by, ov)
    if best is None:
        return {'feasible':0}
    _,active,rates,by,ov = best
    return {'feasible':feasible,'active':sorted(active),'rates':rates,'by_class':by,'overall':ov}


def main():
    path,rows = load_rows()
    out = {
        'dataset':path,
        'user4_50_broad':search(rows,'b4',(0.0,0.5,1.0),0.05,0.03),
        'user4_25_broad':search(rows,'b4',(0.0,0.25,0.5,0.75,1.0),0.05,0.03),
        'alt6_50_broad':search(rows,'b6',(0.0,0.5,1.0),0.05,0.03),
        'alt6_50_relaxed':search(rows,'b6',(0.0,0.5,1.0),0.07,0.03),
    }
    print('RNG002_BROAD_REPORT_BEGIN')
    print(json.dumps(round_report(out),ensure_ascii=False,separators=(',',':')))
    print('RNG002_BROAD_REPORT_END')


if __name__ == '__main__':
    main()
