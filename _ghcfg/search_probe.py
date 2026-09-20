#!/usr/bin/env python3
"""End-to-end proof: log in, call /api/search, report per-source hits."""
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("BASE", "https://moontv-plus.tarysoli33.workers.dev")
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
QUERY = os.environ.get("Q", "庆余年")

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

body = json.dumps({"username": os.environ["U"], "password": os.environ["P"]}).encode()
req = urllib.request.Request(
    f"{BASE}/api/login", data=body,
    headers={"Content-Type": "application/json", "User-Agent": UA,
             "Accept": "application/json", "Origin": BASE, "Referer": f"{BASE}/login"},
    method="POST",
)
try:
    with opener.open(req, timeout=40) as r:
        print("login HTTP", r.status)
except urllib.error.HTTPError as e:
    print("login HTTP", e.code, "|", e.read()[:200].decode("utf-8", "replace"))
    sys.exit(0)
except Exception as e:
    print("login error:", type(e).__name__, e)
    sys.exit(0)

if "auth" not in [c.name for c in cj]:
    print(">>> no auth cookie")
    sys.exit(0)

url = f"{BASE}/api/search?" + urllib.parse.urlencode({"q": QUERY})
try:
    r = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json", "Referer": f"{BASE}/search"})
    with opener.open(r, timeout=150) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
except urllib.error.HTTPError as e:
    print("search HTTP", e.code, "|", e.read()[:300].decode("utf-8", "replace"))
    sys.exit(0)
except Exception as e:
    print("search error:", type(e).__name__, e)
    sys.exit(0)

results = data.get("results") or []
print(f"query={QUERY!r}  total results: {len(results)}")
per_source = {}
for item in results:
    src = item.get("source_name") or item.get("source") or "?"
    per_source[src] = per_source.get(src, 0) + 1
print("per-source hit counts:")
for k, v in sorted(per_source.items(), key=lambda kv: -kv[1]):
    print(f"   {k}: {v}")
print("sample titles:")
for item in results[:5]:
    print("   -", item.get("title"))
if results:
    print(">>> SUCCESS - sources are live and returning data")
else:
    print(">>> no results (sources configured but none matched)")
