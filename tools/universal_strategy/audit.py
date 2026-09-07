"""EXP-001: dataset and taxonomy audit; run from the repository root."""
from __future__ import annotations
import ast, itertools, os
from collections import Counter
import numpy as np
from core import *

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    expected=set(itertools.combinations(range(2,15),3))
    out={'experiment':'EXP-001','run_id':os.environ.get('GITHUB_RUN_ID'),'input_commit':os.environ.get('GITHUB_SHA'),
         'loss_definition':'best pure action EV - forced action EV; not mixed EV - action EV',
         'weighting':'normalize reach_probability within each study; do not pool unnormalized weights across studies',
         'board_scope':'BRD001 only; 286 unpaired rainbow rank triples', 'hand_order':HANDS,
         'precedence':'made hands; 2OC+any direct/BDFD/BDSD draw; combo SD+BDFD; OESD; gutshot; BDFD; bare A-high; residual 2OC; Air',
         'definition_notes':[
          'Underpair = pocket pair between top and middle board rank; Weak pair = pocket pair below middle rank. Matches existing RNG001 feature extractor; differs from older RNG002 scripts that called all non-overpairs Underpair.',
          'OESD includes double gutshots (two completing ranks / nominal eight straight outs). No claim that outs are clean.',
          'Combo draw = direct straight draw + BDFD on rainbow, except hands already assigned 2OC+draw. No direct flush draw exists on these flops.',
          '2OC+draw includes BDSD as in the previous BB33 classifier. A-high overrides bare 2OC, not the draw rows.',
          'Display order is the approved pedagogical order, not an exact total ranking by hand strength/clean outs; wide pocket/draw categories overlap in strength.',
          '13-template candidate completes missing legacy flops with BBx (including connected BBx). con means lower two board ranks consecutive. This operational proposal does not claim exact equivalence to all old handpicked examples.'
         ],'datasets':{}}
    for study in FILES:
        d=load(study); boards=set(d['board']); ranks={tuple(sorted(board_features(b))) for b in boards}
        assert ranks==expected and len(boards)==286
        zero=d['w']==0; W=d['w'].sum()
        info={'file':d['file'],'sha256':d['sha256'],'rows':len(d['w']),'boards':len(boards),'zero_reach_rows':int(zero.sum()),
              'weight_sum':float(W),'solver_frequencies':dict(zip(d['actions'],(d['w']@d['freq']/W).tolist())),
              'solver_local_regret_bb':float(d['w']@((d['freq']*d['loss']).sum(axis=1))/W),
              'iteration_range':[int(d['iteration'].min()),int(d['iteration'].max())],
              'reported_exploitability_range':[float(d['exploit'].min()),float(d['exploit'].max())],
              'positive_reach_missing_EV_rows':int(((~zero)&np.all(d['ev']==0,axis=1)).sum()),
              'hand_weights':dict(zip(HANDS,(np.bincount(d['hand'],weights=d['w'],minlength=len(HANDS))/W).tolist())),
              'taxonomies':{}}
        for grid in ('six','eight','thirteen'):
            ag=aggregate(d,grid); cw=ag['w'].reshape(-1,len(HANDS)).sum(axis=1)
            info['taxonomies'][grid]={'counts':dict(sorted(Counter(board_class(b,grid) for b in boards).items())),
               'frequencies':{c:(ag['freq'].reshape(-1,len(HANDS),len(d['actions']))[i].sum(axis=0)/cw[i]).tolist() for i,c in enumerate(ag['classes'])}}
        out['datasets'][study]=info
        print(study,info['rows'],'boards',info['boards'],'FREQ',info['solver_frequencies'],'solver_regret',round(info['solver_local_regret_bb'],6),flush=True)
    tree=ast.parse((ROOT/'tools/report_utg_old13_reanalysis.py').read_text())
    stmt=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CLASSES' for t in n.targets))
    ns={}; exec(compile(ast.Module(body=[stmt],type_ignores=[]),'legacy_list','exec'),{'__builtins__':{}},ns)
    cc=Counter(b for _,bs in ns['CLASSES'] for b in bs)
    out['legacy_examples']={'unique_flops':len(cc),'duplicate_memberships':{b:n for b,n in cc.items() if n!=1},'is_complete':len(cc)==286}
    dump(OUT/'EXP-001.json',out)
    md=['# EXP-001 — проверка входов и словаря','',f"GHA run: {out['run_id'] or 'local preflight'}; input commit: {out['input_commit'] or 'local preflight'}.",'',
        'Все 7 датасетов проверены по SHA-256, manifest IDs, уникальности board/combo, покрытию 286 rank triples, конечности чисел, сумме частот и формулам EV/loss. Личные диапазоны Markdown не загружались.','',
        '| Study | Строк | Solver actions | Solver local regret, bb |','|---|---:|---|---:|']
    for s,x in out['datasets'].items(): md.append(f"| {s} | {x['rows']} | "+' / '.join(f'{a} {v*100:.2f}%' for a,v in x['solver_frequencies'].items())+f" | {x['solver_local_regret_bb']:.6f} |")
    md+=['','## Выводы','',f"Старые 13 названий покрывают {len(cc)} уникальных примеров, не 286 флопов. Их нельзя считать готовой полной сеткой.",'',
       '`loss_if_action = best_EV - action_EV`. Дополнительная потеря относительно экспортированной mixed-стратегии равна candidate local regret минус solver local regret. Это не BR/exploitability.','',
       'Все три фиксированных предложения (6 / 8 / 13 классов) покрывают ровно 286 флопов без пересечений. Ни одно пока не выбрано как итоговая стратегия.','',
       '## Явные определения и ограничения','']+[f'- {x}' for x in out['definition_notes']]+['','Decision: KEEP inputs; proceed to finite action-map comparison.']
    (OUT/'EXP-001.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print('EXP-001 COMPLETE',flush=True)
if __name__=='__main__':main()
