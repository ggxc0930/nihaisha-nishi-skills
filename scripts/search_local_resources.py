#!/usr/bin/env python3
"""Search the generated local Nihaisha resource index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = REPO_ROOT / "references" / "local-resource-index.jsonl"


def load_rows(index_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with index_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def score(row: dict[str, object], terms: list[str]) -> int:
    rel = str(row.get("relative_path", ""))
    name = str(row.get("name", ""))
    top_dir = str(row.get("top_dir", ""))
    ext = str(row.get("extension", ""))
    hay = f"{rel} {name} {top_dir} {ext}".lower()
    total = 0
    matched = 0
    for term in terms:
        term_lower = term.lower()
        term_score = 0
        if term_lower in name.lower():
            term_score += 10
        if term_lower in rel.lower():
            term_score += 6
        if term_lower in top_dir.lower():
            term_score += 4
        if term_lower == ext.lstrip(".").lower() or term_lower == ext.lower():
            term_score += 3
        if term_lower in hay:
            term_score += 1
        if term_score:
            matched += 1
            total += term_score
    if not matched:
        return 0
    if matched == len(terms):
        total += 20
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Search local Nihaisha resource metadata.")
    parser.add_argument("terms", nargs="+")
    parser.add_argument("-n", "--limit", type=int, default=20)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    args = parser.parse_args()

    if not args.index.exists():
        raise SystemExit(
            f"Missing index: {args.index}\n"
            "Run: python scripts/index_local_resources.py"
        )

    rows = load_rows(args.index)
    ranked = [(score(row, args.terms), row) for row in rows]
    ranked = [(value, row) for value, row in ranked if value > 0]
    ranked.sort(key=lambda item: (-item[0], str(item[1].get("relative_path", ""))))

    if not ranked:
        print("未找到匹配结果。")
        return 0

    for value, row in ranked[: args.limit]:
        print(f"- score={value} [{row['extension']}] {row['relative_path']}")
        print(f"  size={row['size']} modified={row['modified']} risk={row['publish_risk']}")
        print(f"  path={row['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
