#!/usr/bin/env python3
"""Confirm the MoonTVPlus site itself serves danmaku via the new source.

Logs in as owner, hits /api/admin/reload to drop the cached AdminConfig,
then calls the site's own /api/danmaku/* proxy endpoints.
"""
import http.cookiejar
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

SITE = os.environ.get("BASE", "https://moontv-plus.tarysoli33.workers.dev")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

body = json.dumps({"username": os.environ["U"], "password": os.environ["P"]}).encode()
req = urllib.request.Request(
    f"{SITE}/api/login", data=body, method="POST",
    headers={"Content-Type": "application/json", "User-Agent": UA,
             "Accept": "application/json", "Origin": SITE, "Referer": f"{SITE}/login"})
try:
    with opener.open(req, timeout=40) as r:
        print("login HTTP", r.status)
except urllib.error.HTTPError as e:
    print("login HTTP", e.code, e.read()[:200].decode("utf-8", "replace"))
    raise SystemExit(0)
except Exception as e:
    print("login error:", type(e).__name__, e)
    raise SystemExit(0)

if "auth" not in [c.name for c in cj]:
    print(">>> no auth cookie"); raise SystemExit(0)


def get(path, raw=False, timeout=120):
    r = urllib.request.Request(SITE + path, headers={
        "User-Agent": UA, "Accept": "application/json", "Referer": f"{SITE}/play"})
    try:
        with opener.open(r, timeout=timeout) as resp:
            b = resp.read()
            return resp.status, (b.decode("utf-8", "replace") if raw else json.loads(b))
    except urllib.error.HTTPError as e:
        b = e.read()
        try:
            return e.code, json.loads(b)
        except Exception:
            return e.code, b[:200].decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


print("=== reload config cache ===")
st, d = get("/api/admin/reload")
print("  HTTP", st, d if isinstance(d, dict) else str(d)[:120])

print("=== site /api/danmaku/search ===")
st, d = get("/api/danmaku/search?keyword=" + urllib.parse.quote("庆余年"))
print("  HTTP", st)
animes = d.get("animes") or [] if isinstance(d, dict) else []
print("  animes:", len(animes))
if animes:
    print("  first:", animes[0].get("animeTitle"))
    aid = animes[0]["animeId"]

    print("=== site /api/danmaku/episodes ===")
    for i in range(4):
        st, e = get(f"/api/danmaku/episodes?animeId={aid}")
        eps = e.get("episodes") or [] if isinstance(e, dict) else []
        print(f"  try{i+1}: HTTP {st} | episodes={len(eps)}")
        if eps:
            break

    if eps:
        eid = eps[0]["episodeId"]
        print("=== site /api/danmaku/comment ===")
        for i in range(4):
            st, c = get(f"/api/danmaku/comment?episodeId={eid}")
            n = len(c.get("comments") or []) if isinstance(c, dict) else -1
            print(f"  try{i+1}: HTTP {st} | comments={n}")
            if n > 0:
                print("\n>>> SUCCESS - MoonTVPlus serves danmaku end-to-end")
                sample = (c.get("comments") or [])[:3]
                for s in sample:
                    print("   -", str(s.get("m"))[:50])
                raise SystemExit(0)
        print("\n>>> search+episodes ok but no comments yet")
else:
    print("  ", str(d)[:200])
