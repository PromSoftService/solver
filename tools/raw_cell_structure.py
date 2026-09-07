#!/usr/bin/env python3
"""EXP-004: saved solver cells, no optimization or human policy selection.
Separate entry point avoids the old tools/universal_strategy/** CI trigger.
"""
from __future__ import annotations
import csv
import hashlib
import itertools
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / 'universal_strategy'))
import numpy as np
import core

BASE = core.ROOT / 'analysis/universal_strategy/experiments'
DEST = BASE / 'EXP-004'
EXPECTED_CORE = '18a139a74aeb0eebf7df6b92033986440af146e7'
TITLES = {
 'UTG_BB_BET':'UTG c-bet B33 vs BB: BB CHECK -> UTG X/B',
 'BB_DEF33':'BB defense vs UTG B33: BB CHECK -> UTG B33 -> BB F/C/R',
 'BB_DEF75':'BB defense vs UTG B75: BB CHECK -> UTG B75 -> BB F/C/R',
 'UTG_BTN_BET':'UTG c-bet B33 vs BTN: UTG X/B at flop root',
 'BTN_DEF33':'BTN defense vs UTG B33: UTG B33 -> BTN F/C/R',
 'BTN_STAB':'BTN stab B33: UTG CHECK -> BTN X/B',
 'UTG_DEF33':'UTG defense vs BTN B33: UTG CHECK -> BTN B33 -> UTG F/C/R',
}
DEFINITIONS = (
 'A + две карты K/Q/J/T', 'A + K/Q + карта 2..9',
 'A + J/T + карта 5..9', 'A + J/T + карта 2..4',
 'A, средняя карта 7..9', 'A, средняя карта <=6',
 'Без A: три карты K/Q/J/T',
 'Без A: две карты K/Q/J/T, младшая <=9; включая связанные',
 'K/Q-high, средняя <=9; две младшие НЕ соседние',
 'K/Q-high, средняя <=9; две младшие соседние',
 'J..8-high, средняя <=9; две младшие НЕ соседние',
 'J..8-high, средняя <=9; две младшие соседние',
 'Старшая карта 7..4',
)


def blob_sha(p: Path) -> str:
    data=p.read_bytes()
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def quantile(values, w, q):
    order=np.argsort(values,kind='stable')
    i=int(np.searchsorted(np.cumsum(w[order]),q*w.sum(),side='left'))
    return float(values[order[min(i,len(order)-1)]])


def profile(d, mask, W, class_w):
    positive=mask & (d['w']>0);w=d['w'][positive];mass=float(w.sum())
    out=dict(row_count=int(mask.sum()),positive_reach_rows=int(positive.sum()),
             positive_reach_boards=len(set(d['board'][positive])),reach_weight=mass,
             share_of_study=mass/W,share_of_class=mass/class_w if class_w else None)
    fields=('frequencies','action_ev_bb','mixed_ev_bb','mean_best_ev_bb',
            'forced_action_local_regret_bb','solver_local_regret_bb','extra_loss_vs_mixed_bb',
            'action_loss_p95_bb','action_loss_mass_gt_05','action_loss_mass_gt_10',
            'frequency_p10','frequency_p90')
    if not len(w):
        out.update(status='no_rows' if not mask.any() else 'zero_reach')
        out.update({k:None for k in fields});return out
    freq,ev,loss=d['freq'][positive],d['ev'][positive],d['loss'][positive]
    mean=lambda x:w@x/mass
    vec=lambda x:dict(zip(d['actions'],[float(v) for v in x]))
    baseline=float(mean((freq*loss).sum(axis=1)))
    out.update(status='observed',frequencies=vec(mean(freq)),action_ev_bb=vec(mean(ev)),
               mixed_ev_bb=float(mean(d['mixed'][positive])),mean_best_ev_bb=float(mean(ev.max(axis=1))),
               forced_action_local_regret_bb=vec(mean(loss)),solver_local_regret_bb=baseline,
               extra_loss_vs_mixed_bb=vec(mean(loss)-baseline),
               action_loss_p95_bb=vec([quantile(loss[:,i],w,.95) for i in range(len(d['actions']))]),
               action_loss_mass_gt_05=vec(mean((loss>.5).astype(float))),
               action_loss_mass_gt_10=vec(mean((loss>1).astype(float))),
               frequency_p10=vec([quantile(freq[:,i],w,.1) for i in range(len(d['actions']))]),
               frequency_p90=vec([quantile(freq[:,i],w,.9) for i in range(len(d['actions']))]))
    return out


