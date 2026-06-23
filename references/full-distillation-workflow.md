# 全量资料蒸馏工作流

> 本文件说明如何把本地大体量资料加工成 Skill 可用的蒸馏层。公开仓库不提交本机原始文件、完整路径清单或批处理输出。

## 目标形态

- `references/*.md`: 人工复核后的课程摘要、主题索引、方证/穴位/药性/课次地图。
- `assets/screenshots/*.webp`: 关键板书、PPT、演示截图。
- `scripts/*.py`: 本地索引、文本抽取、截图检索和蒸馏草稿生成工具。
- `distillation-output/`: 本地批处理输出，默认不提交。

## 本地全量流程

1. 生成私有资源索引：

```bash
python scripts/index_local_resources.py --source "你的本地资料目录"
```

2. 生成蒸馏计划：

```bash
python scripts/build_distillation_plan.py
```

3. 抽取文本语料：

```bash
python scripts/extract_text_corpus.py --limit 100
python scripts/extract_text_corpus.py --top-dir "某个课程目录"
```

4. 生成蒸馏草稿：

```bash
python scripts/build_distilled_reference.py
```

5. 人工复核后，把适合公开的学习型摘要迁移到 `references/*.md`。

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

## 发布边界

- 不把本地原始大文件直接提交到 Git。
- 不提交 `references/local-resource-index.jsonl`、`references/local-resource-inventory.md`、`distillation-output/`。
- 只把人工复核后的学习型摘要、索引、脚本和必要截图发布到 Skill。
