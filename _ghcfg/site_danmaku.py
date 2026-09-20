#!/usr/bin/env python3
"""Confirm MoonTVPlus serves danmaku via the new source.

Cross-checks the upstream directly, then exercises the site's own proxy
endpoints with retries (CF isolates may still hold a stale cached config).
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
KW = os.environ.get("KW", "庆余年")

cfg = json.loads(json.load(open("/tmp/c.json"))[0]["results"][0]["config"])
sc = cfg.get("SiteConfig") or {}
base = (sc.get("DanmakuApiBase") or "").rstrip("/")
tok = (sc.get("DanmakuApiToken") or "").strip()
eff = base if tok == "87654321" else f"{base}/{tok}"

print("=== D1 danmaku config ===")
print("  SourceType:", sc.get("DanmakuSourceType"))
print("  base:", base)
print("  token length:", len(tok))
print("  effective base:", eff)


def raw(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()[:150].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:150].decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


print("\n=== upstream direct (sanity) ===")
st, b = raw(eff + "/api/v2/search/anime?keyword=" + urllib.parse.quote(KW))
print("  with token   :", st, b[:100])
st2, b2 = raw(base + "/api/v2/search/anime?keyword=" + urllib.parse.quote(KW))
print("  without token:", st2, b2[:100])

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
body = json.dumps({"username": os.environ["U"], "password": os.environ["P"]}).encode()
req = urllib.request.Request(
    f"{SITE}/api/login", data=body, method="POST",
    headers={"Content-Type": "application/json", "User-Agent": UA,
             "Accept": "application/json", "Origin": SITE, "Referer": f"{SITE}/login"})
try:
    with op.open(req, timeout=40) as r:
        print("\nlogin HTTP", r.status)
except Exception as e:
    print("\nlogin failed:", type(e).__name__, e)
    sys.exit(0)
print("  cookies:", [c.name for c in cj])


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


print("\n=== site /api/danmaku/search (retries for cold isolates) ===")
animes = []
for i in range(1, 11):
    st, d = site("/api/danmaku/search?keyword=" + urllib.parse.quote(KW))
    n = len(d.get("animes") or []) if isinstance(d, dict) else -1
    note = "" if n > 0 else str(d)[:90]
    print(f"  try{i:2d}: HTTP {st} animes={n} {note}")
    if n > 0:
        animes = d["animes"]
        break
    time.sleep(8)

if not animes:
    print("\n>>> site search still failing")
    sys.exit(1)

print("\n=== site /api/danmaku/episodes ===")
aid = animes[0]["animeId"]
eps = []
for i in range(1, 7):
    st, d = site(f"/api/danmaku/episodes?animeId={aid}")
    eps = d.get("episodes") or [] if isinstance(d, dict) else []
    print(f"  try{i}: HTTP {st} episodes={len(eps)}")
    if eps:
        break
    time.sleep(5)

if not eps:
    print("\n>>> episodes failing")
    sys.exit(1)

print("\n=== site /api/danmaku/comment ===")
eid = eps[0]["episodeId"]
for i in range(1, 7):
    st, d = site(f"/api/danmaku/comment?episodeId={eid}")
    n = len(d.get("comments") or []) if isinstance(d, dict) else -1
    print(f"  try{i}: HTTP {st} comments={n}")
    if n > 0:
        print("\n>>> SUCCESS - MoonTVPlus serves danmaku end-to-end")
        for s in (d.get("comments") or [])[:3]:
            print("   -", str(s.get("m"))[:50])
        sys.exit(0)
    time.sleep(5)

print("\n>>> episodes ok, no comments returned")
sys.exit(1)
