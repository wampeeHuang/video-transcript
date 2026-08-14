#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""提取视频硬烧录字幕（OCR）。

硬字幕已烧进画面像素，音频里没有，whisper 听不到 → 必须 OCR。

用法:
    python extract_hardsub_ocr.py <视频路径> <输出.tsv> [--fps 2] [--crop 0.28] [--lang ch_sim,en]

依赖: ffmpeg, easyocr, torch（GPU 可选）

输出: TSV，每行 "mm:ss<TAB>文本"。之后由 LLM 做语义清洗（去场景字噪声、纠 OCR 错、合并、格式化），脚本不做清洗。

语言: --lang 传 easyocr 语言列表（逗号分隔）。字符集过滤仍按 CJK+拉丁，
日假名/韩谚文需扩下面 CJK 判断，属待生长点。
"""
import sys, os, re, subprocess, tempfile, shutil, difflib, argparse
import easyocr

CJK = re.compile(r"[一-鿿]")


def main(video, out_tsv, fps=2, crop_ratio=0.28, lang="ch_sim,en"):
    frames_dir = tempfile.mkdtemp(prefix="hardsub_")
    try:
        y0 = 1.0 - crop_ratio
        subprocess.run([
            "ffmpeg", "-y", "-i", video,
            "-vf", "fps=%d,crop=iw:ih*%f:0:ih*%f,scale=1920:-1" % (fps, crop_ratio, y0),
            os.path.join(frames_dir, "f_%04d.png"),
        ], check=True, capture_output=True)

        frames = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
        reader = easyocr.Reader(lang.split(","), gpu=True, verbose=False)

        rows = []
        for i, fn in enumerate(frames):
            t = i / fps
            parts = []
            for bbox, text, conf in reader.readtext(os.path.join(frames_dir, fn)):
                if conf < 0.35:
                    continue
                text = text.strip()
                if not text or (not CJK.search(text) and not re.search(r"[A-Za-z]{2,}", text)):
                    continue
                parts.append(text)
            line = "".join(parts).replace("|", "").strip()
            if line:
                rows.append((t, line))

        merged = []
        for t, text in rows:
            if merged:
                pt, ptext = merged[-1]
                if difflib.SequenceMatcher(None, ptext, text).ratio() >= 0.6:
                    if len(text) > len(ptext):
                        merged[-1] = (t, text)
                    continue
            merged.append((t, text))

        with open(out_tsv, "w", encoding="utf-8") as f:
            for t, text in merged:
                m, s = divmod(int(t), 60)
                f.write("%02d:%02d\t%s\n" % (m, s, text))

        print("frames=%d rows=%d merged=%d -> %s" % (len(frames), len(rows), len(merged), out_tsv))
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out_tsv")
    ap.add_argument("--fps", type=int, default=2)
    ap.add_argument("--crop", type=float, default=0.28)
    ap.add_argument("--lang", default="ch_sim,en")
    a = ap.parse_args()
    main(a.video, a.out_tsv, a.fps, a.crop, a.lang)
