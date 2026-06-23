#!/usr/bin/env python3
"""Create a local distillation work plan from the private resource index."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "references" / "local-resource-index.jsonl"
DEFAULT_OUTPUT = ROOT / "distillation-output" / "distillation-plan.jsonl"

TEXT_EXTENSIONS = {".txt", ".md", ".htm", ".html", ".docx", ".pdf", ".xlsx"}
CONVERT_FIRST_EXTENSIONS = {".doc", ".ppt", ".mdb"}
VISUAL_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}
MEDIA_EXTENSIONS = {".mp4", ".mp3", ".wav", ".m4a"}


def load_rows(index_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with index_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def classify(ext: str) -> str:
    ext = ext.lower()
    if ext in TEXT_EXTENSIONS:
        return "extract-text"
    if ext in CONVERT_FIRST_EXTENSIONS:
        return "convert-first"
    if ext in VISUAL_EXTENSIONS:
        return "image-index"
    if ext in MEDIA_EXTENSIONS:
        return "media-keyframes-or-transcript"
    if ext in {".zip", ".rar", ".7z"}:
        return "archive-review"
    if ext in {".exe", ".apk", ".opz"}:
        return "software-metadata-only"
    return "metadata-only"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local distillation plan.")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.index.exists():
        raise SystemExit("Missing local index. Run scripts/index_local_resources.py first.")

    rows = load_rows(args.index)
    planned: list[dict[str, object]] = []
    by_action: Counter[str] = Counter()
    by_dir: dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        action = classify(str(row.get("extension", "")))
        item = {
            "action": action,
            "top_dir": row.get("top_dir", ""),
            "extension": row.get("extension", ""),
            "size_bytes": row.get("size_bytes", 0),
            "relative_path": row.get("relative_path", ""),
            "path": row.get("path", ""),
        }
        planned.append(item)
        by_action[action] += 1
        by_dir[str(row.get("top_dir", ""))][action] += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        for item in planned:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    summary = args.output.with_suffix(".md")
    lines = [
        "# 本地蒸馏计划",
        "",
        "> 本文件为本机生成产物，默认不提交到公开仓库。",
        "",
        "## 按动作统计",
        "",
        "| 动作 | 文件数 |",
        "| --- | --- |",
    ]
    for action, count in by_action.most_common():
        lines.append(f"| {action} | {count} |")
    lines.extend(["", "## 按顶层目录和动作统计", "", "| 顶层目录 | extract-text | convert-first | image-index | media-keyframes-or-transcript | metadata-only |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for top_dir in sorted(by_dir):
        counts = by_dir[top_dir]
        lines.append(
            f"| {top_dir} | {counts['extract-text']} | {counts['convert-first']} | "
            f"{counts['image-index']} | {counts['media-keyframes-or-transcript']} | {counts['metadata-only']} |"
        )
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Planned {len(planned)} files")
    print(f"Wrote {args.output}")
    print(f"Wrote {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
