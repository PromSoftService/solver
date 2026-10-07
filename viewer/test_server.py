from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from server import combo_cell, rank_signature, resolve_board, select_exports


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


if __name__ == "__main__":
    unittest.main()
