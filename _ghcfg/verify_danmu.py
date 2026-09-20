#!/usr/bin/env python3
"""Diagnose danmaku endpoints on deployed danmu_api.

Hypothesis: globals.animes / globals.episodeIds are per-isolate in-memory caches.
search populates them on isolate A; a later comment call on isolate B 404s.
"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("BASE", "https://danmu-api.tarysoli33.workers.dev")
TOKEN = os.environ["DANMAKU_TOKEN"]
UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}
KW = os.environ.get("KW", "庆余年")


def call(path, xml=False, method="GET", body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE}/{TOKEN}{path}", data=data, headers=UA, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            b = r.read()
            return r.status, (b.decode("utf-8", "replace") if xml else json.loads(b))
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw[:200].decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


dc = lambda s: len(re.findall(r"<d p=", s)) if isinstance(s, str) else -1

print("=== 1. search ===")
st, d = call("/api/v2/search/anime?keyword=" + urllib.parse.quote(KW))
print("  HTTP", st)
animes = d.get("animes") or [] if st == 200 else []
print("  animes:", len(animes))
if not animes:
    print("  ", str(d)[:200]); raise SystemExit(0)
aid = animes[0]["animeId"]
print("  animeId:", aid, "|", animes[0]["animeTitle"])

print("=== 2. bangumi ===")
st, d = call(f"/api/v2/bangumi/{aid}")
print("  HTTP", st)
eps = (d.get("bangumi") or {}).get("episodes") or [] if st == 200 else []
print("  episodes:", len(eps))
for e in eps[:3]:
    print(f"   epId={e.get('episodeId')}  url={str(e.get('url'))[:70]}")

print("=== 3. match (POST) ===")
st, m = call("/api/v2/match", method="POST",
             body={"fileName": f"{KW}.S01E01.1080p.WEB-DL.x264.mkv"})
print("  HTTP", st, "|", json.dumps(m, ensure_ascii=False)[:220] if isinstance(m, dict) else str(m)[:200])
match_ok = isinstance(m, dict) and m.get("success")
if match_ok:
    print("  isMatched:", m.get("isMatched"), "| epId:", (m.get("match") or {}).get("episodeId"))

print("=== 4. comment by episodeId (5x, same id) ===")
if eps:
    eid = eps[0]["episodeId"]
    for i in range(5):
        st, r = call(f"/api/v2/comment/{eid}?format=xml", xml=True)
        print(f"   try{i+1}: HTTP {st} <d>={dc(r)}")
        if st == 200 and dc(r) > 0:
            print("   >>> warm-up works")
            break
        time.sleep(1)

print("=== 5. comment by url (bypasses id cache) ===")
for e in eps[:2]:
    u = e.get("url")
    if not u:
        continue
    st, r = call("/api/v2/comment?url=" + urllib.parse.quote(u, safe="") + "&format=xml", xml=True)
    print(f"   HTTP {st} <d>={dc(r)}  url={u[:60]}")

print("=== 6. search then immediately comment (same burst) ===")
st, d2 = call("/api/v2/search/anime?keyword=" + urllib.parse.quote(KW))
if st == 200 and (d2.get("animes") or []):
    aid2 = d2["animes"][0]["animeId"]
    st, b2 = call(f"/api/v2/bangumi/{aid2}")
    eps2 = (b2.get("bangumi") or {}).get("episodes") or [] if st == 200 else []
    if eps2:
        st, r = call(f"/api/v2/comment/{eps2[0]['episodeId']}?format=xml", xml=True)
        print(f"   burst: bangumi eps={len(eps2)} -> comment HTTP {st} <d>={dc(r)}")
