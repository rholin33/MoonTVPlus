#!/usr/bin/env python3
"""End-to-end verify the new danmu_api: search -> episodes -> danmaku XML."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("BASE", "https://danmu-api.tarysoli33.workers.dev")
TOKEN = os.environ["DANMAKU_TOKEN"]
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}


def get(path, want_xml=False):
    url = f"{BASE}/{TOKEN}{path}"
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            return r.status, (body.decode("utf-8", "replace") if want_xml else json.loads(body))
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200].decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


print("=== 1. search/anime ===")
st, d = get("/api/v2/search/anime?keyword=" + urllib.parse.quote("庆余年"))
if st != 200:
    print("  FAIL", st, d); raise SystemExit(0)
animes = d.get("animes") or []
print(f"  HTTP {st} | animes={len(animes)}")
if not animes:
    print("  no animes"); raise SystemExit(0)
a = animes[0]
aid = a["animeId"]
print(f"  picked: {a['animeTitle']} (id={aid})")

print("=== 2. bangumi episodes ===")
st, d = get(f"/api/v2/bangumi/{aid}")
if st != 200:
    print("  FAIL", st, str(d)[:200]); raise SystemExit(0)
eps = (d.get("bangumi") or {}).get("episodes") or []
print(f"  HTTP {st} | episodes={len(eps)}")
if not eps:
    print("  no episodes"); raise SystemExit(0)
e = eps[0]
cid = e.get("episodeId")
print(f"  picked: ep{cid} {e.get('episodeTitle')}")

print("=== 3. comment XML (danmaku) ===")
st, xml = get(f"/api/v2/comment/{cid}?format=xml", want_xml=True)
if st != 200:
    print("  FAIL", st, str(xml)[:200]); raise SystemExit(0)
print(f"  HTTP {st} | bytes={len(xml)}")
import re
comments = re.findall(r"<d p=\"[^\"]*\"[^>]*>([^<]*)</d>", xml)
print(f"  parsed <d> nodes: {len(comments)}")
for c in comments[:8]:
    print("   -", c[:60])
if comments:
    print("\n>>> SUCCESS - danmaku pipeline works end-to-end")
else:
    print("\n>>> XML returned but no comments (may be an episode without danmaku)")
