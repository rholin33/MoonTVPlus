#!/usr/bin/env python3
"""Verify danmaku settings landed in admin_config and the upstream answers."""
import json
import os
import re
import sys
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

# Reproduce getDanmakuApiBaseUrl()
eff = base if tok == "87654321" else f"{base}/{tok}"
print("effective base:", eff)

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}


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


print("\n=== live check via the EXACT url MoonTVPlus will build ===")
kw = "庆余年"
st, d = call("/api/v2/search/anime?keyword=" + urllib.parse.quote(kw))
print("  search  HTTP", st)
animes = d.get("animes") or [] if st == 200 else []
print("  animes:", len(animes))
if not animes:
    print("  ", str(d)[:200]); sys.exit(1)

aid = animes[0]["animeId"]
st, d = call(f"/api/v2/bangumi/{aid}")
eps = (d.get("bangumi") or {}).get("episodes") or [] if st == 200 else []
print("  bangumi HTTP", st, "| episodes:", len(eps))
if not eps:
    sys.exit(1)

eid = eps[0]["episodeId"]
print("  comment attempts (cold-isolate warm-up expected):")
for i in range(4):
    st, r = call(f"/api/v2/comment/{eid}?format=xml", xml=True)
    n = len(re.findall(r"<d p=", r)) if isinstance(r, str) else -1
    print(f"    try{i+1}: HTTP {st} | <d>={n}")
    if st == 200 and n > 0:
        print(f"\n>>> SUCCESS - {n} danmaku returned")
        break
