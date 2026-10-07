# Solver Viewer

Read-only local browser for the repository's compact current-street
`combos.csv` exports. It does not start TexasSolver, alter datasets, or invent
unexported tree nodes.

Run from the repository root:

```powershell
python viewer/server.py
```

Then open `http://127.0.0.1:8765`.

For a phone on the same trusted Wi-Fi, run:

```powershell
.\viewer\start-lan.cmd
```

The command listens on every network interface and prints the detected private
addresses. Use the address from the phone's Wi-Fi subnet. Allow Python on
**private networks** if Windows Firewall asks. LAN mode has no password, so
stop it before joining an untrusted network.

The viewer selects the latest local dataset run with the largest number of
available branch exports. For every exported node it supports:

- the 13x13 starting-hand matrix;
- the exact 52-card suit-combo matrix;
- action and made-hand/draw filters, combined by intersection;
- per-cell action frequencies and exact combo inspection;
- node reach height normalized to the first available exported node for the
  same acting player on that flop.

Only existing study boards and branches are shown. Rank-only flop input such
as `Q72` resolves to the study's representative suit isomorph.
