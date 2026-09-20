#!/usr/bin/env python3
"""Verify danmaku config + live pipeline, tolerating cold-isolate warm-up.

danmu_api keeps animes/episodeIds in per-isolate memory. A freshly routed
request can 404 on /bangumi or /comment until that isolate has seen a search.
Retry the whole chain a few times before declaring failure.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

cfg = json.loads(json.load(open("/tmp/c.json"))[0]["results"][0]["config"])
sc = cfg.get("SiteConfig") or {}

print("=== admin_config.SiteConfig (danmaku) ===")
for k in ("DanmakuSourceType", "DanmakuApiBase", "DanmakuApiToken", "DanmakuAutoLoadDefault"):
    v = sc.get(k)
    if k == "DanmakuApiToken" and v:
        v = v[:6] + "…"
    print(f"  {k}: {v!r}")

st = sc.get("DanmakuSourceType")
base = (sc.get("DanmakuApiBase") or "").rstrip("/")
tok = (sc.get("DanmakuApiToken") or "").strip()
ok = st == "custom" and "tarysoli33" in base and tok and tok != "87654321"
print(f"\nconfig looks right: {'YES' if ok else 'NO'}")
if not ok:
    sys.exit(1)

eff = base if tok == "87654321" else f"{base}/{tok}"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
KW = "庆余年"


def call(path, xml=False):
    req = urllib.request.Request(eff + path, headers=UA)
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


print("\n=== live pipeline (retry to survive cold isolates) ===")
final = None
for attempt in range(1, 6):
    st1, d1 = call("/api/v2/search/anime?keyword=" + urllib.parse.quote(KW))
    animes = d1.get("animes") or [] if st1 == 200 else []
    if not animes:
        print(f"  [{attempt}] search HTTP {st1} -> no animes, retrying")
        time.sleep(2)
        continue
    aid = animes[0]["animeId"]

    st2, d2 = call(f"/api/v2/bangumi/{aid}")
    eps = (d2.get("bangumi") or {}).get("episodes") or [] if st2 == 200 else []
    if not eps:
        print(f"  [{attempt}] search ok({len(animes)}) | bangumi HTTP {st2} -> 0 eps, retrying")
        time.sleep(2)
        continue

    eid = eps[0]["episodeId"]
    st3, xml = call(f"/api/v2/comment/{eid}?format=xml", xml=True)
    n = len(re.findall(r"<d p=", xml)) if isinstance(xml, str) else -1
    print(f"  [{attempt}] search ok({len(animes)}) | bangumi ok({len(eps)} eps) | "
          f"comment HTTP {st3} <d>={n}")
    if st3 == 200 and n > 0:
        final = n
        break
    time.sleep(2)

if final:
    print(f"\n>>> SUCCESS - danmaku pipeline live, {final} comments on ep1")
else:
    print("\n>>> pipeline did not return danmaku in 5 attempts")
    sys.exit(1)
