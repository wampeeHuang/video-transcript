# 分支 1：软字幕直读

> 视频有独立字幕轨/文件（B站 CC 字幕、SRT、ASS）。最快最准，优先走这条。

## 提取

**B站视频**：用 `scripts/extract_softsub.py` 抓 CC 字幕（AI 自动字幕）。

```bash
# 先设登录 cookie（CC 字幕匿名返回空，need_login_subtitle=True）
export BILIBILI_COOKIE="SESSDATA=xxx; bili_jct=xxx; ..."
python scripts/extract_softsub.py <BV号或B站URL> <输出.txt>
```

产出 `[0.0s -> 1.0s] 文本` 逐行碎片，每行一条。B站 CC 字幕是云端 ASR 生成，文件里已经带音近错字。

**必须登录**：B站 CC 字幕现在匿名请求返回空（`need_login_subtitle=True`），不设 `BILIBILI_COOKIE` 拿不到字幕。脚本会报"CC 字幕需登录"而不是"无字幕"，两种报错要分清。

**SRT/ASS 文件**：直接读文件文本，不用脚本。

## 清洗

软字幕噪声 = **ASR 音近错字 + 繁简混排**。

1. 正字表修音近错（`corrections.md`）
2. 繁体转简体
3. 合并碎片成句（一句 = 语义完整，到 `。？！` 或自然停顿）
4. 句内中文标点，句末 `。？！`，不留半角逗号

## 格式化

按 `frontmatter-schema.md` 输出 mm:ss 句式 + frontmatter。

时间戳 = 该句第一个碎片的 start 时间，取整到秒，格式 `mm:ss`（0.0s→00:00，65.7s→01:05）。

## 已知坑

- B站 CC 字幕的专有名词错字多（OpenClaw→OpenCloud、字节跳动→自家上当），正字表覆盖不全时**列出交用户定，不瞎改**。
- `[0.0s -> 1.0s]` 的 end 时间直接丢弃，只留 start 转 mm:ss。
