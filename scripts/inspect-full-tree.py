#!/usr/bin/env python3
"""Inspect and independently validate a TexasSolverGPU full-tree archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable


STRATEGY_FIELDS = ("card_strings", "reach_probs", "strategy_probs", "action_evs", "evs")
STREET_ROUNDS = {"flop": 1, "turn": 2, "river": 3}


def parse_history(value: str) -> tuple[int, ...]:
    value = value.strip()
    if not value or value.lower() == "root":
        return ()
    try:
        return tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("history/path must be comma-separated integers") from exc


def history_key(history: Iterable[int]) -> str:
    values = tuple(history)
    return "root" if not values else ",".join(str(value) for value in values)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_nodes(root: dict[str, Any], path: tuple[int, ...] = ()):
    yield path, root
    children = root.get("childrens")
    if isinstance(children, list):
        for index, child in enumerate(children):
            if isinstance(child, dict):
                yield from iter_nodes(child, path + (index,))
    elif isinstance(children, dict):
        for key, child in children.items():
            if isinstance(child, dict):
                yield from iter_nodes(child, path + (key,))


def chance_boundaries(root: dict[str, Any]) -> list[tuple[int, ...]]:
    result: list[tuple[int, ...]] = []

    def visit(node: dict[str, Any], path: tuple[int, ...]) -> None:
        if node.get("type") == "chance":
            children = node.get("childrens")
            if children not in ({}, [], None):
                raise ValueError(f"current-street fragment crossed chance boundary at {path}")
            result.append(path)
            return
        children = node.get("childrens")
        if isinstance(children, list):
            for index, child in enumerate(children):
                if isinstance(child, dict):
                    visit(child, path + (index,))

    visit(root, ())
    return result


def validate_native_fragment(root: dict[str, Any], expected_round: int) -> dict[str, int]:
    counts = {"action": 0, "chance": 0, "terminal": 0}
    for path, node in iter_nodes(root):
        node_type = node.get("type")
        if node_type not in counts:
            raise ValueError(f"unknown node type {node_type!r} at {path}")
        counts[node_type] += 1
        if "betting round" in node and int(node["betting round"]) != expected_round:
            raise ValueError(f"wrong betting round at {path}: {node['betting round']} != {expected_round}")
        if node_type == "action":
            strategy = node.get("strategy")
            if not isinstance(strategy, dict):
                raise ValueError(f"action node has no strategy at {path}")
            missing = [field for field in STRATEGY_FIELDS if field not in strategy]
            if missing:
                raise ValueError(f"strategy is missing {missing} at {path}")
    chance_boundaries(root)
    return counts


def load_index(archive: zipfile.ZipFile) -> list[dict[str, Any]]:
    with archive.open("index.jsonl") as source:
        return [json.loads(line) for line in source if line.strip()]


def validate_graph(manifest: dict[str, Any], records: list[dict[str, Any]], names: set[str]) -> dict[str, Any]:
    if manifest.get("format") != "texassolvergpu-full-tree-fragments":
        raise ValueError("unsupported archive format")
    by_key: dict[str, dict[str, Any]] = {}
    for record in records:
        key = record["history_key"]
        if key in by_key:
            raise ValueError(f"duplicate history key: {key}")
        if record["entry"] not in names:
            raise ValueError(f"missing fragment entry: {record['entry']}")
        if history_key(record["history"]) != key:
            raise ValueError(f"history key mismatch: {key}")
        by_key[key] = record
    if "root" not in by_key:
        raise ValueError("root fragment is missing")
    if int(manifest["fragment_count"]) != len(records):
        raise ValueError("manifest fragment_count does not match index")
    fragment_entries = {name for name in names if name.startswith("fragments/") and name.endswith(".json")}
    if len(fragment_entries) != len(records):
        raise ValueError("archive fragment-entry count does not match index")

    edges = 0
    missing: list[str] = []
    for record in records:
        parent_round = int(record["betting_round"])
        for boundary in record.get("chance_boundaries", []):
            for child in boundary.get("legal_cards", []):
                edges += 1
                child_key = child["history_key"]
                child_record = by_key.get(child_key)
                if child_record is None:
                    missing.append(child_key)
                elif int(child_record["betting_round"]) != parent_round + 1:
                    raise ValueError(f"street transition mismatch: {record['history_key']} -> {child_key}")
    if manifest.get("complete") and missing:
        raise ValueError(f"complete archive has {len(missing)} missing chance children; first={missing[0]}")
    if int(manifest["chance_edge_count"]) != edges:
        raise ValueError("manifest chance_edge_count does not match index")
    return {"indexed_fragments": len(records), "chance_edges": edges, "missing_children": len(missing)}


def deep_validate(archive: zipfile.ZipFile, records: list[dict[str, Any]]) -> dict[str, Any]:
    total_nodes = {"action": 0, "chance": 0, "terminal": 0}
    total_bytes = 0
    for number, record in enumerate(records, 1):
        raw = archive.read(record["entry"])
        total_bytes += len(raw)
        if len(raw) != int(record["native_bytes"]):
            raise ValueError(f"native byte count mismatch: {record['entry']}")
        digest = hashlib.sha256(raw).hexdigest()
        if digest != record["native_sha256"]:
            raise ValueError(f"native SHA256 mismatch: {record['entry']}")
        node = json.loads(raw)
        counts = validate_native_fragment(node, int(record["betting_round"]))
        expected_boundaries = [tuple(item["relative_history"]) for item in record.get("chance_boundaries", [])]
        if chance_boundaries(node) != expected_boundaries:
            raise ValueError(f"chance-boundary index mismatch: {record['entry']}")
        for key in total_nodes:
            total_nodes[key] += counts[key]
        if number == 1 or number % 1000 == 0:
            print(f"deep validation: {number}/{len(records)} fragments", file=sys.stderr)
    return {"native_bytes": total_bytes, "nodes": total_nodes}


def select_node(root: dict[str, Any], path: tuple[int, ...]) -> dict[str, Any]:
    node = root
    for index in path:
        children = node.get("childrens")
        if not isinstance(children, list) or index < 0 or index >= len(children):
            raise ValueError(f"invalid action path at index {index}")
        node = children[index]
    return node


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--deep", action="store_true", help="read, hash, parse and validate every native fragment")
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--history", type=parse_history, help="extract the fragment with this absolute history")
    parser.add_argument("--path", type=parse_history, default=(), help="action path inside the selected fragment")
    parser.add_argument("--output", type=Path, help="write the selected native node as JSON")
    args = parser.parse_args()

    archive_sha256 = sha256_file(args.archive)
    with zipfile.ZipFile(args.archive) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
        records = load_index(archive)
        if not manifest.get("complete") and not args.allow_incomplete:
            raise ValueError("archive is explicitly marked incomplete")
        result = validate_graph(manifest, records, names)
        result.update({
            "archive": str(args.archive.resolve()),
            "archive_sha256": archive_sha256,
            "archive_bytes": args.archive.stat().st_size,
            "complete": bool(manifest.get("complete")),
            "board": manifest.get("board"),
            "fragments_by_street": manifest.get("fragments_by_street"),
        })
        if args.deep:
            result["deep"] = deep_validate(archive, records)
        if args.history is not None:
            by_key = {record["history_key"]: record for record in records}
            key = history_key(args.history)
            if key not in by_key:
                raise ValueError(f"history not found: {key}")
            selected = select_node(json.loads(archive.read(by_key[key]["entry"])), args.path)
            text = json.dumps(selected, ensure_ascii=False, indent=2)
            if args.output:
                args.output.write_text(text + "\n", encoding="utf-8")
                result["selected_output"] = str(args.output.resolve())
            else:
                print(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(f"FULL-TREE VALIDATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
