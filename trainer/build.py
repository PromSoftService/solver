"""Package an approved manual snapshot and existing exports; never solve or simplify."""
import argparse, base64, csv, gzip, hashlib, html, json, re, sys
from pathlib import Path
from functools import lru_cache

HERE = Path(__file__).resolve().parent
RANKS = '23456789TJQKA'
DECK = [r+s for r in RANKS for s in 'cdhs']
COMBOS = [(a,b) for a in range(52) for b in range(a+1,52)]
IDS = {''.join(sorted((DECK[a],DECK[b]))):i for i,(a,b) in enumerate(COMBOS)}
EN = ['Two pair+','Overpair','Top pair','Underpair','Second pair','Weak pair','Third pair','Low pocket pair','OESD','Gutshot','2 overcards + BDFD','Air']
RU = ['Две пары+','Оверпара','Топ-пара','Андерпара','Вторая пара','Weak pair','Третья пара','Low pocket','OESD без пары','Гатшот без пары','Две оверкарты + БДФД','Воздух']
NINE = ['ВС','Dry','BBx','Bxx','xxx','СС','НС','Ax','Aw']

def dumps(o): return json.dumps(o,ensure_ascii=False,separators=(',',':'))
def section(md, heading):
    start=md.index(heading); level=len(heading)-len(heading.lstrip('#'))
    rest=md[start:]; stop=re.search(r'\n#{1,'+str(level)+r'} ',rest)
    return rest[:stop.start()] if stop else rest

def table(md,heading,cols=None):
    block=section(md,heading); rows=[]; header=None
    for line in block.splitlines():
        if not line.startswith('|'): continue
        cells=[x.strip().replace('**','') for x in line.split('|')[1:-1]]
        if cells[0] in EN+RU:
            rows.append([re.split(r'·|<br>',x)[0].strip() for x in cells[1:]])
        elif header is None: header=cells[1:]
    assert len(rows)==12,(heading,len(rows))
    return {'columns':cols or header,'rows':rows,'heading':heading.lstrip('# ')}

