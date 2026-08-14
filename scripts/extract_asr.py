#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""音频 ASR 转录：ffmpeg 转 wav + faster_whisper → 纯文本。

用法:
    python extract_asr.py <视频路径> <输出.txt> [--model large-v3] [--lang zh]

依赖: ffmpeg, faster_whisper, CUDA GPU（device=cuda float16）

输出: 整段无标点文本。之后由 LLM 清洗（去幻觉/台标、补标点、分段），脚本不做清洗。
"""
import argparse, subprocess, tempfile, shutil, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", help="视频路径")
    ap.add_argument("out", help="输出 txt 路径")
    ap.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "large-v3"))
    ap.add_argument("--lang", default="zh")
    args = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("缺少 faster_whisper：pip install faster-whisper", file=sys.stderr)
        return 1

    print(f"Loading model {args.model}...", flush=True)
    model = WhisperModel(args.model, device="cuda", compute_type="float16")

    tmpdir = tempfile.mkdtemp(prefix="asr_")
    try:
        wav = os.path.join(tmpdir, "audio.wav")
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", args.video, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav],
            capture_output=True,
        )
        if r.returncode != 0:
            print("ffmpeg FAIL", r.stderr.decode(errors="ignore")[-300:], file=sys.stderr)
            return 1

        segments, info = model.transcribe(wav, language=args.lang, vad_filter=False, beam_size=5)
        text = "".join(seg.text for seg in segments).strip()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(f"OK {args.out} ({len(text)} chars)")


if __name__ == "__main__":
    sys.exit(main())
