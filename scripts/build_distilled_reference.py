#!/usr/bin/env python3
"""Build extractive Markdown drafts from local extracted text."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "distillation-output" / "extracted-text"
DEFAULT_OUTPUT = ROOT / "distillation-output" / "reference-drafts"

KEYWORDS = [
    "伤寒", "金匮", "针灸", "黄帝内经", "神农本草", "天纪", "紫微", "汉唐",
    "经方", "桂枝汤", "麻黄汤", "小柴胡汤", "四逆汤", "阳明", "少阴", "厥阴",
    "穴", "本草", "附子", "癌", "肿瘤", "水气", "痰饮", "胸痹",
]


def normalize_module(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    return rel.parts[0] if len(rel.parts) > 1 else "misc"


def select_lines(text: str, max_lines: int) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    scored: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        score = 0
        for keyword in KEYWORDS:
            if keyword in line:
                score += 3
        if re.search(r"[汤散丸饮方]|\d+\.|第.+(讲|课|章)", line):
            score += 1
        if score:
            scored.append((score, index, line))
    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = sorted(scored[:max_lines], key=lambda item: item[1])
    return [line for _, _, line in selected]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create extractive reference drafts.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-files-per-module", type=int, default=60)
    parser.add_argument("--max-lines-per-file", type=int, default=25)
    args = parser.parse_args()

    if not args.input_dir.exists():
        raise SystemExit("Missing extracted text directory. Run scripts/extract_text_corpus.py first.")

    modules: dict[str, list[Path]] = defaultdict(list)
    for path in args.input_dir.rglob("*.txt"):
        modules[normalize_module(path, args.input_dir)].append(path)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for module, paths in sorted(modules.items()):
        output = args.output_dir / f"{module}.md"
        lines = [
            f"# {module} 本地蒸馏草稿",
            "",
            "> 本文件由本地抽取文本生成，是人工复核前的草稿。发布到 Skill references 前应去除冗余、校对错字、保留学习型摘要。",
            "",
        ]
        for path in sorted(paths)[: args.max_files_per_module]:
            text = path.read_text(encoding="utf-8", errors="ignore")
            selected = select_lines(text, args.max_lines_per_file)
            if not selected:
                continue
            lines.extend([f"## {path.relative_to(args.input_dir)}", ""])
            for line in selected:
                lines.append(f"- {line[:500]}")
            lines.append("")
        output.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
