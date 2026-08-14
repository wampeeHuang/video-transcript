#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""B站 CC 字幕下载：BV号/URL → [from -> to] 文本。

用法:
    python extract_softsub.py <BV号或B站URL> <输出.txt>

依赖: 无（标准库）。B站 CC 字幕（AI 字幕）需登录，匿名请求 need_login_subtitle=True 返回空 → 必须设环境变量 BILIBILI_COOKIE（SESSDATA 等登录 cookie）。

输出: 逐行 "[0.0s -> 1.0s] 文本" 碎片。B站 CC 字幕是云端 ASR 生成，自带音近错字，清洗交给 LLM。
"""
import json, re, sys, os, time, hashlib, urllib.request, urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
MIXIN = [46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,27,43,5,49,33,9,42,19,29,28,14,39,12,38,41,13,37,48,7,16,24,55,40,61,26,17,0,1,60,51,30,4,22,25,54,21,56,59,6,63,57,62,11,36,20,34,44,52]
COOKIE = os.environ.get("BILIBILI_COOKIE", "")


def get(url):
    headers = {"User-Agent": UA, "Referer": "https://www.bilibili.com/"}
    if COOKIE:
        headers["Cookie"] = COOKIE
    req = urllib.request.Request(url, headers=headers)
    r = urllib.request.urlopen(req, timeout=15)
    return json.loads(r.read().decode("utf-8"))


def get_wbi_keys():
    d = get("https://api.bilibili.com/x/web-interface/nav")
    img = d["data"]["wbi_img"]["img_url"].split("/")[-1].split(".")[0]
    sub = d["data"]["wbi_img"]["sub_url"].split("/")[-1].split(".")[0]
    return img, sub


def wbi_sign(params, img, sub):
    mixin = ''.join([(img + sub)[i] for i in MIXIN])[:32]
    params = dict(params)
    params["wts"] = int(time.time())
    params = {k: ''.join(ch for ch in str(v) if ch not in "!'()*") for k, v in params.items()}
    query = urllib.parse.urlencode(sorted(params.items()))
    w_rid = hashlib.md5((query + mixin).encode()).hexdigest()
    return query + "&w_rid=" + w_rid


def extract_bv(s):
    m = re.search(r"(BV[0-9A-Za-z]{10})", s)
    return m.group(1) if m else None


def download_subtitle(url):
    if url.startswith("//"):
        url = "https:" + url
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.bilibili.com/"})
    r = urllib.request.urlopen(req, timeout=30)
    return json.loads(r.read().decode("utf-8"))


def main():
    if len(sys.argv) < 3:
        print("用法: python extract_softsub.py <BV号或B站URL> <输出.txt>", file=sys.stderr)
        return 1
    bv = extract_bv(sys.argv[1])
    if not bv:
        print(f"解析不出 BV 号: {sys.argv[1]}", file=sys.stderr)
        return 1
    out = sys.argv[2]

    # 1. view API → cid + title
    view = get(f"https://api.bilibili.com/x/web-interface/view?bvid={bv}")
    if view.get("code") != 0:
        print(f"view code={view.get('code')} msg={view.get('message')}", file=sys.stderr)
        return 1
    cid = view["data"]["cid"]
    title = view["data"].get("title", "")

    # 2. player/wbi/v2 → subtitle list
    img, sub = get_wbi_keys()
    q = wbi_sign({"bvid": bv, "cid": cid}, img, sub)
    player = get(f"https://api.bilibili.com/x/player/wbi/v2?{q}")
    if player.get("code") != 0:
        print(f"player code={player.get('code')} msg={player.get('message')}", file=sys.stderr)
        return 1
    subtitles = player["data"].get("subtitle", {}).get("subtitles", [])
    if not subtitles:
        if player["data"].get("need_login_subtitle"):
            print("CC 字幕需登录：设 BILIBILI_COOKIE 环境变量（SESSDATA）后重试", file=sys.stderr)
        else:
            print("无 CC 字幕（该视频没有 AI 字幕）", file=sys.stderr)
        return 1

    # 3. 下载字幕 JSON → [from -> to] content
    sub_url = subtitles[0].get("subtitle_url")
    body = download_subtitle(sub_url).get("body", [])
    lines = []
    for item in body:
        frm = item.get("from", 0.0)
        to = item.get("to", 0.0)
        content = item.get("content", "").strip()
        if content:
            lines.append(f"[{frm}s -> {to}s] {content}")

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"title={title}")
    print(f"OK {out} ({len(lines)} 条)  cid={cid}")


if __name__ == "__main__":
    sys.exit(main())
