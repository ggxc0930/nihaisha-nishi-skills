#!/usr/bin/env python3
"""Search Nihaisha Skill reference markdown files by ranked text chunks."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
QUERY_SPLIT_RE = re.compile(r"[\s,，、;；:：|/\\+]+")
SKIP_FILES = {
    "local-resource-index.jsonl",
    "local-resource-inventory.md",
}

IMPORTANT_TERMS = [
    "舌", "舌苔", "白苔", "黄苔", "厚腻", "齿痕", "裂纹", "脉", "浮", "沉", "迟", "数", "细", "弦", "滑",
    "发热", "恶寒", "怕冷", "怕风", "汗", "无汗", "有汗", "口渴", "口苦", "胸闷", "胸痛", "腹痛",
    "便秘", "下利", "小便", "失眠", "头痛", "咳嗽", "痰", "水肿", "手脚冷", "月经", "肿瘤", "癌",
    "桂枝汤", "麻黄汤", "葛根汤", "小柴胡汤", "大柴胡汤", "四逆汤", "承气汤", "白虎汤", "真武汤",
]


def normalize_terms(raw_terms: list[str]) -> list[str]:
    terms: list[str] = []
    for raw in raw_terms:
        for part in QUERY_SPLIT_RE.split(raw.strip()):
            part = part.strip()
            if part and part not in terms:
                terms.append(part)
    for term in IMPORTANT_TERMS:
        joined = "".join(raw_terms)
        if term in joined and term not in terms:
            terms.append(term)
    return terms


def iter_chunks(path: Path, window: int) -> list[tuple[int, str]]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    chunks: list[tuple[int, str]] = []
    for start in range(0, len(lines), window):
        chunk = "\n".join(lines[start : start + window]).strip()
        if chunk:
            chunks.append((start + 1, chunk))
    return chunks


def score_chunk(chunk: str, terms: list[str], filename: str) -> int:
    score = 0
    matched = 0
    hay = f"{filename}\n{chunk}"
    for term in terms:
        term_score = 0
        count = hay.count(term)
        if count:
            term_score += min(count, 5) * 4
        if term in filename:
            term_score += 5
        if re.search(rf"^#+ .*{re.escape(term)}", chunk, flags=re.MULTILINE):
            term_score += 8
        if term_score:
            matched += 1
            score += term_score
    if matched > 1:
        score += matched * 5
    if matched == len(terms):
        score += 20
    return score


def main() -> int:
    parser = argparse.ArgumentParser(description="Search references/*.md for ranked text chunks.")
    parser.add_argument("terms", nargs="+", help="Search terms, symptoms, disease names, formulas, tongue/pulse terms.")
    parser.add_argument("-n", "--limit", type=int, default=10)
    parser.add_argument("--window", type=int, default=18, help="Lines per searchable chunk.")
    parser.add_argument("--show-terms", action="store_true")
    args = parser.parse_args()

    terms = normalize_terms(args.terms)
    if args.show_terms:
        print("检索词：" + " ".join(terms))

    ranked: list[tuple[int, Path, int, str]] = []
    for path in REFERENCES.glob("*.md"):
        if path.name in SKIP_FILES:
            continue
        for line_no, chunk in iter_chunks(path, args.window):
            score = score_chunk(chunk, terms, path.name)
            if score > 0:
                ranked.append((score, path, line_no, chunk))

    ranked.sort(key=lambda item: (-item[0], item[1].name, item[2]))
    if not ranked:
        print("未找到匹配结果。")
        return 0

    for score, path, line_no, chunk in ranked[: args.limit]:
        excerpt = re.sub(r"\n{2,}", "\n", chunk)
        excerpt = "\n".join(excerpt.splitlines()[:8])
        print(f"- {path.relative_to(ROOT)}:{line_no} score={score}")
        print(excerpt)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
