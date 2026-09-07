"""Run finite comparisons and checkpoint their results. Never solve new poker trees."""
from __future__ import annotations
import argparse, hashlib, itertools, json, os
from pathlib import Path
from core import *
import optimize as o

BASE=ROOT/'analysis/universal_strategy'

def fingerprint():
    h=hashlib.sha256()
    for name in ('core.py','optimize.py','experiments.py'):h.update((ROOT/'tools/universal_strategy'/name).read_bytes())
    return h.hexdigest()

def safe_cached(group,grid,mixed,data):
    name='--'.join(group);path=OUT/'maps'/f'{grid}__{name}__{int(mixed)}.json'
    if path.exists():
        old=json.loads(path.read_text())
        if old.get('code_sha256')==fingerprint():return old
    print('EVALUATE',grid,name,'mix',mixed,flush=True)
    z=o.evaluate_group([data[s] for s in group],grid,mixed)
    z.update(code_sha256=fingerprint(),run_id=os.environ.get('GITHUB_RUN_ID'),input_commit=os.environ.get('GITHUB_SHA'))
    dump(path,z)
    print('RESULT',grid,name,'LP',z['relaxation']['feasible'],'VALID',z.get('all_screening_gates_pass',False),z.get('complexity',{}),flush=True)
    return z

def minimum_partition(items,available):
    if not items:yield [];return
    first=items[0]
    for g in available:
        if first in g and set(g)<=set(items):
            for rest in minimum_partition([s for s in items if s not in g],available):yield [g]+rest

def record_progress(stage,text,next_step):
    import re
    p=BASE/'PROGRESS.md';s=p.read_text()
    heading='### '+stage+' — verified bounded comparison'
    block=heading+'\n\n'+text+'\n\n'
    if heading in s:s=re.sub(re.escape(heading)+r'.*?(?=\n### |\n## |\Z)',block.rstrip(),s,flags=re.S)
    else:s=s.replace('## Current best candidate',block+'## Current best candidate')
    s=re.sub(r'## Next step\n.*','## Next step\n'+next_step+'\n',s,flags=re.S)
    p.write_text(s)

