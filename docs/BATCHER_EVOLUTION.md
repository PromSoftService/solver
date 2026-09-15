# Batcher evolution

This is the short operational history. Detailed evidence remains in `HISTORY.md`.

1. **v015 selected-node runner.** The stock Windows/WebView2 bridge launched the unchanged CUDA solver, solved one board, applied one history and exported one current-street node.
2. **Full-tree experiment.** Guessed monolithic APIs were rejected. Exhaustive stock traversal proved access but required 33,125 fragments, about 18.3 minutes and 589 MB for one board, so it was rejected for production.
3. **Production reset.** The supported contract became one board, one GPU solve, one configured decision history and one stock current-street export.
4. **STU001 timing proof.** Five UTG-vs-BB flops validated the 50% flop/turn abstraction and native raise semantics.
5. **STU002.** Six independent UTG-vs-BB flop decisions were solved over all 286 BRD001 flops. A JSON-to-CSV serialization defect was repaired without re-solving.
6. **Table classifier evolution.** Early wide hand tables were reduced, failed horizontal smoothing was removed, pocket pairs were split into Underpair/Weak pair/Low pocket pair, and direct draws received priority over made hands.
7. **Ten-column baseline.** B13 became an internal deterministic partition and ten final flop groups became the displayed baseline. Cells use raw combo frequencies, pure action above 65%, otherwise exact top-two 50/50; BDFD has a separate frequency split and EV veto.
8. **STU003 to STU004.** A five-flop UTG-vs-BTN pilot proved the configuration. STU004 replaced it with four selected branches across all 286 flops; the pilot package was removed from active main.
9. **Universal workbook generation.** STU002 and STU004 now use one Python entry point plus shared analysis/workbook modules. The old Node workbook builder and study-specific strategy generators were removed.
10. **Human simplification research.** Candidate flop partitions and subgroup selectors were tested manually from existing combo data. STU002 now has documented approved examples for the four-class BB response to c-bet, the three-class UTG responses to check-raise and donk, and the three-class BB response to the donk-raise; no production script generates or consumes them, and canonical solver workbooks remain unchanged.
11. **STU005 preparation.** Exact bundled BTN-open/BB-call ranges became RNG003, explicit BTN-vs-BB selected-node aliases were added, and a six-branch BRD001 package was prepared without a GPU solve. STU004 and STU005 configs now share one reproducible generator.

Current canonical outputs are one `<STU>_flop_strategy.xlsx` baseline for STU002 and one for STU004. STU005 is prepared and its GPU solve is in progress. GPU solver output, study definitions, ranges and boards are preserved.