def partition():
    if blob_sha(Path(core.__file__))!=EXPECTED_CORE:
        raise ValueError('core.py changed: review definitions before EXP-004')
    boards=[' '.join(r+s for r,s in zip(rs,'shd')) for rs in itertools.combinations('AKQJT98765432',3)]
    def predicates(b):
        hi,mid,lo=core.board_features(b)
        return (hi==14 and lo>=10,hi==14 and mid>=12 and lo<10,
                hi==14 and mid in (11,10) and 5<=lo<=9,hi==14 and mid in (11,10) and lo<=4,
                hi==14 and 7<=mid<=9,hi==14 and mid<=6,
                hi<14 and lo>=10,hi<14 and mid>=10 and lo<=9,
                hi in (13,12) and mid<=9 and mid-lo!=1,hi in (13,12) and mid<=9 and mid-lo==1,
                8<=hi<=11 and mid<=9 and mid-lo!=1,8<=hi<=11 and mid<=9 and mid-lo==1,hi<=7)
    for b in boards:
        flags=predicates(b)
        if sum(flags)!=1 or core.B13[flags.index(True)]!=core.board_class(b,'thirteen'):
            raise ValueError('Partition disagreement: '+b)
    result=[]
    for c,definition in zip(core.B13,DEFINITIONS):
        bs=[b for b in boards if core.board_class(b,'thirteen')==c]
        result.append(dict(name=c,definition=definition,board_count=len(bs),examples=bs[:3],boards=bs))
    if sum(x['board_count'] for x in result)!=286:raise ValueError('Incomplete partition')
    return result


def analyze(study):
    print('START',study,flush=True)
    d=core.load(study);W=float(d['w'].sum())
    bclasses=np.array([core.board_class(b,'thirteen') for b in d['board']])
    result=dict(study=study,title=TITLES[study],file=d['file'],sha256=d['sha256'],
                range_id=d['range_id'],config_id=d['config_id'],node=d['node'],
                actions=list(d['actions']),row_count=len(d['w']),board_count=len(set(d['board'])),classes={},cells={})
    result['overall']=profile(d,np.ones(len(d['w']),dtype=bool),W,W)
    for c in core.B13:
        bm=bclasses==c;cw=float(d['w'][bm].sum())
        result['classes'][c]=profile(d,bm,W,cw)
        result['cells'][c]={h:profile(d,bm & (d['hand']==i),W,cw) for i,h in enumerate(core.HANDS)}
        if not np.isclose(sum(v['reach_weight'] for v in result['cells'][c].values()),cw,rtol=1e-10,atol=1e-8):
            raise ValueError('Cell reach totals disagree')
        for a in d['actions']:
            weighted=sum(v['reach_weight']*v['frequencies'][a] for v in result['cells'][c].values() if v['frequencies'] is not None)
            if cw and not np.isclose(weighted/cw,result['classes'][c]['frequencies'][a],atol=1e-10):
                raise ValueError('Cell frequency totals disagree')
    if result['board_count']!=286:raise ValueError('Wrong dataset coverage')
    core.dump(DEST/(study+'.json'),result)
    print('DONE',study,'195 cells',result['overall']['frequencies'],flush=True)
    return result


def compare_columns(study,left,right):
    """Descriptive profile distance, NOT merge regret or policy test."""
    pairs=[];coverage=[0.,0.]
    for h in core.HANDS:
        p,q=study['cells'][left][h],study['cells'][right][h]
        if p['frequencies'] is None or q['frequencies'] is None:continue
        a,b=p['share_of_class'],q['share_of_class'];coverage[0]+=a;coverage[1]+=b
        diffs={act:100*abs(p['frequencies'][act]-q['frequencies'][act]) for act in study['actions']}
        lossdiff=max(abs(p['forced_action_local_regret_bb'][act]-q['forced_action_local_regret_bb'][act]) for act in study['actions'])
        pairs.append(dict(hand=h,weight=(a+b)/2,tv_pp=sum(diffs.values())/2,
                          max_action_difference_pp=max(diffs.values()),max_loss_difference_bb=lossdiff,
                          material=(a>=.02 and b>=.02),left_share=a,right_share=b))
    norm=sum(x['weight'] for x in pairs);material=[x for x in pairs if x['material']]
    return dict(left=left,right=right,common_hand_coverage=coverage,
                mean_hand_profile_tv_pp=sum(x['weight']*x['tv_pp'] for x in pairs)/norm if norm else None,
                worst_material_hand=max(material,key=lambda x:x['max_action_difference_pp']) if material else None,rows=pairs)


