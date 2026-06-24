#!/usr/bin/env python3
"""OCR scanned PDF files from the local distillation plan."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "distillation-output" / "distillation-plan.jsonl"
DEFAULT_OUTPUT = ROOT / "distillation-output" / "extracted-text"


def output_path(base: Path, relative_path: str) -> Path:
    safe = relative_path.replace("\\", "/")
    target = base / safe
    return target.with_suffix(target.suffix + ".txt")


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_plan(plan_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with plan_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def pdf_page_count(source: Path) -> int | None:
    import pypdfium2 as pdfium

    try:
        pdf = pdfium.PdfDocument(str(source))
        return len(pdf)
    except Exception:  # noqa: BLE001 - some damaged PDFs cannot be opened.
        return None


def render_page_to_image(page: Any, scale: float) -> Any:
    bitmap = page.render(scale=scale)
    return bitmap.to_pil().convert("RGB")


def ocr_image(engine: Any, image: Any) -> list[str]:
    import numpy as np

    result, _ = engine(np.array(image))
    if not result:
        return []

    lines: list[tuple[float, float, str, float]] = []
    for item in result:
        if len(item) < 3:
            continue
        box, text, score = item[0], str(item[1]), float(item[2])
        if not text.strip():
            continue
        try:
            y = min(float(point[1]) for point in box)
            x = min(float(point[0]) for point in box)
        except Exception:  # noqa: BLE001 - OCR boxes vary across versions.
            y, x = 0.0, 0.0
        lines.append((y, x, text.strip(), score))

    lines.sort(key=lambda row: (row[0], row[1]))
    return [text for _, _, text, _ in lines]


def ocr_pdf(source: Path, max_pages: int, scale: float, engine: Any) -> str:
    import pypdfium2 as pdfium

    parts: list[str] = []
    pdf = pdfium.PdfDocument(str(source))
    page_count = len(pdf)
    limit = min(page_count, max_pages) if max_pages else page_count
    for index in range(limit):
        page = pdf[index]
        image = render_page_to_image(page, scale)
        lines = ocr_image(engine, image)
        if lines:
            parts.append(f"\n\n## Page {index + 1}\n\n" + "\n".join(lines))
    return normalize_text("\n".join(parts))


def main() -> int:
    parser = argparse.ArgumentParser(description="OCR missing scanned PDF text outputs.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--top-dir")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--max-pages", type=int, default=80)
    parser.add_argument("--max-source-pages", type=int, default=0, help="Only OCR PDFs with this many pages or fewer; 0 means no filter.")
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--sort-by-pages", action="store_true", help="OCR shorter PDFs first.")
    args = parser.parse_args()

    if not args.plan.exists():
        raise SystemExit("Missing distillation plan. Run scripts/build_distillation_plan.py first.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.report:
        report_path = args.report
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = re.sub(r"[^\w.-]+", "_", args.top_dir or "all", flags=re.UNICODE)
        report_path = args.output_dir.parent / f"ocr-report-{suffix}-{stamp}.jsonl"

    rows = [
        item
        for item in load_plan(args.plan)
        if item.get("action") == "extract-text" and str(item.get("extension", "")).lower() == ".pdf"
    ]
    if args.top_dir:
        rows = [item for item in rows if item.get("top_dir") == args.top_dir]
    rows = [item for item in rows if not output_path(args.output_dir, str(item["relative_path"])).exists()]
    if args.sort_by_pages or args.max_source_pages:
        counted: list[tuple[int, dict[str, Any]]] = []
        for item in rows:
            pages = pdf_page_count(Path(str(item["path"])))
            if pages is None:
                continue
            if args.max_source_pages and pages > args.max_source_pages:
                continue
            item["page_count"] = pages
            counted.append((pages, item))
        counted.sort(key=lambda row: (row[0], int(row[1].get("size_bytes", 0)), str(row[1].get("relative_path", ""))))
        rows = [item for _, item in counted]
    rows = rows[args.start :]
    if args.limit:
        rows = rows[: args.limit]

    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    processed = 0
    skipped = 0
    errors = 0
    with report_path.open("w", encoding="utf-8", newline="\n") as report:
        for row in rows:
            source = Path(str(row["path"]))
            rel = str(row["relative_path"])
            target = output_path(args.output_dir, rel)
            if args.skip_existing and target.exists():
                skipped += 1
                report.write(json.dumps({"status": "exists", "relative_path": rel, "target": str(target)}, ensure_ascii=False) + "\n")
                continue
            try:
                text = ocr_pdf(source, args.max_pages, args.scale, engine)
                if text:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    header = f"# {rel}\n\nSource: `{source}`\nExtraction: OCR via RapidOCR\n\n"
                    target.write_text(header + text + "\n", encoding="utf-8", newline="\n")
                    processed += 1
                    status = "ok"
                else:
                    skipped += 1
                    status = "empty"
                report.write(json.dumps({"status": status, "relative_path": rel, "target": str(target), "page_count": row.get("page_count")}, ensure_ascii=False) + "\n")
            except Exception as exc:  # noqa: BLE001 - report and continue batch OCR.
                errors += 1
                report.write(json.dumps({"status": "error", "relative_path": rel, "error": repr(exc), "page_count": row.get("page_count")}, ensure_ascii=False) + "\n")
            report.flush()
            print(f"{processed + skipped + errors}/{len(rows)} {rel}", flush=True)

    print(f"processed={processed} skipped={skipped} errors={errors}")
    print(f"report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
