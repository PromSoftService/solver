# Clean handoff / local run

## Force a local checkout to exactly match remote `main`

**Warning:** the final command deliberately deletes ignored files too, including old `output/`, `.tmp/`, caches and any other ignored local artifacts inside this repository.

Run from the repository root:

```powershell
git fetch origin
git reset --hard origin/main
git clean -fdx
```

Then verify:

```powershell
git status
```

It should report a clean working tree on `main`.

## Start the first new-generation study

```powershell
.\scripts\RUN__STU001__BRD001__AND_PUSH.cmd
```

The launcher itself fetches remote again, requires local HEAD == `origin/main`, requires a clean worktree, solves/validates every board, then commits and pushes `results/STU001__BRD001__RUN-...` automatically.

If any board fails, no study-result commit/push is made.

### If full-tree export discovery fails

The first failed board should contain:

```text
export-probes.json
bridge-transcript.jsonl
```

The batch intentionally stops immediately on `FULL_TREE_EXPORT_UNRESOLVED` instead of solving the remaining boards. Keep the incomplete ignored `output/` directory; after the exporter is fixed, resume with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-STU001.ps1 -Resume
```

Do not change STU001's poker tree merely because the native full-export bridge method needs discovery.

## Prompt for a new ChatGPT chat

```text
Продолжай работу с репозиторием:
https://github.com/PromSoftService/solver

Remote main — единственный источник истины. Не используй память старого чата вместо репозитория.

Сначала полностью прочитай:
1. AGENTS.md
2. README.md
3. docs/ARCHITECTURE.md
4. docs/STUDY_REGISTRY.md
5. docs/BRIDGE_SCHEMA.md
6. docs/HISTORY.md
7. docs/HANDOFF.md

Репозиторий 2026-09-08 был сознательно сброшен на новое поколение studies.
Старые CFG001/CFG002/CFG003 datasets и universal EXP-001..004 — только история. Они удалены из current main и НЕ являются активными данными для новой стратегии. Не восстанавливай и не анализируй их, если я отдельно этого не попрошу.

Новая обязательная архитектура:
- один flop board = один полный postflop solve;
- B33 и B75 существуют одновременно в одном дереве;
- после solve сохраняется полный solved strategy tree до river;
- flop/turn/river и любые ветки потом анализируются из сохраненного tree без повторного GPU solve;
- study result коммитится и пушится только после полной проверки всех boards;
- partial study не пушится.

Активный первый study: STU001 / RNG001 / BRD001.
Tree:
- flop B33/B75 + all-in;
- turn B33/B75 + all-in;
- river B33/B75/B150 + all-in;
- normal raise = native TexasSolver 60% pot-raise parameter + all-in;
- max one normal raise per street;
- OOP turn/river donks используют те же normal bet sizes.

Моя локальная команда study:
.\scripts\RUN__STU001__BRD001__AND_PUSH.cmd

Если study уже успешно завершился и сам запушил results/STU001__BRD001__RUN-..., сначала найди последний run в remote main, прочитай RUN_MANIFEST.json и tree.meta.json, затем работай только с этими full-tree results.

Если run остановился с FULL_TREE_EXPORT_UNRESOLVED, НЕ запускай 286 solves заново и НЕ меняй poker tree. Разбери export-probes.json и bridge-transcript.jsonl первого failed board, найди реальный full-tree export API TexasSolverGPU v0.2.0, исправь только exporter, проверь runner/CI, затем дай мне одну точную команду Resume.

Не отправляй меня в GUI, если bridge automation может решить задачу. Код/CI/анализ делай сам; GPU solve выполняется на моем Windows/NVIDIA ПК.
```
