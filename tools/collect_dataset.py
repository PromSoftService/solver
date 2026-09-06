#!/usr/bin/env python3
import argparse, csv, json, math
from pathlib import Path

def fnum(x):
    try: return float(x)
    except Exception: return math.nan

def main():
    ap=argparse.ArgumentParser(description='Collect tsgpu-batch combos.json outputs into one analysis CSV.')
    ap.add_argument('output_dir', help='tsgpu-batch output directory')
    ap.add_argument('--csv', dest='csv_path', default=None)
    ap.add_argument('--money-scale', type=float, default=10.0)
    args=ap.parse_args()
    root=Path(args.output_dir)
    out=Path(args.csv_path) if args.csv_path else root/'dataset.csv'
    rows=[]
    for run_path in sorted(root.glob('*/run.json')):
        run=json.loads(run_path.read_text(encoding='utf-8-sig'))
        combo_path=run_path.parent/'combos.json'
        if not combo_path.exists():
            continue
        combos=json.loads(combo_path.read_text(encoding='utf-8-sig'))
        board=run.get('board','')
        for x in combos:
            freqs={'F':fnum(x.get('fold_frequency',0)), 'C':fnum(x.get('call_frequency',0)), 'R':fnum(x.get('raise_frequency',0))}
            evu={'F':fnum(x.get('ev_fold')), 'C':fnum(x.get('ev_call')), 'R':fnum(x.get('ev_raise'))}
            evbb={k:(v/args.money_scale if not math.isnan(v) else math.nan) for k,v in evu.items()}
            best=max(evbb, key=lambda k: -math.inf if math.isnan(evbb[k]) else evbb[k])
            freq_action=max(freqs, key=freqs.get)
            best_ev=evbb[best]
            rows.append({
              'board':board,'combo':x.get('combo',''),'reach_probability':x.get('reach_probability',0),
              'fold_frequency':freqs['F'],'call_frequency':freqs['C'],'raise_frequency':freqs['R'],
              'ev_fold_units':evu['F'],'ev_call_units':evu['C'],'ev_raise_units':evu['R'],'mixed_ev_units':fnum(x.get('mixed_ev')),
              'ev_fold_bb':evbb['F'],'ev_call_bb':evbb['C'],'ev_raise_bb':evbb['R'],'mixed_ev_bb':fnum(x.get('mixed_ev'))/args.money_scale,
              'best_ev_action':best,'best_ev_bb':best_ev,'highest_frequency_action':freq_action,'highest_frequency':freqs[freq_action],
              'loss_if_fold_bb':best_ev-evbb['F'],'loss_if_call_bb':best_ev-evbb['C'],'loss_if_raise_bb':best_ev-evbb['R'],
              'iteration':run.get('final_status',{}).get('iteration'),'exploitability':run.get('final_status',{}).get('exploitability'),
            })
    if not rows:
        raise SystemExit('No */run.json + combos.json pairs found')
    fields=list(rows[0].keys())
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f'Wrote {len(rows)} rows -> {out}')

if __name__=='__main__': main()