def inline(s):
    s=html.escape(s)
    s=re.sub(r'&lt;br\s*/?&gt;','<br>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'`(.+?)`',r'<code>\1</code>',s)
    return s

def markdown(md):
    out=[]; in_table=False; list_depth=0
    def close_lists():
        nonlocal list_depth
        while list_depth:
            out.append('</li></ul>');list_depth-=1
    for line in md.splitlines()+['']:
        bullet=re.match(r'^( *)(?:- )(.+)$',line)
        if in_table and not line.startswith('|'):out.append('</tbody></table></div>');in_table=False
        if list_depth and not bullet:close_lists()
        if line.startswith('|'):
            cells=[inline(x.strip()) for x in line.split('|')[1:-1]]
            if all(re.fullmatch(r'[:\- ]+',c) for c in cells):continue
            if not in_table:
                out.append('<div class="scroll"><table><thead><tr>'+''.join('<th>'+c+'</th>' for c in cells)+'</tr></thead><tbody>');in_table=True
            else:out.append('<tr>'+''.join('<td>'+c+'</td>' for c in cells)+'</tr>')
        elif line.startswith('#'):
            level=max(3,min(6,len(line)-len(line.lstrip('#'))-1))
            out.append(f'<h{level}>'+inline(line.lstrip('# '))+f'</h{level}>')
        elif bullet:
            depth=min(len(bullet[1])//2+1,list_depth+1)
            while list_depth>depth:out.append('</li></ul>');list_depth-=1
            if depth>list_depth:out.append('<ul><li>');list_depth+=1
            else:out.append('</li><li>')
            out.append(inline(bullet[2]))
        elif line.strip():out.append('<p>'+inline(line)+'</p>')
    return '\n'.join(out)

def snapshot(md):
    heads={'cb_btn':'#### BTN vs BB: BB чек','cb_utg':'#### UTG vs BB: BB чек','df_btn':'#### BB против BTN: BB чек','df_utg':'#### BB против UTG: BB чек',
           'donk':'### 4.1. Донк BB —','vsdonk':'### 4.2. BTN и UTG против донка BB','vsxr':'### 4.3. BTN и UTG против чек-рейза BB',
           'oopcb':'#### 4.4.1.','stabdef':'#### 4.4.2.'}
    tables={k:table(md,h) for k,h in heads.items()}
    ex={}
    for key,h in [('weakcb','#### 1. Weak-пары на BBx'),('dry','#### 2. Пары BTN'),('third','#### 3. Третья пара на'),('drawlow','#### 4. OESD'),('ace','#### 5. Топ-пара'),('topcc','#### 6. Топ-пара'),('gutdry','#### 7. Гатшоты'),('high','#### 8. Пары'),('weakdf','#### Weak-пары BB на BBx'),('weakdry','#### Weak-пары BB на Dry'),('weakxxx','#### Weak-пары против UTG на xxx'),('weakwheel','#### Weak-пары против UTG на Aw'),('over','#### Оверпары BB:'),('overslow','#### Две оверкарты + БДФД против UTG'),('gutcc','#### Гатшоты без пары на СС'),('gutbb','#### Гатшоты без пары на BBx')]:
        block=section(md,h)
        parts=block.split('\n\n')
        lead=next(p.strip() for p in parts[1:] if p.strip())
        ex[key]={'title':block.splitlines()[0].lstrip('# '),'lead':markdown(lead),'html':markdown(block)}
    # All reviewed cases for a flop, independent of the dealt hand or position.
    # Titles retain the exact position and comparison scope from the manual.
    scopes={'weakcb':[2,7],'dry':[1],'third':[5,6],'drawlow':[6],
            'ace':[7,8],'topcc':[5],'gutdry':[1],'high':[0],
            'weakdf':[2,7],'weakdry':[1,3],'weakxxx':[4],
            'weakwheel':[5,6,8],'over':[1,3,4,6],'overslow':[6],
            'gutcc':[5],'gutbb':[2]}
    for i,(key,value) in enumerate(ex.items()):
        value['flops']=scopes[key]
        value['kind']='C-bet' if i<8 else 'Защита BB'
    return dict(tables=tables,explanations=ex,manualSHA=hashlib.sha256(md.encode()).hexdigest(),rows=RU,englishRows=EN,nine=NINE)

def build(repo,manual,out,refresh=False):
    sys.path.insert(0,str(repo/'viewer'));sys.path.insert(0,str(repo/'scripts'))
    from server import Repository,combo_cell,ACTION_SHAPES
    from flop_strategy import hand_category
    repository=Repository(repo); md=manual.read_text(encoding='utf-8-sig'); snap=snapshot(md)
    saved=HERE/'approved-snapshot.json'
    if saved.exists():
        prior=json.loads(saved.read_text(encoding='utf-8'))
        if prior!=snap and not refresh:
            raise ValueError('Manual differs from approved-snapshot.json. Review the changes and explicitly update the snapshot before rebuilding.')
    studies=[]; board_list=None; data={}; provenance=[]
    @lru_cache(maxsize=None)
    def meta(board,combo):
        base,draw,bd,_=hand_category(board,combo)
        made=EN.index(base) if base in EN[:8] else 10 if base=='2 overcards' and bd else 11
        dr=8 if draw=='OESD' else 9 if draw=='Gutshot' else -1
        return [made,dr,int(bd)]
    for sid in ('STU005','STU002','STU004'):
        entry=next(v for v in repository.studies.values() if v['study']['study_id']==sid)
        sidx=len(studies); boards=entry['boards'];board_list=board_list or boards
        assert boards==board_list
        actors=['UTG','BTN'] if sid=='STU004' else ['BB','BTN' if sid=='STU005' else 'UTG']
        weights=[[entry['preflop_weights'][actor].get(combo_cell(DECK[a]+DECK[b])['label'],0) for a,b in COMBOS] for actor in actors]
        branches=[]
        for branch in entry['study']['branches']:
            bid=branch['id']
            if sidx<2 and bid.startswith('06'):continue
            actions=ACTION_SHAPES[branch['action_shape']];path=entry['exports'][bid]
            branches.append(dict(id=bid,actor=actors.index(branch['acting_player']),actions=actions,history=branch['history'],bet=branch.get('expected_bet_amount',0)/10,raiseTo=branch.get('expected_raise_amount',0)/10))
            provenance.append(dict(path=str(path.relative_to(repo)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            count=0
            with path.open(encoding='utf-8-sig',newline='') as f:
                for row in csv.DictReader(f):
                    board=row['board'];combo=row['combo'];cid=IDS[''.join(sorted(re.findall(r'[2-9TJQKA][cdhs]',combo)))]; m=meta(board,combo)
                    if board not in data:data[board]={'meta':{},'studies':[{}, {}, {}]}
                    data[board]['meta'][cid]=m
                    p=[float(row[a+'_frequency']) for a in actions]
                    if abs(sum(p)-1)>0.0001:
                        assert sum(p)==0,(bid,board,combo,p)
                    data[board]['studies'][sidx].setdefault(bid[:2],[]).append([cid]+p)
                    count+=1
            print(sid,bid,count,flush=True)
        studies.append(dict(id=sid,actors=actors,weights=weights,branches=branches,pot=6.5 if sid=='STU004' else 5.5))
    blocks=[]
    for board in board_list:
        raw=dumps(data[board]).encode();blocks.append(base64.b64encode(gzip.compress(raw,compresslevel=9,mtime=0)).decode())
    payload={**snap,'studies':studies,'boards':board_list,'combos':COMBOS,'deck':DECK,'blocks':blocks,'provenance':provenance,'version':'2026-10-18.1'}
    # Bootstrap is inlined; no fetch, imports, external fonts, or runtime server.
    template=(HERE/'index.html').read_text(encoding='utf-8')
    result=template.replace('/*__CSS__*/',(HERE/'style.css').read_text(encoding='utf-8')).replace('/*__CORE__*/',(HERE/'core.js').read_text(encoding='utf-8')).replace('/*__APP__*/',(HERE/'app.js').read_text(encoding='utf-8')).replace('"__PAYLOAD__"',dumps(payload).replace('</','<\\/'))
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(result,encoding='utf-8')
    (out.parent/'trainer-manifest.json').write_text(json.dumps({'version':payload['version'],'manualSHA':snap['manualSHA'],'sources':provenance,'boards':len(blocks),'htmlBytes':len(result.encode()),'htmlSHA256':hashlib.sha256(result.encode()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
    (out.parent/'trainer-test-data.json').write_text(dumps(payload),encoding='utf-8')
    (HERE/'approved-snapshot.json').write_text(json.dumps(snap,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Built',out,len(result.encode()),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--manual',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--refresh-snapshot',action='store_true',help='Explicitly snapshot an already reviewed manual; never select new actions');a=p.parse_args();build(a.repo.resolve(),a.manual,a.output,a.refresh_snapshot)
