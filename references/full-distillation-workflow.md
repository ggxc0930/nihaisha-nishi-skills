# 全量资料蒸馏工作流

> 本文件说明如何把本地大体量资料加工成 Skill 可用的蒸馏层。公开仓库不提交本机原始文件、完整路径清单或批处理输出。

## 目标形态

- `references/*.md`: 人工复核后的课程摘要、主题索引、方证/穴位/药性/课次地图。
- `assets/screenshots/*.webp`: 关键板书、PPT、演示截图。
- `scripts/*.py`: 本地索引、文本抽取、截图检索和蒸馏草稿生成工具。
- `distillation-output/`: 本地批处理输出，默认不提交。

## 本地全量流程

Windows 下建议把中间产物写到 D 盘，避免占用 C 盘工作区：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_distillation_to_d.ps1 `
  -Source "你的本地资料目录" `
  -OutputRoot "D:\nihaisha-distillation" `
  -Python "python"
```

如果使用 Codex bundled Python，可把 `-Python` 设置为对应 Python 路径。

1. 生成私有资源索引：

```bash
python scripts/index_local_resources.py --source "你的本地资料目录" --jsonl "D:/nihaisha-distillation/distillation-output/local-resource-index.jsonl" --markdown "D:/nihaisha-distillation/distillation-output/local-resource-inventory.md"
```

2. 生成蒸馏计划：

```bash
python scripts/build_distillation_plan.py --index "D:/nihaisha-distillation/distillation-output/local-resource-index.jsonl" --output "D:/nihaisha-distillation/distillation-output/distillation-plan.jsonl"
```

3. 抽取文本语料：

```bash
python scripts/extract_text_corpus.py --plan "D:/nihaisha-distillation/distillation-output/distillation-plan.jsonl" --output-dir "D:/nihaisha-distillation/distillation-output/extracted-text" --limit 100
python scripts/extract_text_corpus.py --plan "D:/nihaisha-distillation/distillation-output/distillation-plan.jsonl" --output-dir "D:/nihaisha-distillation/distillation-output/extracted-text" --top-dir "某个课程目录"
```

4. 对扫描版 PDF 做 OCR：

```bash
python -m pip install rapidocr-onnxruntime
python scripts/ocr_scanned_pdfs.py --plan "D:/nihaisha-distillation/distillation-output/distillation-plan.jsonl" --output-dir "D:/nihaisha-distillation/distillation-output/extracted-text" --sort-by-pages --max-source-pages 80 --limit 10 --skip-existing
```

OCR 会显著慢于普通文本抽取。建议先用 `--sort-by-pages` 处理短 PDF，再逐步扩大 `--max-source-pages`；已经生成的文本可用 `--skip-existing` 跳过。

5. 生成蒸馏草稿：

```bash
python scripts/build_distilled_reference.py --input-dir "D:/nihaisha-distillation/distillation-output/extracted-text" --output-dir "D:/nihaisha-distillation/distillation-output/reference-drafts"
```

6. 人工复核后，把适合公开的学习型摘要迁移到 `references/*.md`。

## 文件类型策略

| 类型 | 策略 |
| --- | --- |
| PDF | 抽取文本，扫描版需要 OCR 后再进入蒸馏。 |
| DOCX | 直接抽取段落和表格。 |
| DOC | 先用 Word/LibreOffice 转成 DOCX 或 PDF。 |
| TXT/HTM | 直接抽取文本。 |
| XLSX | 抽取表格文本。 |
| 图片 | 先做文件索引；关键图可人工挑选或后续接 OCR/视觉模型。 |
| 视频/音频 | 先做文件索引；后续用转写模型和关键帧抽取。 |
| 软件/压缩包 | 只做元数据，不进入公开 Skill。 |

## 视频/音频预处理

安装或定位 `ffmpeg.exe` 和 `ffprobe.exe` 后，可先把视频/音频处理成转写用音频和关键帧：

```powershell
python scripts/process_media_assets.py `
  --queue "D:\nihaisha-distillation\distillation-output\media-transcription-queue.jsonl" `
  --output-dir "D:\nihaisha-distillation\distillation-output\media-distillation" `
  --ffmpeg "D:\path\to\ffmpeg.exe" `
  --ffprobe "D:\path\to\ffprobe.exe" `
  --audio `
  --keyframes
```

该步骤不会完成语音转文字；它只生成后续转写模型需要的低码率音频和用于人工/视觉筛选的关键帧。

如果 `ffmpeg` 报 `moov atom not found`，通常表示 MP4 索引损坏或文件不完整。此类文件不进入修复流程，记录为 damaged media 后跳过。

## 发布边界

- 不把本地原始大文件直接提交到 Git。
- 不提交 `references/local-resource-index.jsonl`、`references/local-resource-inventory.md`、`distillation-output/`。
- 只把人工复核后的学习型摘要、索引、脚本和必要截图发布到 Skill。
