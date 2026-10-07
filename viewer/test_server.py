from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from server import actor_action_sources, combo_cell, rank_signature, resolve_board, select_exports


class ViewerHelpersTest(unittest.TestCase):
    def test_combo_cells_follow_standard_matrix_orientation(self) -> None:
        self.assertEqual(combo_cell("AsKs"), {"label": "AKs", "row": 0, "col": 1})
        self.assertEqual(combo_cell("AhKd"), {"label": "AKo", "row": 1, "col": 0})
        self.assertEqual(combo_cell("7c7d"), {"label": "77", "row": 7, "col": 7})

    def test_rank_only_flop_resolves_to_representative_board(self) -> None:
        boards = ["Qs 7h 2d", "As Kh Qd"]
        self.assertEqual(rank_signature("2c Qh 7s"), "Q72")
        self.assertEqual(resolve_board("Q72", boards), "Qs 7h 2d")
        self.assertEqual(resolve_board("Qh 2c 7s", boards), "Qs 7h 2d")

    def test_unknown_flop_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            resolve_board("JT9", ["Qs 7h 2d"])

    def test_legacy_branch_first_exports_are_discovered(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "01_ROOT" / "20260101-000000Z" / "combos.csv"
            path.parent.mkdir(parents=True)
            path.write_text("board,combo\n", encoding="utf-8")
            label, exports = select_exports(root, [{"id": "01_ROOT"}])
            self.assertIn("per-branch latest", label)
            self.assertEqual(exports["01_ROOT"], path)

    def test_actor_range_uses_only_actors_earlier_actions(self) -> None:
        branches = [
            {"id": "01_BB_FIRST", "acting_player": "BB", "history": "flop root", "action_shape": "CHECK_DONK"},
            {"id": "02_BTN_AFTER_CHECK", "acting_player": "BTN", "history": "BB Check", "action_shape": "CHECK_BET"},
            {"id": "03_BB_AFTER_CBET", "acting_player": "BB", "history": "BB Check -> BTN Bet 50%", "action_shape": "FOLD_CALL_RAISE"},
            {"id": "04_BTN_AFTER_CHECK_RAISE", "acting_player": "BTN", "history": "BB Check -> BTN Bet 50% -> BB Raise 60 native", "action_shape": "FOLD_CALL"},
        ]
        entry = {"study": {"branches": branches}, "exports": {branch["id"]: Path(branch["id"]) for branch in branches}}
        bb_sources = actor_action_sources(entry, branches[2])
        btn_sources = actor_action_sources(entry, branches[3])
        self.assertEqual([(source["id"], action) for source, action, _ in bb_sources], [("01_BB_FIRST", "check")])
        self.assertEqual([(source["id"], action) for source, action, _ in btn_sources], [("02_BTN_AFTER_CHECK", "bet")])


if __name__ == "__main__":
    unittest.main()