def table(st,field,action=None,percent=False):
    def row(label,vals):
        vals=vals[:6]+[':---:' if label=='---' else '│']+vals[6:]
        return '| '+label+' | '+' | '.join(vals)+' |'
    out=[row('Рука',list(core.B13)),row('---',[':---:']*len(core.B13))]
    for i,h in enumerate(core.HANDS):
        if i in (7,12):out.append(row('**────────**',['─']*len(core.B13)))
        values=[]
        for c in core.B13:
            cell=st['cells'][c][h]
            if cell['status']!='observed':
                values.append('—' if cell['status']=='no_rows' else '∅');continue
            v=cell[field]
            if action is not None:v=v[action]
            if field=='frequencies' and action is None:
                values.append('/'.join(f'{100*v[a]:.0f}' for a in st['actions']))
            else:values.append(f'{100*v:.1f}' if percent else f'{v:.4f}')
        out.append(row(h,values))
    return '\n'.join(out)


def render(result):
    head=['# EXP-004 — исходные профили solver: 7 спотов × 13 флопов × 15 рук','',
          '**Это исходные частоты, а не рекомендуемые человеческие действия. Ничего не объединено.**','',
          'GHA run: '+result['run_id']+'; code commit: '+result['input_commit']+'.','',
          'Вес = reach_probability, нормированный отдельно в каждом study. — = нет строк в dataset; '
          '∅ = строки есть, но суммарный reach равен нулю. Нулевая частота действия не означает отсутствующую руку. '
          'Проценты округлены только для отображения; JSON/CSV содержат полную точность.','',
          'Для BET-спотов показан BET%, CHECK=100−BET. Для защиты ячейка = **FOLD/CALL/RAISE %**. '
          'Вертикальная граница отделяет A-high флопы; горизонтальные — готовые руки, дро, high-card. '
          'Границы служат навигации, а не утверждению об одинаковых действиях.','',
          '## Определения флопов','',
          'B=K/Q/J/T. con/dis относится строго к соседству ДВУХ МЛАДШИХ рангов. '
          'Это сохранённая операционная сетка, не буквальная реконструкция всех старых примеров.','',
          '| Класс | Определение | Число флопов | Примеры |','|---|---|---:|---|']
    for c in result['flops']:
        head.append('| '+c['name']+' | '+c['definition']+' | '+str(c['board_count'])+' | '+', '.join(c['examples'])+' |')
    head+=['','## Определения рук и ограничения','',
           'Классификатор core.py не изменён. Underpair — карманка между старшей и средней картой; Weak pair — ниже средней. '
           'Сначала готовые руки. Bare A-high без прямого стрит-дро и BDFD остаётся A-high даже с BDSD. '
           'Иначе 2 overcards + draw (прямое стрит-дро, BDFD или BDSD) имеет приоритет над Combo draw. '
           'Combo draw = прямое стрит-дро + BDFD; OESD включает double gutshot. '
           'Затем остаточные BDFD, 2OC и Air. Строки непересекаются, но фиксированный порядок отображения '
           'НЕ является точным ранжированием чистых аутов/силы. 2OC+draw может содержать сильное дро, хотя строка ниже BDFD. '
           'Это ограничение сохранено явно, без молчаливого переопределения.','',
           'loss_if_action = среднее по reach(best pure EV − action EV). Это не best(mean EV) − mean(action EV). '
           'Дополнительная потеря против экспортированной mixed-стратегии сохранена отдельно. '
           'BR/strategy-lock не выполнялись. Equity не используется.','']
    compact=list(head);full=list(head);flat=[]
    for key,st in result['studies'].items():
        lines=['## '+TITLES[key],'','### Solver frequencies','',
               table(st,'frequencies','B' if st['actions']==['X','B'] else None,True),'',
               '### Reach класса и частоты всего диапазона','',
               '| Флоп | Доля reach study, % | '+('BET %' if st['actions']==['X','B'] else 'F/C/R %')+' |','|---|---:|---:|']
        for c,p in st['classes'].items():
            acts=['B'] if st['actions']==['X','B'] else st['actions']
            freq='/'.join(f'{100*p["frequencies"][a]:.1f}' for a in acts)
            lines.append(f'| {c} | {100*p["share_of_study"]:.3f} | {freq} |')
        lines.append('');compact+=lines;full+=lines
        full+=['### Вес руки внутри класса флопов, %','',table(st,'share_of_class',None,True),'']
        for a in st['actions']:
            full+=['### Forced '+core.ACTION_NAMES[a].upper()+': local regret, bb','',table(st,'forced_action_local_regret_bb',a),'']
        for c,hands in st['cells'].items():
            for h,p in hands.items():
                item=dict(study=key,flop=c,hand=h,status=p['status'],reach_weight=p['reach_weight'],
                          share_of_study=p['share_of_study'],share_of_class=p['share_of_class'],
                          positive_reach_rows=p['positive_reach_rows'],positive_reach_boards=p['positive_reach_boards'])
                for field in ('frequencies','action_ev_bb','forced_action_local_regret_bb','extra_loss_vs_mixed_bb',
                              'action_loss_p95_bb','action_loss_mass_gt_05','action_loss_mass_gt_10'):
                    for a in st['actions']:item[field+'_'+a]=p[field][a] if p[field] is not None else None
                item['mixed_ev_bb']=p['mixed_ev_bb'];flat.append(item)
    comparisons=['## Сходство соседних столбцов: только диагностика','',
                 'Сравниваются одинаковые строки. Средняя TV — half-L1 разница частот, взвешенная средним составом '
                 'двух столбцов на общих строках. Значимая строка для максимума: >=2% reach В КАЖДОМ из двух классов. '
                 'Это диагностический порог, не покерный закон. Покрытие общими строками показано отдельно. '
                 'Цена объединения НЕ рассчитана; никакие классы не слиты.','',
                 '| Спот | Левый класс | Правый класс | Средняя TV, п.п. | Макс. по значимой строке, п.п. | Рука | Покрытие L/R, % |',
                 '|---|---|---|---:|---:|---|---|']
    for key,diag in result['neighbor_diagnostics'].items():
        for p in diag:
            worst=p['worst_material_hand'];mean=p['mean_hand_profile_tv_pp']
            comparisons.append('| '+key+' | '+p['left']+' | '+p['right']+' | '+(f'{mean:.2f}' if mean is not None else '—')+
                               ' | '+(f'{worst["max_action_difference_pp"]:.2f}' if worst else '—')+
                               ' | '+(worst['hand'] if worst else '—')+' | '+
                               '/'.join(f'{100*x:.1f}' for x in p['common_hand_coverage'])+' |')
    full+=comparisons
    (BASE/'EXP-004.md').write_text('\n'.join(full)+'\n',encoding='utf-8')
    (BASE/'EXP-004-matrices.md').write_text('\n'.join(compact)+'\n',encoding='utf-8')
    with (BASE/'EXP-004-cells.csv').open('w',encoding='utf-8',newline='') as f:
        fields=list(dict.fromkeys(k for row in flat for k in row))
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(flat)


def main():
    old={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.glob('EXP-00[123].*')}
    result=dict(experiment='EXP-004',mode='raw_solver_profiles_no_human_policy',
                run_id=os.environ.get('GITHUB_RUN_ID','local'),input_commit=os.environ.get('GITHUB_SHA','local'),
                classifier_git_blob=EXPECTED_CORE,hand_order=list(core.HANDS),flops=partition(),studies={},neighbor_diagnostics={})
    for study in core.FILES:result['studies'][study]=analyze(study)
    for key,st in result['studies'].items():
        result['neighbor_diagnostics'][key]=[compare_columns(st,l,r) for l,r in zip(core.B13,core.B13[1:])]
    core.dump(BASE/'EXP-004.json',result);render(result)
    if any(hashlib.sha256(p.read_bytes()).hexdigest()!=sha for p,sha in old.items()):
        raise ValueError('An old experiment artifact was unexpectedly modified')
    if len(result['studies'])!=7:raise ValueError('Expected seven independent studies')
    print('EXP-004 COMPLETE: 7 studies; 13 classes; 15 rows; 1365 cells; no human actions selected.',flush=True)


if __name__=='__main__':main()
