# Clean handoff / local run

## Force a local checkout to exactly match remote `main`

**Warning:** the final command deliberately deletes ignored files too, including old `output/`, `.tmp/`, caches and any other ignored local artifacts inside this repository.

Run from the repository root:

```powershell
git fetch origin
git reset --hard origin/main
git clean -fdx
git status
```

## Active study

Run:

```powershell
.\scripts\RUN__STU002__BRD001__AND_PUSH.cmd
```

STU002 uses RNG001 + BRD001 and the exact historical CFG001 tree-action abstraction:

- flop BB/OOP open bet: none;
- flop UTG/IP bet: 33%;
- flop BB/OOP raise parameter: 60;
- flop UTG/IP raise parameter: 100;
- turn bets/donk/raises: 100;
- river bets/donk/raises: 100;
- maxRaiseNumber=3;
- addAllinThreshold=200 study value -> native 2.0;
- all six add-all-in flags enabled.

Unlike the old CFG001 workflow, STU002 must save **the complete solved postflop tree through river** for each board. It must not export only BB_RESPONSE or UTG_CBET.

The launcher fetches remote, requires local HEAD == `origin/main`, requires a clean worktree, solves/validates all 286 boards, and only then commits/pushes `results/STU002__BRD001__RUN-...` automatically.

If any board fails, no result commit/push is made.

### If full-tree export discovery fails

The first failed board contains diagnostics such as:

```text
export-probes.json
bridge-transcript.jsonl
```

The batch intentionally stops on `FULL_TREE_EXPORT_UNRESOLVED` instead of solving the remaining boards. Keep the incomplete ignored `output/` directory. After the exporter is fixed, resume with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-STU002.ps1 -Resume
```

Do not change STU002's poker tree merely because the native full-export bridge method needs discovery.

## Prompt for a new ChatGPT chat

```text
Продолжай работу с репозиторием:
https://github.com/PromSoftService/solver

Remote main — единственный источник истины.

Сначала прочитай полностью:
1. AGENTS.md
2. README.md
3. docs/ARCHITECTURE.md
4. docs/STUDY_REGISTRY.md
5. docs/BRIDGE_SCHEMA.md
6. docs/HISTORY.md
7. docs/HANDOFF.md

Активный study: STU002 / RNG001 / BRD001.

STU002 специально использует старое компактное дерево CFG001, потому что большой multi-size STU001 считает слишком долго. Не заменяй его снова на B33/B75/B150 без прямого запроса пользователя.

Точные active tree settings:
- flop BB/OOP open bet = none;
- flop UTG/IP bet = 33%;
- flop BB/OOP raise parameter = 60;
- flop UTG/IP raise parameter = 100;
- turn bets/donk/raises = 100;
- river bets/donk/raises = 100;
- maxRaiseNumber=3;
- addAllinThreshold=200 study value -> native 2.0;
- all add-all-in flags enabled.

Ключевая новая архитектура:
- один board решается один раз;
- после solve сохраняется полный solved postflop tree до river;
- потом из сохраненного tree можно отдельно анализировать flop/turn/river/любые ветки без нового GPU solve;
- node-only export запрещен как финальный результат study;
- study пушится автоматически только после успешных 286/286 и полной проверки деревьев.

Локальная команда:
.\scripts\RUN__STU002__BRD001__AND_PUSH.cmd

Если уже появился results/STU002__BRD001__RUN-..., сначала прочитай его RUN_MANIFEST.json и tree.meta.json и работай только с этим full-tree result.

Если run остановился с FULL_TREE_EXPORT_UNRESOLVED, не меняй poker tree и не запускай остальные boards. Разбери export-probes.json и bridge-transcript.jsonl первого failed board, исправь только full-tree exporter, проверь Windows CI и дай одну точную команду Resume.

Старые CFG001/CFG002/CFG003 datasets и universal EXP-001..004 удалены из current main и не являются активными данными. Исторический CFG001 используется только как источник tree-action settings для STU002.
```
