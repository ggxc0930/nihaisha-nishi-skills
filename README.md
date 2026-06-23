<div align="center">

# nihaisha-nishi-skills

**把倪海厦中医课程和本地资料库整理成可检索、可追溯、有安全边界的 Agent Skill。**

Claude Code / Codex / OpenClaw Skill。装进 agent 后，可以用自然语言按症状、方剂、穴位、课程模块、课次、板书截图或本地资料文件名检索倪海厦课程资料，输出学习型辨证梳理、方证/穴位/药性对比、逐课复习计划、截图证据索引和本地资源定位。

[![Skill](https://img.shields.io/badge/Agent-Skill-orange.svg)](./SKILL.md)
[![TCM](https://img.shields.io/badge/TCM-%E5%80%AA%E6%B5%B7%E5%8E%A6-green.svg)](./references/index.md)
[![Local Resources](https://img.shields.io/badge/local%20resources-private%20index-blue.svg)](./references/local-resource-inventory.example.md)

**English** → [docs/README.en.md](./docs/README.en.md)

</div>

---

## 课程蒸馏方法

本项目参考了开源基准项目 [JuneYaooo/nihaisha-nishi-tcm](https://github.com/JuneYaooo/nihaisha-nishi-tcm) / `nihaisha-tcm` 的组织方式，并在此基础上接入本地资料清单生成脚本、检索脚本和更明确的开源边界。

## 本增强版新增什么

- **本地资源索引**：使用者可在自己的电脑上生成 `references/local-resource-inventory.md` 和 `references/local-resource-index.jsonl`，公开仓库不提交本机路径、文件名或完整资源清单。
- **本地检索脚本**：`scripts/search_local_resources.py` 可按关键词定位本地 PDF、DOC、视频、图片、软件和压缩包。
- **可再生成**：`scripts/index_local_resources.py` 可在本地资料变化后重新生成清单和 JSONL 索引。
- **全量蒸馏流水线**：`scripts/build_distillation_plan.py`、`scripts/extract_text_corpus.py`、`scripts/build_distilled_reference.py` 可把本地大资料逐步加工成 Skill 草稿。
- **更稳的开源策略**：仓库默认发布 skill、索引、截图证据和学习型整理；未确认授权的完整视频、电子书、扫描件、讲稿、压缩包和软件不直接放进公开仓库。
- **社群入口**：保留 `docs/wechat_public_code.jpg` 微信群二维码。二维码图片显示有效期到 2026-06-24 前，过期后需要替换该文件。

## 能做什么

- **白话问题入口**：把“感冒怕冷”“手脚冷”“拉肚子”“睡不着”等普通表达转成课程里的分水岭问题。
- **多课程检索**：覆盖伤寒论、金匮要略、仲景心法、临床案例、八纲辨证、扶阳论坛、易筋经、梁冬对话、斯坦福演讲、天纪、黄帝内经、神农本草、针灸课程，以及讲稿笔记、汉唐中医、诊疗日志、电子书和音频合集索引。
- **六经与方证导航**：按六经、症状、方剂和传变逻辑整理《伤寒论》核心内容。
- **穴位与药性学习**：可检索针灸经络穴位、配穴思路，以及神农本草课程里的药性、剂型、配伍与单味药线索。
- **逐课复习**：按课程模块和课次整理主题地图、关键词和适合复习的问题。
- **截图证据**：已接入 2986 条截图证据索引，对应图片均已压缩为仓库内 WebP，可按方名、穴位、课次、病机、术数关键词或时间点检索。
- **本地资料定位**：已接入本地文件级索引能力，可定位使用者本机的视频、PDF、DOC/DOCX、图片、软件、压缩包和电子书目录。
- **身体情况对标**：支持把用户的症状、疾病名、方子、舌苔/脉象描述转成课程资料检索，输出学习型方证/病机方向对比。
- **安全边界**：默认作为课程学习与中医理论整理，不做个人诊断、处方或剂量指导。

## 适合哪些场景

| 场景 | 适合程度 | 说明 |
| --- | --- | --- |
| 学习倪海厦课程 | 很适合 | 从课程模块、课次、主题、截图证据几个入口复习。 |
| 查某个方的课程方证 | 很适合 | 可返回症状群、病机层次、相关方和禁忌提醒。 |
| 查针灸、经络、穴位 | 很适合 | 可按穴位、经络、配穴场景和实操截图检索。 |
| 查本草药性或内经理论 | 适合 | 可进入神农本草、黄帝内经模块做课程学习整理。 |
| 用白话提问 | 很适合 | 先转成辨证分水岭，再进入课程术语。 |
| 身体情况和疾病名对标 | 适合 | 用 `clinical-intake-workflow.md` 和 `search_references.py` 找课程中相近的病机/方证方向。 |
| 上传方子做课程对照 | 适合 | 可分析方子在课程资料中的常见方证、分水岭和风险点，但不给个人剂量或改方。 |
| 舌苔图片或脉象描述 | 有限制 | 可把可见/文字特征转成检索词辅助分析，不做图片诊断。 |
| 找板书、PPT 或实操截图 | 适合 | 用 `scripts/search_screenshots.py` 跨模块检索截图索引。 |
| 找本地资料文件 | 适合 | 先本地生成索引，再用 `scripts/search_local_resources.py` 检索文件索引。 |
| 整理学习笔记 | 适合 | 可生成可追加到 references 的 Markdown。 |
| 真实病情用药决策 | 不适合 | 本 skill 不提供个人诊断、处方、剂量或自我用药建议。 |

## 本地资料覆盖

| 指标 | 数值 |
| --- | --- |
| 本地源目录 | 使用者自行指定 |
| 详细清单 | `references/local-resource-inventory.md`，本地生成，不提交 |
| 机器索引 | `references/local-resource-index.jsonl`，本地生成，不提交 |
| 示例说明 | [`references/local-resource-inventory.example.md`](./references/local-resource-inventory.example.md) |

对比基准项目，本项目在原有课程模块之外，提供可复用的本地资料索引与检索脚本。公开仓库默认只发布 Skill、脚本、示例说明与学习型整理，避免把未确认授权的原始资料或用户本机文件清单直接开源。

## 全量蒸馏

本项目支持把本地大体量资料逐步加工成 Skill 蒸馏层。入口说明见 [`references/full-distillation-workflow.md`](./references/full-distillation-workflow.md)。

```bash
python scripts/index_local_resources.py --source "你的本地资料目录"
python scripts/build_distillation_plan.py
python scripts/extract_text_corpus.py --top-dir "某个课程目录"
python scripts/build_distilled_reference.py
```

生成的 `distillation-output/`、`references/local-resource-index.jsonl` 和 `references/local-resource-inventory.md` 默认不提交。人工复核后的学习型摘要再迁移到 `references/*.md`。

## 课程模块

| 模块 | 文本资料 | 截图证据 |
| --- | --- | --- |
| 伤寒论 | [`references/shanghanlun.md`](./references/shanghanlun.md)、[`references/lesson-map.md`](./references/lesson-map.md)、六经/方证/症状细分模块 | [`references/screenshot-evidence.md`](./references/screenshot-evidence.md) 649 张 |
| 金匮要略 | [`references/jingui.md`](./references/jingui.md) | [`references/jingui-screenshot-evidence.md`](./references/jingui-screenshot-evidence.md) 656 张 |
| 仲景心法 | [`references/zhongjing-xinfa.md`](./references/zhongjing-xinfa.md) | [`references/zhongjing-xinfa-screenshot-evidence.md`](./references/zhongjing-xinfa-screenshot-evidence.md) 68 张 |
| 临床案例/倪师医案 | [`references/clinical-cases.md`](./references/clinical-cases.md) | [`references/clinical-cases-screenshot-evidence.md`](./references/clinical-cases-screenshot-evidence.md) 88 张 |
| 八纲辨证 | [`references/bagang.md`](./references/bagang.md) | [`references/bagang-screenshot-evidence.md`](./references/bagang-screenshot-evidence.md) 33 张代表画面 |
| 扶阳论坛 | [`references/fuyang.md`](./references/fuyang.md) | [`references/fuyang-screenshot-evidence.md`](./references/fuyang-screenshot-evidence.md) 37 张 |
| 易筋经 | [`references/yijinjing.md`](./references/yijinjing.md) | [`references/yijinjing-screenshot-evidence.md`](./references/yijinjing-screenshot-evidence.md) 28 张 |
| 梁冬对话倪师 | [`references/liangdong.md`](./references/liangdong.md) | - |
| 斯坦福大学演讲 | [`references/stanford.md`](./references/stanford.md) | - |
| 天纪 | [`references/tianji.md`](./references/tianji.md) | [`references/tianji-screenshot-evidence.md`](./references/tianji-screenshot-evidence.md) 527 张 |
| 黄帝内经 | [`references/huangdi.md`](./references/huangdi.md) | [`references/huangdi-screenshot-evidence.md`](./references/huangdi-screenshot-evidence.md) 272 张 |
| 神农本草 | [`references/bencao.md`](./references/bencao.md) | [`references/bencao-screenshot-evidence.md`](./references/bencao-screenshot-evidence.md) 127 张 |
| 针灸课程 | [`references/acupuncture.md`](./references/acupuncture.md) | [`references/acupuncture-screenshot-evidence.md`](./references/acupuncture-screenshot-evidence.md) 501 张 |

## 文字资料模块

| 模块 | 文件 | 用途 |
| --- | --- | --- |
| 针灸大成笔记 | [`references/notes-acupuncture-dacheng.md`](./references/notes-acupuncture-dacheng.md) | 针灸讲稿、针灸大成和学习笔记补充。 |
| 黄帝内经笔记 | [`references/notes-huangdi.md`](./references/notes-huangdi.md) | 内经讲稿、图文笔记和原著补充。 |
| 神农本草笔记 | [`references/notes-bencao.md`](./references/notes-bencao.md) | 本草讲稿、彩版笔记和单味药图文资料。 |
| 伤寒论笔记 | [`references/notes-shanghan.md`](./references/notes-shanghan.md) | 伤寒讲稿、图文笔记和学习笔记。 |
| 金匮要略笔记 | [`references/notes-jingui.md`](./references/notes-jingui.md) | 金匮整理稿、讲义和学习笔记。 |
| 汉唐中医 | [`references/hantang.md`](./references/hantang.md) | 汉唐文章、方剂讲解、文集医案和专题评论。 |
| 诊疗日志 | [`references/diagnostic-logs.md`](./references/diagnostic-logs.md) | 诊疗日志、病案记录、人纪班案例。 |
| 电子书合集 | [`references/ebooks.md`](./references/ebooks.md) | 电子书、原著、秘方手法和大合集索引。 |
| 音频合集 | [`references/audio-collection.md`](./references/audio-collection.md) | MP3/录音合集索引和已蒸馏课程映射。 |

## 安装

### 方式一：让 AI 自己装

把下面这段 prompt 丢给你的 AI 助手：

```text
帮我安装 nihaisha skill：
https://github.com/JuneYaooo/nihaisha-tcm
```

agent 可以 clone 仓库，再把目录安装到对应的 skills 目录。

### 方式二：手动安装

```bash
git clone git@github.com:JuneYaooo/nihaisha-tcm.git
cd nihaisha-tcm
bash install_as_skill.sh --target codex    # Codex
# 或
bash install_as_skill.sh --target claude   # Claude Code
```

脚本会把 skill 装到：

- Codex: `~/.codex/skills/nihaisha/`
- Claude Code: `~/.claude/skills/nihaisha/`
- OpenClaw: `~/skills/nihaisha/`

装完后重启对应 agent，让 skill 元数据重新加载。

## 使用示例

```text
用 nihaisha 帮我整理太阳中风和太阳伤寒的区别。
```

```text
用 nihaisha 查桂枝汤、麻黄汤、葛根汤的方证分水岭。
```

```text
用 nihaisha 按白话解释：为什么有的人感冒怕冷无汗，有的人怕风有汗？
```

```text
用 nihaisha 找小柴胡汤相关的板书截图证据。
```

```text
用 nihaisha 查金匮里胸痹、水气、痰饮相关课程脉络。
```

```text
用 nihaisha 按课程资料对标：我怕冷无汗、头项强痛、咳嗽白痰，可能和哪些方证方向相关？
```

```text
用 nihaisha 分析这个方子在倪海厦课程里更像什么方证：桂枝、白芍、炙甘草、生姜、大枣。
```

```text
用 nihaisha 根据我的舌苔描述“舌淡胖有齿痕、苔白腻”和脉象“沉细”检索相关课程方向。
```

```text
用 nihaisha 整理针灸课程里任督二脉和常用急救穴位。
```

```text
用 nihaisha 找天纪里命宫、四化相关板书证据。
```

截图检索也可以直接跑脚本：

```bash
python3 scripts/search_screenshots.py 小柴胡汤 加减
python3 scripts/search_screenshots.py 少阴 下利
python3 scripts/search_screenshots.py 天纪 命宫
python3 scripts/search_screenshots.py 针灸 足三里
python3 scripts/search_references.py 怕冷 无汗 头项强痛 麻黄汤
python3 scripts/search_references.py 舌淡 齿痕 苔白腻 沉细
python3 scripts/search_local_resources.py 伤寒论
python3 scripts/search_local_resources.py 天纪 紫微
```

> 截图索引优先返回仓库内 `assets/screenshots/...` 相对路径。梁冬对话和斯坦福演讲暂未接入截图证据。本地资源索引只在使用者自己的电脑上生成和检索，不会复制原始资料。

## 安全说明

本项目用于倪海厦课程学习、资料检索和中医理论整理，不用于医疗诊断或个体化治疗。

涉及附子类、四逆汤辈、大承气汤/急下存阴、抵当汤、大陷胸汤、癌症/肿瘤、妊娠、儿童、胸痛、意识改变、严重脱水或其他急危重症时，应立即咨询合格医生或急诊处理。

## 版权与用途说明

本项目仅作个人学习、资料整理与技术交流使用，不作商业用途。项目中涉及的课程名称、截图、转写整理与相关资料版权归原权利人所有；如有侵权或不适宜公开的内容，请联系删除。

使用者本地资料目录中的视频、电子书、扫描件、讲稿、压缩包、软件和病案资料默认按“本地元数据索引”处理，不代表拥有公开传播权。若要发布某个原始文件，请先确认授权并建立白名单。

## 致谢与社区

感谢 [Datawhale 社区](https://github.com/datawhalechina) 与 [LINUX DO — 中文开发者社区](https://linux.do/) 对开源学习、技术交流和知识共创氛围的长期推动。本项目的整理和分享也希望延续这种开放互助的社区精神，仅供学习交流使用。

## 交流社群

欢迎扫码加入微信交流群，交流倪海厦课程学习、中医理论整理、Agent Skills 使用、资料检索与学习笔记共建等相关内容。

本群仅用于非商业的学习交流与技术讨论，不提供个人诊断、处方、剂量或自我用药建议。

> 当前二维码图片显示“7 天内（6 月 24 日前）有效”，过期后请替换 `docs/wechat_public_code.jpg`。

<p align="center">
  <img src="./docs/wechat_public_code.jpg" alt="nihaisha 微信交流群二维码" width="260">
</p>

## 当前覆盖

- 已整理并接入截图图片：`01.针灸课程`、`03.黄帝内经课程`、`05.神农本草课程`、`07.伤寒论课程`、`09.金匮要略课程`、`11.仲景心法传讲`、`13.人纪之临床案例`、`14.人纪之八纲辨证`、`15.扶阳论坛`、`18.倪师易筋经`、`22.倪海厦天纪`。
- 已整理文字资料：`02.针灸大成笔记`、`04.黄帝内经笔记`、`06.神农本草笔记`、`08.伤寒论笔记`、`10.金匮要略笔记`、`12.倪师音频合集`、`16.倪师汉唐中医`、`17.倪师绝版诊疗日志`、`21.倪师电子书合集`。
- 已整理文本，截图证据待补跑：`19.梁冬对话倪师`、`20.倪师斯坦福大学演讲`。
- 已接入本地资源索引脚本：使用者可自行生成本机私有索引，详见 `references/local-resource-inventory.example.md`。
- 待扩展：其他尚未蒸馏或尚未补跑截图证据的资料。
