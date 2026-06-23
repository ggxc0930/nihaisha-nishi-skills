#!/usr/bin/env python3
"""Build a lightweight index for a local Nihaisha resource folder.

The generated index records filenames, paths, extensions, sizes, and timestamps.
It intentionally does not copy course videos, ebooks, transcripts, or scans into
the repository.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSONL = REPO_ROOT / "references" / "local-resource-index.jsonl"
DEFAULT_MARKDOWN = REPO_ROOT / "references" / "local-resource-inventory.md"

PUBLISH_RISK_EXTENSIONS = {
    ".mp4": "course-video",
    ".mp3": "course-audio",
    ".wav": "course-audio",
    ".pdf": "ebook-or-scan",
    ".doc": "document",
    ".docx": "document",
    ".ppt": "slide-deck",
    ".pptx": "slide-deck",
    ".rar": "archive",
    ".zip": "archive",
    ".7z": "archive",
}


def human_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.2f}{unit}" if unit != "B" else f"{int(value)}B"
        value /= 1024
    return f"{num_bytes}B"


def iter_files(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        try:
            stat = file_path.stat()
            relative = file_path.relative_to(root)
        except OSError:
            continue
        parts = relative.parts
        ext = file_path.suffix.lower() or "[no extension]"
        rows.append(
            {
                "path": str(file_path),
                "relative_path": str(relative),
                "name": file_path.name,
                "top_dir": parts[0] if parts else "",
                "extension": ext,
                "size_bytes": stat.st_size,
                "size": human_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                "publish_risk": PUBLISH_RISK_EXTENSIONS.get(ext, "metadata-only"),
            }
        )
    rows.sort(key=lambda item: str(item["relative_path"]).lower())
    return rows


def write_jsonl(rows: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def markdown_table(rows: list[list[object]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_markdown(rows: list[dict[str, object]], source: Path, output: Path) -> None:
    total_size = sum(int(row["size_bytes"]) for row in rows)
    by_ext = Counter(str(row["extension"]) for row in rows)
    by_dir: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "bytes": 0})
    for row in rows:
        top_dir = str(row["top_dir"])
        by_dir[top_dir]["files"] += 1
        by_dir[top_dir]["bytes"] += int(row["size_bytes"])

    ext_rows = [[count, ext] for ext, count in by_ext.most_common(25)]
    dir_rows = [
        [top_dir, data["files"], human_size(data["bytes"])]
        for top_dir, data in sorted(by_dir.items(), key=lambda item: item[0])
    ]

    qr_candidates = [
        row
        for row in rows
        if (
            any(token in str(row["name"]).lower() for token in ("qr", "wechat", "微信", "二维码", "群"))
            and "密码" not in str(row["name"])
            and str(row["extension"]) in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        )
    ][:20]
    qr_text = (
        markdown_table(
            [[row["relative_path"], row["size"], row["modified"]] for row in qr_candidates],
            ["候选文件", "大小", "修改时间"],
        )
        if qr_candidates
        else "未在本地资源文件名中发现明确的微信/二维码图片候选；当前仓库使用 `docs/wechat_public_code.jpg`。"
    )

    content = f"""# 本地资源清单

> 本文件由 `scripts/index_local_resources.py` 生成，只记录本机资料目录的文件级元数据。不要把不适合公开的课程视频、电子书、扫描件、讲稿或压缩包直接提交到公开仓库。

## 总览

| 项目 | 数值 |
| --- | --- |
| 源目录 | `{source}` |
| 文件数 | {len(rows)} |
| 总大小 | {human_size(total_size)} |
| 详细索引 | `references/local-resource-index.jsonl` |

## 与基准 skill 的覆盖差异

| 维度 | 当前仓库基础 skill | 本地资料目录 |
| --- | --- | --- |
| 已蒸馏课程模块 | 伤寒、金匮、仲景心法、临床案例、八纲、扶阳、易筋经、梁冬、斯坦福、天纪、黄帝内经、神农本草、针灸 | 按本机资料实际覆盖补充 |
| 截图证据 | 仓库内 2986 条截图索引和 WebP 资产 | 含大量图片与视频源，可继续补充截图证据 |
| 文字资料 | 已整理笔记/电子书/日志/音频索引 | 由本机索引统计决定，可做二次蒸馏 |
| 开源策略 | 可直接作为 skill 使用 | 建议默认只开源摘要和脚本；原始资料按发布白名单处理 |

## 按顶层目录统计

{markdown_table(dir_rows, ["顶层目录", "文件数", "大小"])}

## 按扩展名统计

{markdown_table(ext_rows, ["文件数", "扩展名"])}

## 二维码候选

{qr_text}

## 使用建议

- 先用 `python scripts/search_local_resources.py <关键词>` 定位本地资料，再决定是否只做学习型摘要。
- 若要公开发布某个原始文件，先确认该文件适合公开，再把文件加入发布白名单。
- 视频、电子书、扫描件、课程讲稿、病案和处方资料默认只做本地索引，不随仓库发布。
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Index local Nihaisha resources.")
    parser.add_argument("--source", type=Path, required=True, help="Local resource folder to index.")
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()

    source = args.source
    if not source.exists():
        raise SystemExit(f"Source folder does not exist: {source}")
    rows = iter_files(source)
    write_jsonl(rows, args.jsonl)
    write_markdown(rows, source, args.markdown)
    print(f"Indexed {len(rows)} files from {source}")
    print(f"Wrote {args.jsonl}")
    print(f"Wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
