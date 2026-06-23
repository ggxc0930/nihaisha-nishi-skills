#!/usr/bin/env python3
"""Prepare media files for later transcription and visual evidence review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess


def safe_name(value: str) -> str:
    value = value.replace("\\", "/")
    value = re.sub(r"[:*?\"<>|]+", "_", value)
    value = re.sub(r"/+", "/", value).strip("/")
    return value


def run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="ignore")
    return proc.returncode, proc.stdout


def probe(ffprobe: Path, source: Path) -> dict[str, object]:
    code, out = run([
        str(ffprobe),
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-print_format",
        "json",
        str(source),
    ])
    if code != 0:
        return {"status": "error", "error": out[-2000:]}
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {"status": "error", "error": out[-2000:]}
    data["status"] = "ok"
    return data


def extract_audio(ffmpeg: Path, source: Path, target: Path) -> tuple[str, str]:
    if target.exists() and target.stat().st_size > 0:
        return "exists", ""
    target.parent.mkdir(parents=True, exist_ok=True)
    code, out = run([
        str(ffmpeg),
        "-y",
        "-i",
        str(source),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "32k",
        str(target),
    ])
    return ("ok" if code == 0 else "error"), out[-2000:]


def extract_keyframes(ffmpeg: Path, source: Path, target_dir: Path, interval_seconds: int) -> tuple[str, str]:
    done = target_dir / ".done"
    if done.exists():
        return "exists", ""
    target_dir.mkdir(parents=True, exist_ok=True)
    pattern = target_dir / "frame_%05d.jpg"
    selector = f"select='eq(n\\,0)+gte(t-prev_selected_t\\,{interval_seconds})',scale='min(1280,iw)':-2"
    code, out = run([
        str(ffmpeg),
        "-y",
        "-i",
        str(source),
        "-vf",
        selector,
        "-vsync",
        "vfr",
        "-q:v",
        "4",
        str(pattern),
    ])
    if code == 0:
        done.write_text("ok\n", encoding="utf-8")
        return "ok", ""
    return "error", out[-2000:]


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare local media files for distillation.")
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--ffprobe", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--keyframe-interval", type=int, default=600)
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--keyframes", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = args.output_dir / "media-process-report.jsonl"
    rows = [json.loads(line) for line in args.queue.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        rows = rows[args.start : args.start + args.limit]
    else:
        rows = rows[args.start :]

    processed = 0
    errors = 0
    with report.open("a", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            source = Path(str(row["path"]))
            rel = safe_name(str(row["relative_path"]))
            item_dir = args.output_dir / rel
            item_dir.mkdir(parents=True, exist_ok=True)

            metadata_path = item_dir / "metadata.json"
            if metadata_path.exists():
                metadata_status = "exists"
            else:
                metadata = probe(args.ffprobe, source)
                metadata_path.write_text(json.dumps({"source": row, "probe": metadata}, ensure_ascii=False, indent=2), encoding="utf-8")
                metadata_status = str(metadata.get("status", "unknown"))

            audio_status = "skipped"
            audio_error = ""
            if args.audio:
                audio_status, audio_error = extract_audio(args.ffmpeg, source, item_dir / "audio_16k_32k.mp3")

            frame_status = "skipped"
            frame_error = ""
            if args.keyframes:
                frame_status, frame_error = extract_keyframes(args.ffmpeg, source, item_dir / "keyframes", args.keyframe_interval)

            if "error" in (metadata_status, audio_status, frame_status):
                errors += 1
            processed += 1
            handle.write(json.dumps({
                "relative_path": row["relative_path"],
                "metadata": metadata_status,
                "audio": audio_status,
                "keyframes": frame_status,
                "audio_error": audio_error,
                "frame_error": frame_error,
            }, ensure_ascii=False) + "\n")
            print(f"{processed}/{len(rows)} {metadata_status} audio={audio_status} keyframes={frame_status} {row['relative_path']}")

    print(f"processed={processed} errors={errors}")
    print(f"report={report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