def architecture(data):
    result={'experiment':'EXP-002','run_id':os.environ.get('GITHUB_RUN_ID'),'input_commit':os.environ.get('GITHUB_SHA'),'budgets':o.BUDGET,'groups':{},'architecture_tests':{}}
    families=[[s for s,d in data.items() if d['actions']==a] for a in ('XB','FCR')]
    for grid in ('six','eight','thirteen'):
        results=[]
        for family in families:
            for size in range(len(family),1,-1):
                for group in itertools.combinations(family,size):
                    z=safe_cached(group,grid,True,data);results.append(z)
                    if z['relaxation']['feasible']:results.append(safe_cached(group,grid,False,data))
        result['groups'][grid]=results
        def compatible(g):return any(set(z['studies'])==set(g) and z.get('all_screening_gates_pass') for z in results) if len(g)>1 else None
        two=families
        four=[[s for s,d in data.items() if d['actions']==a and d['pos']==p] for a in ('XB','FCR') for p in ('IP','OOP')]
        result['architecture_tests'][grid]={'2_maps':[{'studies':g,'joint_map_found':compatible(g)} for g in two],
                                            '4_maps':[{'studies':g,'joint_map_found':compatible(g)} for g in four]}
        dump(OUT/'EXP-002.json',result)
    a=data['UTG_BB_BET'];b=data['UTG_BTN_BET']
    assert np.array_equal(a['board'],b['board']) and np.array_equal(a['combo'],b['combo'])
    tv=float(abs(a['w']/a['w'].sum()-b['w']/b['w'].sum()).sum()/2)
    gap=float(a['w']@a['freq'][:,1]/a['w'].sum()-b['w']@b['freq'][:,1]/b['w'].sum())
    result['shared_bet_bound']={'input_total_variation':tv,'solver_bet_gap':gap,'at_least_one_error_pp':100*max(0,(gap-tv)/2)}
    dump(OUT/'EXP-002.json',result)
    md=['# EXP-002 — общие оси и общие действия: разные требования','',f"GHA run: {result['run_id']}. Code: {result['input_commit']}.",'',
        'Одинаковая сетка категорий допустима. Одна и та же ставка для одной и той же руки/доски против BB и BTN — отдельное, гораздо более жёсткое ограничение.','',
        f"UTG bet: {gap*100:.2f} п.п. разницы между двумя solver-спотами; TV входных распределений всего {tv*100:.2f}%. Для любой общей функции BET(board,combo) хотя бы в одном споте ошибка общей частоты >= {100*(gap-tv)/2:.2f} п.п.",'',
        'Доказательство: для общей вероятности действия f∈[0,1], |Eₚf−E_qf|≤TV(p,q); оставшуюся разницу между целями не могут поглотить две ошибки меньше половины разности. Это ограничение общих действий, не классификатора.','',
        '## Проверки архитектур','', '| Сетка | Два общих набора действий | Четыре: IP/OOP × BET/DEFENSE |','|---|---|---|']
    for grid,z in result['architecture_tests'].items():
        md.append('| '+grid+' | '+('REJECT' if any(x['joint_map_found'] is False for x in z['2_maps']) else 'требует одиночных карт')+' | '+('REJECT' if any(x['joint_map_found'] is False for x in z['4_maps']) else 'требует одиночных карт')+' |')
    md+=['','Отказ означает несовместимость с опубликованными аналитическими фильтрами, а не доказанную эксплойтность. Проверены также все объединения спотов внутри BET и DEFENSE; результаты — EXP-002.json и maps/.','',
         'Фильтры заданы в optimize.py. Средний regret <=0.04bb, класс >=1% reach <=0.10bb; частоты ±8 п.п. overall, ±10 п.п. класса, ±15 п.п. независимой четырёхклассовой диагностики; проверяются редкие дорогие действия и крупные группы рук. Это рабочие допуски анализа, не универсальные покерные законы.','',
         'Изначальный фильтр 0.075bb для класса был слишком жёстким для [7–4]x против B75 при утверждённом широком словаре. Его осознанно заменили на 0.10bb при неизменном overall 0.04bb; отдельный низкий класс обязательно раскрывается в отчёте.','',
         'Предварительный поиск без проверки состава диапазона был отвергнут: малая EV-потеря и совпадение BET не оправдывают удаления целых групп value/draw. В текущем optimize.py состав крупных групп ограничен отдельно.']
    (OUT/'EXP-002.md').write_text('\n'.join(md)+'\n')
    record_progress('EXP-002',f"Script: `tools/universal_strategy/experiments.py --stage architectures`. GHA {result['run_id']}, commit {result['input_commit']}. Reports: `experiments/EXP-002.json`, `.md`, `maps/`.\n\nAll 2/4 shared-action architectures were tested, plus alternative groupings. See report for actual statuses. One shared UTG BET policy has an unavoidable target-frequency error of at least {100*(gap-tv)/2:.2f}pp in one spot. Shared taxonomy remains possible. No selected final candidate yet.",
                    'Run EXP-003: fit individual maps, select the smallest feasible fixed grid and the simplest feasible cover of the seven studies. Review actual maps and tails before publishing.')

