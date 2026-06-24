#!/usr/bin/env python3
"""Extract legacy Office content through installed Microsoft Office COM."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "distillation-output" / "distillation-plan.jsonl"
DEFAULT_OUTPUT = ROOT / "distillation-output" / "extracted-text"


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def output_path(base: Path, relative_path: str) -> Path:
    safe = relative_path.replace("\\", "/")
    target = base / safe
    return target.with_suffix(target.suffix + ".txt")


def load_plan(plan_path: Path) -> list[dict[str, Any]]:
    with plan_path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def get_word_text(word: Any, source: Path) -> str:
    doc = word.Documents.Open(
        str(source),
        ConfirmConversions=False,
        ReadOnly=True,
        AddToRecentFiles=False,
        Visible=False,
        OpenAndRepair=True,
        NoEncodingDialog=True,
    )
    try:
        return clean_text(str(doc.Content.Text))
    finally:
        doc.Close(False)


def get_powerpoint_text(powerpoint: Any, source: Path) -> str:
    presentation = powerpoint.Presentations.Open(str(source), True, False, False)
    parts: list[str] = []
    try:
        for slide_index, slide in enumerate(presentation.Slides, start=1):
            slide_parts: list[str] = []
            for shape in slide.Shapes:
                try:
                    if shape.HasTextFrame and shape.TextFrame.HasText:
                        text = clean_text(str(shape.TextFrame.TextRange.Text))
                        if text:
                            slide_parts.append(text)
                except Exception:  # noqa: BLE001 - skip unsupported shape types.
                    continue
            if slide_parts:
                parts.append(f"## Slide {slide_index}\n" + "\n".join(slide_parts))
    finally:
        presentation.Close()
    return clean_text("\n\n".join(parts))


def get_access_text(access: Any, source: Path, max_rows_per_table: int) -> str:
    access.OpenCurrentDatabase(str(source), False)
    parts: list[str] = []
    try:
        db = access.CurrentDb()
        for table in db.TableDefs:
            name = str(table.Name)
            if name.startswith("MSys"):
                continue
            try:
                recordset = db.OpenRecordset(name)
            except Exception:  # noqa: BLE001 - skip linked or unsupported tables.
                continue
            table_lines = [f"## Table: {name}"]
            try:
                fields = [str(recordset.Fields(index).Name) for index in range(recordset.Fields.Count)]
                if fields:
                    table_lines.append(" | ".join(fields))
                count = 0
                while not recordset.EOF and count < max_rows_per_table:
                    values: list[str] = []
                    for index in range(recordset.Fields.Count):
                        value = recordset.Fields(index).Value
                        values.append("" if value is None else str(value))
                    if any(value.strip() for value in values):
                        table_lines.append(" | ".join(values))
                    count += 1
                    recordset.MoveNext()
            finally:
                recordset.Close()
            if len(table_lines) > 1:
                parts.append("\n".join(table_lines))
    finally:
        access.CloseCurrentDatabase()
    return clean_text("\n\n".join(parts))


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract legacy Office files through Microsoft Office COM.")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--top-dir")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--max-mdb-rows", type=int, default=500)
    parser.add_argument("--extensions", default=".doc,.ppt,.mdb", help="Comma-separated extensions to process.")
    args = parser.parse_args()

    if not args.plan.exists():
        raise SystemExit("Missing distillation plan. Run scripts/build_distillation_plan.py first.")

    import pythoncom
    import win32com.client

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.report:
        report_path = args.report
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = re.sub(r"[^\w.-]+", "_", args.top_dir or "all", flags=re.UNICODE)
        report_path = args.output_dir.parent / f"legacy-office-com-report-{suffix}-{stamp}.jsonl"

    extensions = {part.strip().lower() for part in args.extensions.split(",") if part.strip()}
    rows = [
        item
        for item in load_plan(args.plan)
        if item.get("action") == "convert-first" and str(item.get("extension", "")).lower() in extensions
    ]
    if args.top_dir:
        rows = [item for item in rows if item.get("top_dir") == args.top_dir]
    rows = rows[args.start :]
    if args.limit:
        rows = rows[: args.limit]

    pythoncom.CoInitialize()
    word = None
    powerpoint = None
    access = None
    counts: Counter[str] = Counter()

    def close_app(app: Any) -> None:
        if app is not None:
            try:
                app.Quit()
            except Exception:  # noqa: BLE001
                pass

    def reset_word() -> Any:
        nonlocal word
        close_app(word)
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        try:
            word.AutomationSecurity = 3
        except Exception:  # noqa: BLE001
            pass
        return word

    def reset_powerpoint() -> Any:
        nonlocal powerpoint
        close_app(powerpoint)
        powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
        powerpoint.DisplayAlerts = 1
        try:
            powerpoint.AutomationSecurity = 3
        except Exception:  # noqa: BLE001
            pass
        return powerpoint

    def reset_access() -> Any:
        nonlocal access
        close_app(access)
        access = win32com.client.DispatchEx("Access.Application")
        return access

    def extract_with_retry(ext: str, source: Path) -> str:
        nonlocal word, powerpoint, access
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                if ext == ".doc":
                    if word is None or attempt:
                        reset_word()
                    return get_word_text(word, source)
                if ext == ".ppt":
                    if powerpoint is None or attempt:
                        reset_powerpoint()
                    return get_powerpoint_text(powerpoint, source)
                if ext == ".mdb":
                    if access is None or attempt:
                        reset_access()
                    return get_access_text(access, source, args.max_mdb_rows)
                return ""
            except Exception as exc:  # noqa: BLE001 - retry after resetting Office app.
                last_error = exc
                if ext == ".doc":
                    close_app(word)
                    word = None
                elif ext == ".ppt":
                    close_app(powerpoint)
                    powerpoint = None
                elif ext == ".mdb":
                    close_app(access)
                    access = None
        if last_error is not None:
            raise last_error
        return ""

    try:
        with report_path.open("w", encoding="utf-8", newline="\n") as report:
            for index, item in enumerate(rows, start=1):
                source = Path(str(item["path"]))
                rel = str(item["relative_path"])
                ext = str(item.get("extension", "")).lower()
                target = output_path(args.output_dir, rel)
                if args.skip_existing and target.exists():
                    status = "exists"
                    counts[status] += 1
                    report.write(json.dumps({"status": status, "relative_path": rel, "target": str(target)}, ensure_ascii=False) + "\n")
                    continue
                try:
                    text = extract_with_retry(ext, source)

                    if text:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        header = f"# {rel}\n\nSource: `{source}`\nExtraction: Microsoft Office COM\n\n"
                        target.write_text(header + text + "\n", encoding="utf-8", newline="\n")
                        status = "ok"
                    else:
                        status = "empty"
                    counts[status] += 1
                    report.write(json.dumps({"status": status, "relative_path": rel, "target": str(target)}, ensure_ascii=False) + "\n")
                except Exception as exc:  # noqa: BLE001 - report and continue.
                    status = "error"
                    counts[status] += 1
                    report.write(json.dumps({"status": status, "relative_path": rel, "error": repr(exc)}, ensure_ascii=False) + "\n")
                report.flush()
                print(f"{index}/{len(rows)} {status} {rel}", flush=True)
    finally:
        for app in (word, powerpoint, access):
            close_app(app)
        pythoncom.CoUninitialize()

    print(" ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    print(f"report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
