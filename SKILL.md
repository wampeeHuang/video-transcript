---
name: video-transcript
category: 写作与文档
description: |
  把视频转成干净的转写文案（mm:ss 句式，一句一行）。按字幕来源走三条分支：软字幕直读（B站 CC 字幕 / SRT / ASS 独立字幕轨）、硬字幕 OCR（字幕烧死在画面里）、音频 ASR（无字幕有旁白，whisper）。

  **Use this skill when the user says:** 视频转录, 提取字幕, 字幕转文字, 视频转文案, 转写, 把视频转成文字稿, 字幕清洗, 提取这个视频的字幕, transcript。

  **Also trigger when:** 用户给一个视频文件/路径或 B站链接，想要它的文字稿、逐字稿、文案、字幕文本；或用户给了一堆带时间戳的碎片字幕（`[0.0s -> 1.0s] 文本`）要清洗成句式文案。

  **Do NOT trigger when:**
  - 字幕烧录/压制（SRT → 烧进视频画面）→ 用 video-subtitle-burn，方向相反
  - YouTube → B站搬运/转投 → 用 video-catwave
  - 字幕翻译（无视频、纯文本翻译）→ 不归本 skill
  - 视频放大/超分/剪辑（不涉及提取文字）→ 不归本 skill
---

# 视频转写文案

> 统一目的：**视频 → 干净文案**。三个来源，一个产物。产物是 mm:ss 句式文案，一句一行，无空行，frontmatter 完整。

## 第一步：判断字幕来源（路由）

从快到准、命中即停，三步决策树：

```
1. 有没有独立字幕轨/文件？（ffprobe 查轨 / 目录 SRT·ASS / B站 CC 接口）
   ├─ 有 → references/softsub-branch.md（直读，不上 OCR/ASR）
   └─ 无 → 2

2. 画面有没有烧死字幕？（只有无字幕轨才到这一步）
   2a. 跑 detect_hardsub.py（机械检测，exit 0=有 / 1=无，LLM 不介入）
       ├─ 有字 → references/hardsub-branch.md
       └─ 无字 → 3
   2b. 无 OCR 能力 → 抽帧看图（LLM 视觉兜底）
       ├─ 见烧字 → references/hardsub-branch.md
       └─ 未见 → 3
   2c. 两者都无（没 easyocr + 没视觉）→ 查本机安装条件
       ├─ 具备 → 推荐装 easyocr，用户 OK 装完走 2a；拒绝 → 停
       └─ 不具备 → 告知不具备条件，停

3. 无字幕轨 + 画面无字 → 音频有没有旁白？
   ├─ 有旁白 → references/asr-branch.md
   └─ 无旁白（纯画面 / 静音视频）→ 报：无可转写内容，停
```

- **B站视频**：绝大多数有 CC 字幕，先查 CC 接口，别上 OCR/ASR。
- **检测顺序原则**：先确定性脚本（ffprobe / OCR），视觉读图兜底，不靠 agent 猜。

## 第二步：统一 pipeline

三分支共享同一结构，只有「提取」层不同：

```
提取（脚本，机械） → 清洗（LLM，语义） → 格式化（规则，确定）
```

1. **提取** — 跑对应分支脚本，得到带时间戳的原始文本。脚本只做机械提取，不做语义。
2. **清洗** — 按 `references/cleaning-rules.md` 修错字、去噪声、按语义分段。这步是 LLM 语义判断，不是脚本。
3. **格式化** — 按 `references/frontmatter-schema.md` 输出 mm:ss 句式 + frontmatter。

**分支细节和脚本用法**，读对应分支文档，不读主流程也成立。

## 关键约束

- **清洗是 agent 的 LLM 语义工作**，不固化成脚本调外部 API。脚本只做提取（OCR/whisper/下载），修错字、去幻觉、分段由 agent 按规则做。
- **正字表在 `references/corrections.md`**。音译错的专有名词按表改，拿不准的保留不瞎改，交用户定。
- **提取脚本参数化**：视频路径、输出路径、模型/语言走命令行参数。title/author/domain 不进脚本，由 agent 在格式化步写入 frontmatter。
- **frontmatter 是数据契约**：type、source、author、domain 必填，格式见 `references/frontmatter-schema.md`。

## 完成检查

- [ ] 正文全部 mm:ss 句式，一句一行，无空行
- [ ] 无 `[start -> end]` 碎片残留，无半角逗号
- [ ] frontmatter 完整（type/source/author/domain）
- [ ] 音译正字表里的词已修正，拿不准的已列出交用户