def candidates(data):
    src=json.loads((OUT/'EXP-002.json').read_text())
    result={'experiment':'EXP-003','run_id':os.environ.get('GITHUB_RUN_ID'),'input_commit':os.environ.get('GITHUB_SHA'),'budgets':o.BUDGET,'grids':{}}
    for grid in ('six','eight','thirteen'):
        groups=src['groups'][grid][:]
        for s in data:
            for mixed in (False,True):groups.append(safe_cached((s,),grid,mixed,data))
        best={}
        for z in groups:
            if not z.get('all_screening_gates_pass'):continue
            key=tuple(z['studies']);score=(z['complexity']['score'],z['complexity']['mix_cells'])
            if key not in best or score<(best[key]['complexity']['score'],best[key]['complexity']['mix_cells']):best[key]=z
        partitions=list(minimum_partition(list(data),best))
        if not partitions:
            result['grids'][grid]={'feasible':False,'reason':'No complete cover found under diagnostic budgets.'};continue
        chosen=min(partitions,key=lambda gs:(len(gs),sum(best[g]['complexity']['score'] for g in gs)))
        maps=[best[g] for g in chosen]
        result['grids'][grid]={'feasible':True,'map_count':len(maps),'class_count':len(maps[0]['classes']),'maps':maps,
                  'mix_cells':sum(m['complexity']['mix_cells'] for m in maps),'complexity_score':sum(m['complexity']['score'] for m in maps),
                  'search_note':'Best cover of the successfully constructed action maps. Feasibility certificates and MIP statuses are saved. Not a proof of globally optimal cognitive complexity.'}
        dump(OUT/'EXP-003.json',result)
    good=[(z['class_count'],z['map_count'],z['complexity_score'],g) for g,z in result['grids'].items() if z['feasible']]
    if not good:raise RuntimeError('No grid passed. Do not publish a strategy; inspect fixed vocabulary and error tails.')
    grid=min(good)[-1];result['selected_grid']=grid
    result['selection_policy']='Fewest flop classes among passing fixed candidates; then fewest action maps; then action-boundary + 3*mix score. Not tiny EV differences.'
    result['hand_definition_version']='v2: bare A-high overrides BDSD-only 2OC; direct draws and BDFD still take precedence.'
    dump(OUT/'EXP-003.json',result)
    chosen=result['grids'][grid]
    md=['# EXP-003 — ограниченный поиск человеческих таблиц','',f"GHA {result['run_id']}; commit {result['input_commit']}.",'',
       'Категории рук не добавлялись. Сравниваются ровно три заранее заданные сетки: 6, 8 и 13 классов. Сначала чистые действия, затем разрешены простые 50/50 и 75/25. После проверки допустимости объединяются области одинаковых действий.','',
       '| Сетка | Прошла фильтры | Наборов действий | MIX-ячеек | Стоимость границ/MIX |','|---|---|---:|---:|---:|']
    for g,z in result['grids'].items():md.append(f"| {g} | {z['feasible']} | {z.get('map_count','—')} | {z.get('mix_cells','—')} | {z.get('complexity_score','—')} |")
    md+=['',f"Предварительный выбор: **{grid}**, {chosen['class_count']} классов, {chosen['map_count']} карт действий на одних осях.",'',
       '| Study | Solver | Human | Regret, bb | Доп. потеря против mixed, bb | Масса действий >0.5bb |','|---|---|---|---:|---:|---:|']
    for z in chosen['maps']:
        for study,m in z['metrics'].items():
            fmt=lambda d:' / '.join(f'{a} {v*100:.1f}%' for a,v in d.items())
            md.append(f"| {study} | {fmt(m['solver'])} | {fmt(m['human'])} | {m['local_regret_bb']:.5f} | {m['extra_loss_vs_mixed_bb']:.5f} | {m['costly_action_mass_gt_05']*100:.2f}% |")
    md+=['','Все полные ячейки, частоты по классам, состав крупных групп, квантили ошибок и худшие флопы сохранены в EXP-003.json. Автоматический выбор ещё требует чтения самих правил; не считать доказанным near-GTO.','',
         '### Определения','Bare A-high без пары, прямого стрит-дро и BDFD остаётся A-high даже при наличии BDSD. Это единая precedence для всех семи спотов, не новая строка. Широкие карманные/дро-категории нельзя строго упорядочить по силе во всех раздачах; сохранён один утверждённый порядок отображения.']
    (OUT/'EXP-003.md').write_text('\n'.join(md)+'\n')
    record_progress('EXP-003',f"Script: `experiments.py --stage candidates`. GHA {result['run_id']}, code {result['input_commit']}. Reports: `experiments/EXP-003.json`, `.md`, `maps/`.\n\nCurrent bounded candidate: {grid}, {chosen['class_count']} flop classes, {chosen['map_count']} actual maps, {chosen['mix_cells']} mixed cells. All numeric screening gates pass. Manual semantic review and Markdown replacement remain pending; do not call the strategy finalized.",
                    'Read EXP-003 matrices and tail/composition metrics, simplify remaining conspicuous exceptions only within the same limits, then build and verify strategy_structured.md with original personal preflop/reference sections preserved.')
    p=BASE/'PROGRESS.md';s=p.read_text();import re
    s=re.sub(r'## Current best candidate\n.*?(?=## Rejected ideas)',f"## Current best candidate\nEXP-003 provisional: {grid}; {chosen['class_count']} flop classes, {chosen['map_count']} actual maps, {chosen['mix_cells']} mixed cells. See EXP-003.json for exact maps and per-study metrics. Not final and not BR-validated.\n\n",s,flags=re.S);p.write_text(s)
    print('SELECTED',grid,chosen['map_count'],'maps',chosen['mix_cells'],'mixed cells',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['architectures','candidates'],required=True);args=ap.parse_args()
    data={s:load(s) for s in FILES}
    (architecture if args.stage=='architectures' else candidates)(data)
