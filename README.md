# video-transcript

视频 → 干净转写文案。三个字幕来源，一个产物（mm:ss 句式，一句一行）。

## 目录结构

> 快照。以文件系统为准。

```
video-transcript/
├── SKILL.md                   # agent 入口：路由决策树 + pipeline + 约束
├── references/
│   ├── softsub-branch.md      # 软字幕直读（B站 CC / SRT / ASS）
│   ├── hardsub-branch.md      # 硬字幕 OCR（字幕烧在画面里）
│   ├── asr-branch.md          # 音频 ASR（whisper，无字幕有旁白）
│   ├── cleaning-rules.md      # 清洗规则
│   ├── corrections.md         # 正字表（音近错 → 正确写法）
│   └── frontmatter-schema.md  # 输出数据契约（type/source/author/domain）
└── scripts/
    ├── extract_softsub.py     # B站 CC 下载（WBI 签名 + 登录 cookie）
    ├── detect_hardsub.py      # 检测有无硬字幕（抽稀疏帧 OCR，exit 0/1）
    ├── extract_hardsub_ocr.py # ffmpeg 抽帧 + easyocr 去重
    └── extract_asr.py         # ffmpeg + faster-whisper（CUDA）
```

## 三个分支

| 字幕来源 | 判断 | 脚本 |
|---|---|---|
| 软字幕 | 独立字幕轨/文件（B站 CC、SRT、ASS） | `extract_softsub.py` |
| 硬字幕 | 字幕烧在画面像素，无独立轨 | `extract_hardsub_ocr.py` |
| 音频 ASR | 无字幕、音频有旁白 | `extract_asr.py` |

判断顺序：先查字幕轨 → 没轨才 OCR → 没字才 ASR。纯画面/静音 → 报无可转写内容。

## 统一 pipeline

```
提取（脚本，机械） → 清洗（LLM，语义） → 格式化（规则，确定）
```

- 三个脚本只做机械提取，不做语义。
- 修错字 / 去幻觉 / 分段是 agent 按 `cleaning-rules.md` 做的语义工作。
- 格式化按 `frontmatter-schema.md` 输出。

## 环境依赖

三条分支共享一套环境，别人的机器从零装：

| 依赖 | 用途 | 安装 |
|---|---|---|
| Python 3.10+ | 全部脚本 | — |
| ffmpeg | 抽帧 / 抽音频 | 系统装，加入 PATH |
| torch (CUDA 版) | easyocr + faster-whisper 底层 | `pip install torch --index-url https://download.pytorch.org/whl/cu128` |
| easyocr | 硬字幕 OCR | `pip install easyocr` |
| faster-whisper | 音频 ASR | `pip install faster-whisper` |

验证环境齐没齐（三行都 OK 才算齐）：

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -c "import easyocr; easyocr.Reader(['ch_sim','en'], gpu=True)"
python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', device='cuda', compute_type='float16')"
```

**注意**
- 首次跑 easyocr / faster-whisper 会自动下模型（easyocr 到 `~/.EasyOCR`，faster-whisper `large-v3` 约 3GB）。
- 配置分层：只用软字幕无 GPU 要求；硬字幕 OCR GPU 可选（CPU 慢）；音频 ASR 强需 GPU。全分支推荐 NVIDIA GPU 8GB 显存+（RTX 3060+）、16GB 内存、20GB 磁盘空余、CUDA 12.x。RTX 50 系（Blackwell）要新版 torch / ctranslate2，否则 `cuda` 检测失败。
- B站 CC 字幕必须登录 cookie（匿名拿不到），见 `softsub-branch.md`。

## 快速上手

```bash
cd C:\Users\Administrator\.claude\skills\video-transcript

# 软字幕（B站，CC 字幕需登录 cookie，见 references/softsub-branch.md）
python scripts/extract_softsub.py <BV号或URL> <输出.txt>

# 硬字幕 OCR
python scripts/extract_hardsub_ocr.py <视频> <输出.tsv>

# 音频 ASR
python scripts/extract_asr.py <视频> <输出.txt>
```
