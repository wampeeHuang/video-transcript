# frontmatter 数据契约

清洗后的文案统一用这套 frontmatter。字段是数据契约，不是可选装饰。

## 模板

```yaml
---
title: "视频标题"
created: 2026-08-12
updated: 2026-08-13
type: concept
domain: AI
tags: [AI, B站]
source: https://www.bilibili.com/video/BVxxxxxxxxxxx
platform: B站
author: 秋芝2046
---
```

## 字段规则

| 字段 | 规则 |
|---|---|
| `title` | 视频标题，与文件名一致 |
| `created` | 首次转录日期 |
| `updated` | 最后清洗日期 |
| `type` | 清洗后固定 `concept`。`source` 是信息源卡片，不是转录文案 |
| `domain` | 内容领域：AI / 室内设计 / 其他，按视频主题定 |
| `tags` | `[领域, B站]`，可加第三个标签 |
| `source` | B站 URL（`https://www.bilibili.com/video/BVxxx`），不是文件名 |
| `platform` | 固定 `B站` |
| `author` | UP主名字，查得到必填 |

## 状态字段

清洗流程中可加 `status` 标记进度：

```yaml
status: 草稿    # 提取后，未清洗
status: 已清洗  # 清洗完成
```

## 关键约束

- **`type: concept` 是清洗完成的标志**，别留 `type: source`。
- **`source` 填 URL 不填文件名**，文件名不是唯一真相源。
- **`author` 查得到就填**，查不到留空或问用户，不猜。
- frontmatter 一个字都别在清洗时误改——只动正文。
