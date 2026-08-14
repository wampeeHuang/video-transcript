#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检测视频是否含硬烧录字幕（轻量预检，机械判断，LLM 不介入）。

抽稀疏几帧跑 OCR，判断画面底部有没有烧字。有字 exit 0，无字 exit 1。
路由用：无字幕轨时，先跑本脚本判有没有硬字幕，再决定走 OCR 还是 ASR。

用法:
    python detect_hardsub.py <视频路径> [--frames 5] [--crop 0.28] [--lang ch_sim,en]

依赖: ffmpeg, easyocr
返回: 0=有硬字幕, 1=无硬字幕

语言: --lang 传 easyocr 语言列表（逗号分隔）。字符集过滤仍按 CJK+拉丁，
日假名/韩谚文需扩下面 CJK 判断，属待生长点。
"""
import sys, os, re, subprocess, tempfile, shutil, argparse
import easyocr

CJK = re.compile(r"[一-鿿]")


def main(video, n_frames=5, crop_ratio=0.28, lang="ch_sim,en"):
    frames_dir = tempfile.mkdtemp(prefix="hardsub_detect_")
    try:
        y0 = 1.0 - crop_ratio
        # 每 15s 一帧，最多 n_frames 帧，覆盖开头（硬字幕通常贯穿全程）
        subprocess.run([
            "ffmpeg", "-y", "-i", video,
            "-vf", "fps=1/15,crop=iw:ih*%f:0:ih*%f,scale=1920:-1" % (crop_ratio, y0),
            "-frames:v", str(n_frames),
            os.path.join(frames_dir, "f_%04d.png"),
        ], check=True, capture_output=True)

        frames = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
        if not frames:
            print("无硬字幕：抽帧失败或视频过短", file=sys.stderr)
            return 1

        reader = easyocr.Reader(lang.split(","), gpu=True, verbose=False)

        hit = 0
        for fn in frames:
            for bbox, text, conf in reader.readtext(os.path.join(frames_dir, fn)):
                if conf < 0.35:
                    continue
                text = text.strip()
                if not text or (not CJK.search(text) and not re.search(r"[A-Za-z]{2,}", text)):
                    continue
                hit += 1

        if hit:
            print("有硬字幕（%d 帧检出文字）" % len(frames))
            return 0
        print("无硬字幕（%d 帧均无文字）" % len(frames))
        return 1
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--frames", type=int, default=5)
    ap.add_argument("--crop", type=float, default=0.28)
    ap.add_argument("--lang", default="ch_sim,en")
    a = ap.parse_args()
    sys.exit(main(a.video, a.frames, a.crop, a.lang))
