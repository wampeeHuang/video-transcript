# 分支 3：音频 ASR

> 画面无字幕，音频有旁白 → whisper 转录。最后手段，只在软字幕、硬字幕都没有时用。

## 部署

- 装：`pip install faster-whisper`（底层 ctranslate2）
- 首次跑自动下模型，`large-v3` 约 3GB
- 验证：`python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', device='cuda', compute_type='float16')"`
- **强需 GPU**：CPU 跑 large-v3 基本不可用；低显存用 `--model small`（约 1GB）
- RTX 50 系（Blackwell）要新版 ctranslate2，否则 cuda 检测失败

## 提取

用 `scripts/extract_asr.py`（ffmpeg 转 wav + faster_whisper）。

```bash
python scripts/extract_asr.py <视频路径> <输出.txt> [--model large-v3] [--lang zh]
```

- ffmpeg 转 16kHz 单声道 wav → faster_whisper 转录（`language=zh`，CUDA float16）。
- 依赖：ffmpeg、faster_whisper、CUDA GPU。
- 产出整段无标点文本，之后清洗补标点分段。

## 清洗

ASR 噪声 = **幻觉重复 + 台标 + 无意义片段 + 音近错字**。

1. **删幻觉重复**："土豆土豆土豆"只留合理次数，删无意义重复
2. **删台标/字幕组**："中文字幕志愿者""感谢观看""优优独播剧场"
3. **删乱码词**：明显识别错误的乱码
4. **修音近错**：`corrections.md` 正字表
5. **按语义分段**：补标点，一个完整意思一行

## 格式化

按 `frontmatter-schema.md` 输出句式文案 + frontmatter。ASR 输出无时间戳，若需 mm:ss 需回绑时间轴，否则按语义分段即可。

## 已知坑

- whisper 对无语音/BGM 蒙太奇转录出乱码 → 这种视频该走硬字幕 OCR 分支，不是 ASR。
- model 默认 `large-v3`（精度高慢），可用 `small` 提速（中文质量也可接受）。
- ASR 音近错和软字幕一样，正字表覆盖，拿不准保留。
