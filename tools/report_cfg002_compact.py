#!/usr/bin/env python3
from analyze_cfg002_compare import load, board_stats, analyze_cfg002, EPS


def pct(x): return f'{100*x:.1f}%'
def fmt(z):
    return (f"F {pct(z['fold'])} C {pct(z['call'])} R {pct(z['raise'])} | "
            f"loss F/C/R {z['loss_F']:.4f}/{z['loss_C']:.4f}/{z['loss_R']:.4f} | "
            f"best {z['best_pure']} {z['best_loss']:.4f} cover {pct(z['best_cover'])}")

def section(name, data, keys=None):
    print(f'## {name}')
    items=data.items()
    if keys is not None:
        items=[(k,data[k]) for k in keys if k in data]
    for k,z in items:
        print(f'{k}: {fmt(z)}')


def main():
    p1,r1=load('CFG001'); p2,r2=load('CFG002')
    a=analyze_cfg002(r2)
    print('CFG002_COMPACT_BEGIN')
    print(f'dataset={p2} rows={len(r2)} eps={EPS}')
    print('## board_stats')
    s1=board_stats(r1); s2=board_stats(r2)
    for k in ('ABx','Axx','BBx','Kxx','[Q-8]x','[7-4]x'):
        x=s1[k]; y=s2[k]
        print(f"{k}: CFG001 SDF {pct(x['sdf'])} C {pct(x['call'])} R {pct(x['raise'])} || CFG002 SDF {pct(y['sdf'])} C {pct(y['call'])} R {pct(y['raise'])}")

    section('core made categories', a['core'], [
      'Straight','Set/Trips','Two pair','Overpair','High underpair','Top pair','Second pair','Third pair','Weak pocket pair','High card'])

    print('## coarse_needing_split')
    for k,z in a['coarse_categories_needing_split'].items(): print(f'{k}: {fmt(z)}')

    # Board-specific made categories.
    mb=a['made_by_board']
    wanted=[]
    for b in ('ABx','Axx','BBx','Kxx','[Q-8]x','[7-4]x'):
        for m in ('Set/Trips','Two pair','Straight','Overpair','High underpair','Top pair','Second pair','Third pair','Weak pocket pair'):
            wanted.append(str((b,m)))
    section('made_by_board', mb, wanted)

    section('weak_pair_by_middle', a['weak_pair_by_middle'])
    section('direct_draw_detail', a['direct_draw_detail'])
    section('backdoor_detail', a['backdoor_detail'])

    print('## selected highcard detail')
    for k,z in a['highcard_detail'].items():
        if any(h in k for h in ("'AK'","'AQ'","'AJ'","'KQ'","'KJ'","'AT'")):
            print(f'{k}: {fmt(z)}')

    print('## selected pair+kicker/draw candidates')
    for k,z in a['pair_kicker_detail'].items():
        # Only surface strategically nontrivial pair subgroups: best action not C, or C coverage <80%, or mean C loss > .02.
        if z['best_pure']!='C' or z['cover_C']<0.80 or z['loss_C']>EPS:
            print(f'{k}: {fmt(z)}')
    print('CFG002_COMPACT_END')

if __name__=='__main__': main()
