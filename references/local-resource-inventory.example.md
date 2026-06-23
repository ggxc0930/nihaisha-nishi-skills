# 本地资源清单示例

> 本文件是公开仓库中的示例说明，不包含用户本机路径、文件名或私有资料清单。

## 用途

`scripts/index_local_resources.py` 可以在使用者自己的电脑上扫描倪海厦资料目录，生成本地私有索引：

- `references/local-resource-inventory.md`
- `references/local-resource-index.jsonl`

这两个生成文件默认被 `.gitignore` 忽略，不应提交到公开仓库。

## 生成方式

```bash
python scripts/index_local_resources.py --source "你的本地资料目录"
python scripts/search_local_resources.py 伤寒论
```

## 开源边界

- 公开仓库只发布 Skill、脚本、学习型整理和可复用索引能力。
- 本地视频、电子书、扫描件、讲稿、压缩包、软件、病案资料和完整文件清单保留在使用者本机。
- 若要公开某个原始资料文件，应先确认公开传播授权，再单独加入白名单。
