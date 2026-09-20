#!/usr/bin/env python3
"""End-to-end verify danmu_api with the SAME call sequence MoonTVPlus uses.

danmu_api keeps anime details in an in-memory cache; /api/v2/bangumi/:id
returns 404 unless a preceding search populated it. So: search -> bangumi
-> comment, all against the same warm isolate.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("BASE", "https://danmu-api.tarysoli33.workers.dev")
TOKEN = os.environ["DANMAKU_TOKEN"]
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
KW = os.environ.get("KW", "庆余年")


def call(path, xml=False):
    req = urllib.request.Request(f"{BASE}/{TOKEN}{path}", headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read()
            return r.status, (body.decode("utf-8", "replace") if xml else json.loads(body))
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:250].decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


print(f"=== 1. search/anime  (keyword={KW}) ===")
st, d = call("/api/v2/search/anime?keyword=" + urllib.parse.quote(KW))
print("  HTTP", st)
if st != 200:
    print("  ", str(d)[:200]); raise SystemExit(0)
animes = d.get("animes") or []
print("  animes:", len(animes))
if not animes:
    raise SystemExit(0)

aid = animes[0]["animeId"]
print(f"  picked animeId={aid}  {animes[0]['animeTitle']}")

print("=== 2. bangumi (warm cache from step 1) ===")
st, d = call(f"/api/v2/bangumi/{aid}")
print("  HTTP", st)
if st != 200:
    print("  ", str(d)[:250]); raise SystemExit(0)
eps = (d.get("bangumi") or {}).get("episodes") or []
print("  episodes:", len(eps))
if not eps:
    raise SystemExit(0)
ep = eps[0]
cid = ep.get("episodeId")
print(f"  picked episodeId={cid}  {ep.get('episodeTitle')}")

print("=== 3. comment XML ===")
st, xml = call(f"/api/v2/comment/{cid}?format=xml", xml=True)
print("  HTTP", st, "| bytes:", len(xml) if isinstance(xml, str) else "?")
if st != 200:
    print("  ", str(xml)[:250]); raise SystemExit(0)
comments = re.findall(r"<d p=\"[^\"]*\"[^>]*>([^<]*)</d>", xml)
print("  parsed <d> nodes:", len(comments))
for c in comments[:8]:
    print("   -", c[:55])

print("=== 4. match (url based) ===")
st, d = call("/api/v2/match", )
print("  (GET match needs POST body; checking OPTIONS/route presence) HTTP", st)

if comments:
    print(f"\n>>> SUCCESS - full danmaku pipeline works ({len(comments)} comments)")
else:
    print("\n>>> XML ok but 0 comments on this episode")
