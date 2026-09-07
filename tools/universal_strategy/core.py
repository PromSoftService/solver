"""Fixed, auditable vocabulary for BRD001. No equity computation."""
from __future__ import annotations
import csv, hashlib, json
from collections import Counter
from functools import lru_cache
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis/universal_strategy/experiments'
RANK = {r:i for i,r in enumerate('23456789TJQKA', 2)}
STRAIGHTS = tuple(frozenset(range(i,i+5)) for i in range(2,11)) + (frozenset((14,2,3,4,5)),)
HANDS = ('Two pair+', 'Overpair', 'Top pair', 'Second pair', 'Third pair', 'Underpair', 'Weak pair',
         'Combo draw', 'OESD', 'Gutshot', 'BDFD', '2 overcards + draw', '2 overcards', 'A-high', 'Air / Nothing')
# Display order stays the approved order. Precedence is separate and explicit.
GROUPS = ('Two pair+',) + ('Pairs',)*6 + ('Draws',)*5 + ('High cards',)*2 + ('Air',)
B6 = ('A[K-J]x','A[T-2]x','BBx','K[9-2]x','[Q-8]x','[7-4]x')
B8 = ('AKx','A[Q-J]x','A[T-2]x','BBx','K[9-2]x','[Q-J]x','[T-8]x','[7-4]x')
B13 = ('ABB','A[K/Q]x','A[J-T][9-5]','A[J-T][4-2]','A[9-7]x','A[6-2]x','BBB','BBx','K/Qx dis','K/Qx con','[J-8]x dis','[J-8]x con','[7-4]x')
FILES = {
 'UTG_BB_BET': ('DS__RNG001__CFG001__NOD002__BRD001__RUN-20260906-214220.csv','utg','XB','IP','RNG001','CFG001','NOD002'),
 'BB_DEF33': ('DS__RNG001__CFG001__BRD001__RUN-20260906-161112.csv','bb','FCR','OOP','RNG001','CFG001','NOD001'),
 'BB_DEF75': ('DS__RNG001__CFG002__BRD001__RUN-20260906-184116.csv','bb','FCR','OOP','RNG001','CFG002','NOD001'),
 'UTG_BTN_BET': ('DS__RNG002__CFG003__NOD003__BRD001__RUN-20260907-115423.csv','utg','XB','OOP','RNG002','CFG003','NOD003'),
 'BTN_DEF33': ('DS__RNG002__CFG003__NOD004__BRD001__RUN-20260907-141943.csv','btn','FCR','IP','RNG002','CFG003','NOD004'),
 'BTN_STAB': ('DS__RNG002__CFG003__NOD005__BRD001__RUN-20260907-154228.csv','btn','XB','IP','RNG002','CFG003','NOD005'),
 'UTG_DEF33': ('DS__RNG002__CFG003__NOD006__BRD001__RUN-20260907-192002.csv','utg','FCR','OOP','RNG002','CFG003','NOD006'),
}
ACTION_NAMES = {'X':'check','B':'bet','F':'fold','C':'call','R':'raise'}
HASHES = dict(zip(FILES, (
 '3021940635f3152d7a8fa8273997d51ea5b952b977bfed4bbd05a2bad8640453',
 '4d9eeb71c05b7dedfb310a6fb64b2f62a5376a32fbd21b4274899e77b9038782',
 '2ee1c17e58cd32cd348c7dc355ea243923975ee02ce4aa8b21a5e3b88dbe70d7',
 '14a7a97b11be5c27ad00040c55da064307261b22f0d41c6e31db54f949e27ff0',
 'c4873e866f54dac6a94ba8a53c5035447b9e8014a07fe936eb331b222fc6a988',
 '4a16832fc291aed112bee9ca25be6c17eb9fbe120ef2818462dac4b5a11c0e83',
 '55228aafa1caf32eded4520cc0f1b054266172e93d3724aaa841416906875d7d')))

def num(s: str) -> float:
    v = float(s.replace(',', '.'))
    if not np.isfinite(v): raise ValueError(f'Non-finite number: {s!r}')
    return v

@lru_cache(None)
def board_features(board: str) -> tuple[int,int,int]:
    cards = board.split()
    if len(cards)!=3 or len({c[0] for c in cards})!=3 or len({c[1] for c in cards})!=3:
        raise ValueError(f'Not unpaired rainbow: {board}')
    return tuple(sorted((RANK[c[0]] for c in cards), reverse=True))

@lru_cache(None)
def board_class(board: str, grid: str='six') -> str:
    hi,mid,lo = board_features(board)
    if grid=='four':
        return 'AKx' if (hi,mid)==(14,13) else 'Kxx' if hi==13 else '[A/Q/J]xx' if hi in (14,12,11) else '[T-4]x'
    if grid=='eight':
        if hi==14: return 'AKx' if mid==13 else 'A[Q-J]x' if mid>=11 else 'A[T-2]x'
        if mid>=10: return 'BBx'
        if hi==13: return 'K[9-2]x'
        return '[Q-J]x' if hi>=11 else '[T-8]x' if hi>=8 else '[7-4]x'
    if grid=='thirteen':
        if hi==14:
            if lo>=10: return 'ABB'
            if mid>=12: return 'A[K/Q]x'
            if mid>=10: return 'A[J-T][9-5]' if lo>=5 else 'A[J-T][4-2]'
            return 'A[9-7]x' if mid>=7 else 'A[6-2]x'
        if lo>=10: return 'BBB'
        if mid>=10: return 'BBx'
        if hi<8: return '[7-4]x'
        # Operational definition, not a claim about all straight connectivity:
        # con = the two lower cards are consecutive. Both broadway ranks already excluded.
        return ('K/Qx ' if hi>=12 else '[J-8]x ') + ('con' if mid-lo==1 else 'dis')
    if grid!='six': raise ValueError(grid)
    if hi==14: return 'A[K-J]x' if mid>=11 else 'A[T-2]x'
    if mid>=10: return 'BBx'
    if hi==13: return 'K[9-2]x'
    return '[Q-8]x' if hi>=8 else '[7-4]x'

