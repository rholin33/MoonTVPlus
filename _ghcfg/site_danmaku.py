#!/usr/bin/env python3
"""Diagnose why the site's /api/danmaku/search 404s while the upstream works."""
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
BUILTIN = "https://mtvpls-danmu.netlify.app/87654321"

cfg = json.loads(json.load(open("/tmp/c.json"))[0]["results"][0]["config"])
sc = cfg.get("SiteConfig") or {}
base = (sc.get("DanmakuApiBase") or "").rstrip("/")
tok = (sc.get("DanmakuApiToken") or "").strip()
eff = base if tok == "87654321" else f"{base}/{tok}"

print("=== D1 danmaku config ===")
print("  DanmakuSourceType:", sc.get("DanmakuSourceType"))
print("  DanmakuApiBase  :", base)
print("  DanmakuApiToken :", (tok[:4] + f"…(len={len(tok)})") if tok else tok)
print("  effective base  :", eff)


def probe(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()[:160].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:160].decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


q = "?keyword=" + urllib.parse.quote(KW)
print("\n=== candidate upstream URLs (which one 404s?) ===")
for label, u in [
    ("builtin(netlify)", BUILTIN + "/api/v2/search/anime" + q),
    ("custom w/ token", eff + "/api/v2/search/anime" + q),
    ("custom no token", base + "/api/v2/search/anime" + q),
    ("site itself", SITE + "/api/v2/search/anime" + q),
]:
    st, b = probe(u)
    print(f"  {label:18s} HTTP {st}  {b[:110]}")

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


def site(path, timeout=90):
    r = urllib.request.Request(SITE + path, headers={
        "User-Agent": UA, "Accept": "application/json", "Referer": f"{SITE}/play"})
    try:
        with op.open(r, timeout=timeout) as resp:
            return resp.status, resp.read()[:250].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:250].decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


print("\n=== site reload ===")
print(" ", site("/api/admin/reload"))

print("\n=== site /api/danmaku/search (full body) ===")
for i in range(1, 6):
    st, b = site("/api/danmaku/search" + q)
    print(f"  try{i}: HTTP {st}  {b}")
    if '"animes":[' in b and '"animes":[]' not in b:
        print("\n>>> VERDICT: site OK")
        sys.exit(0)
    time.sleep(5)

print("\n>>> VERDICT: site still failing — compare candidate table above")
