# 分支 2：硬字幕 OCR

> 字幕烧死在画面像素里，无独立字幕轨，whisper 听不到 → 必须 OCR。典型：无旁白 BGM 蒙太奇、字幕组硬压的视频。

## 部署

- 装：`pip install easyocr`（自动带 torch，GPU 需另装 torch CUDA 版）
- 首次跑自动下识别模型到 `~/.EasyOCR`（几百 MB）
- 验证：`python -c "import easyocr; easyocr.Reader(['ch_sim','en'], gpu=True)"`
- GPU 可选：无 GPU 时 `gpu=False`，CPU 能跑但慢

## 提取

用 `scripts/extract_hardsub_ocr.py`（ffmpeg 抽帧裁字幕区 + easyocr）。

```bash
python scripts/extract_hardsub_ocr.py <视频路径> <输出.tsv> [--fps 2] [--crop 0.28] [--lang ch_sim,en]
```

- 默认裁底部 28%，2fps 抽帧。字幕动画快或字幕短可 3fps。
- 产出 TSV：`mm:ss<TAB>文本`，已做相邻帧相似度去重。
- 依赖：ffmpeg、easyocr、torch（GPU 有 CUDA 更快）。

## 清洗

硬字幕噪声 = **场景字 + 动画拆开的短字幕 + 形近错字**。

1. **去场景字**：品牌名、警示语（"高温注意"）、水印、摄影署名、片头片尾台标
2. **合并短字幕**：动画逐字出现拆开的短字幕拼回一句
3. **纠形近错**：OCR 形近错（聱→叠、千→干、冼→选、站式→暂时 等），不是音近错
4. **补标点**：OCR 无标点，按语义补
5. 繁转简

## 格式化

按 `frontmatter-schema.md` 输出 mm:ss 句式 + frontmatter。

## 已知坑

- **硬字幕是旁白的剪辑版，会漏纯 voiceover 句**（无字幕的旁白）。要完整逐字稿时，OCR 结果 + 音频 ASR 交叉补。
- 2fps 是下限，逐字动画字幕可能漏字。
- OCR 出**形近错**（不是音近错），正字表（音近为主）覆盖不了，按上下文纠。
