#!/usr/bin/env python3
"""Verify danmaku end-to-end through the site (fixed response parsing).

The episodes route passes the upstream payload through unchanged, so the list
lives at data["bangumi"]["episodes"], not data["episodes"].
"""
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SITE = os.environ.get("BASE", "https://moontv-plus.tarysoli33.workers.dev")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
KW = "庆余年"

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
body = json.dumps({"username": os.environ["U"], "password": os.environ["P"]}).encode()
req = urllib.request.Request(
    f"{SITE}/api/login", data=body, method="POST",
    headers={"Content-Type": "application/json", "User-Agent": UA,
             "Accept": "application/json", "Origin": SITE, "Referer": f"{SITE}/login"})
try:
    with op.open(req, timeout=40) as r:
        print("login HTTP", r.status)
except Exception as e:
    print("login failed:", type(e).__name__, e)
    sys.exit(0)


def site(path, timeout=120):
    r = urllib.request.Request(SITE + path, headers={
        "User-Agent": UA, "Accept": "application/json", "Referer": f"{SITE}/play"})
    try:
        with op.open(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        b = e.read()
        try:
            return e.code, json.loads(b)
        except Exception:
            return e.code, b[:200].decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


def episodes_of(d):
    """Handle both shapes: {bangumi:{episodes:[...]}} and {episodes:[...]}."""
    if not isinstance(d, dict):
        return []
    b = d.get("bangumi")
    if isinstance(b, dict) and b.get("episodes"):
        return b["episodes"]
    return d.get("episodes") or []


print("\n=== 1. /api/danmaku/search ===")
animes = []
for i in range(1, 9):
    st, d = site("/api/danmaku/search?keyword=" + urllib.parse.quote(KW))
    animes = d.get("animes") or [] if isinstance(d, dict) else []
    print(f"  try{i}: HTTP {st} animes={len(animes)}")
    if animes:
        break
    time.sleep(5)

if not animes:
    print(">>> search FAILED")
    sys.exit(1)
aid = animes[0]["animeId"]
print(f"  picked animeId={aid} {animes[0].get('animeTitle')}")

print("\n=== 2. /api/danmaku/episodes ===")
eps = []
for i in range(1, 9):
    st, d = site(f"/api/danmaku/episodes?animeId={aid}")
    eps = episodes_of(d)
    print(f"  try{i}: HTTP {st} episodes={len(eps)}"
          + ("" if eps else f"  keys={list(d.keys())[:6] if isinstance(d,dict) else d}"))
    if eps:
        break
    time.sleep(4)

if not eps:
    print(">>> episodes FAILED")
    sys.exit(1)
eid = eps[0].get("episodeId")
print(f"  picked episodeId={eid} {eps[0].get('episodeTitle')}")

print("\n=== 3. /api/danmaku/comment ===")
for i in range(1, 9):
    st, d = site(f"/api/danmaku/comment?episodeId={eid}")
    n = len(d.get("comments") or []) if isinstance(d, dict) else -1
    print(f"  try{i}: HTTP {st} comments={n}")
    if n > 0:
        print(f"\n>>> SUCCESS - site serves danmaku ({n} comments)")
        for s in (d.get("comments") or [])[:5]:
            print("   -", str(s.get("m"))[:55])
        sys.exit(0)
    time.sleep(4)

print("\n>>> comment FAILED")
sys.exit(1)