@lru_cache(None)
def hand_class(board: str, combo: str) -> int:
    cards = board.split(); holes = [combo[:2], combo[2:]]
    if len(combo)!=4 or len(set(cards+holes))!=5: raise ValueError((board,combo))
    br = board_features(board); hr = tuple(RANK[h[0]] for h in holes)
    cnt = Counter(br+hr); u = frozenset(cnt)
    if any(s<=u for s in STRAIGHTS) or max(cnt.values())>=3 or sum(v>=2 for v in cnt.values())>=2: return 0
    if hr[0]==hr[1]:
        return 1 if hr[0]>br[0] else 5 if hr[0]>br[1] else 6
    matched = set(br) & set(hr)
    if matched: return 2 + br.index(max(matched))
    missing = set()
    for s in STRAIGHTS:
        if len(s & u)==4: missing.update(s-u)
    sd = 2 if len(missing)>=2 else 1 if len(missing)==1 else 0
    bd = holes[0][1]==holes[1][1] and holes[0][1] in [b[1] for b in cards]
    bs = any(len(s & u)==3 and bool(s & (set(hr)-set(br))) for s in STRAIGHTS) if not sd else False
    # Retain the previously used BB rule: 2OC + any draw overrides generic draw rows.
    if min(hr)>br[0] and (sd or bd or bs): return 11
    if sd and bd: return 7
    if sd: return 8 if sd==2 else 9
    if bd: return 10
    # A-high has precedence over bare 2OC, without introducing a new row.
    if max(hr)==14: return 13
    if min(hr)>br[0]: return 12
    return 14

def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def load(study: str) -> dict:
    filename,hero,acts,pos,rng,cfg,node=FILES[study]
    path=ROOT/'datasets'/filename
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=HASHES[study]: raise ValueError(f'{study}: dataset hash changed; review inputs before running')
    with path.open(encoding='utf-8-sig',newline='') as f: raw=list(csv.DictReader(f))
    boards=np.array([x['board'] for x in raw]); combos=np.array([x['combo'] for x in raw])
    if len(set(zip(boards,combos)))!=len(raw): raise ValueError('Duplicate board/combo')
    freq=np.array([[num(x[ACTION_NAMES[a]+'_frequency']) for a in acts] for x in raw])
    ev=np.array([[num(x['ev_'+ACTION_NAMES[a]+'_'+hero]) for a in acts] for x in raw])
    loss=np.array([[num(x['loss_if_'+ACTION_NAMES[a]+'_'+hero]) for a in acts] for x in raw])
    w=np.array([num(x['reach_probability']) for x in raw])
    mixed=np.array([num(x['mixed_ev_'+hero]) for x in raw])
    hand=np.array([hand_class(b,c) for b,c in zip(boards,combos)])
    if (w<0).any() or w.sum()<=0: raise ValueError('Invalid reach')
    if np.max(np.abs(freq.sum(axis=1)-1))>2e-5 or (freq<0).any(): raise ValueError('Invalid frequencies')
    if np.max(np.abs(loss-(ev.max(axis=1)[:,None]-ev)))>2e-5: raise ValueError('Unexpected loss semantics')
    if np.max(np.abs(mixed-(freq*ev).sum(axis=1)))>2e-5: raise ValueError('Unexpected mixed EV')
    manifest=json.loads(path.with_suffix('.manifest.json').read_text(encoding='utf-8-sig'))
    if manifest['range_id']!=rng or manifest['config_id']!=cfg or manifest['board_set_id']!='BRD001': raise ValueError('Manifest IDs mismatch')
    if manifest.get('decision_id',node)!=node: raise ValueError('Decision mismatch')
    return dict(study=study,file=filename,sha256=digest,hero=hero,actions=acts,pos=pos,range_id=rng,config_id=cfg,node=node,
                board=boards,combo=combos,hand=hand,w=w,freq=freq,ev=ev,loss=loss,mixed=mixed,
                iteration=np.array([num(x['iteration']) for x in raw]),exploit=np.array([num(x['exploitability']) for x in raw]),manifest=manifest)

def aggregate(d: dict, grid='six') -> dict:
    classes={'six':B6,'eight':B8,'thirteen':B13}[grid]
    bi=np.array([classes.index(board_class(b,grid)) for b in d['board']]); ci=bi*len(HANDS)+d['hand']; n=len(classes)*len(HANDS)
    w=np.bincount(ci,weights=d['w'],minlength=n)
    def agg(x): return np.stack([np.bincount(ci,weights=d['w']*x[:,j],minlength=n) for j in range(x.shape[1])],axis=1)
    return dict(classes=classes,bi=bi,ci=ci,w=w,loss=agg(d['loss']),freq=agg(d['freq']),
                bad05=agg((d['loss']>.5).astype(float)),bad10=agg((d['loss']>1).astype(float)))
