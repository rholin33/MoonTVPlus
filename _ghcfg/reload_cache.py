#!/usr/bin/env python3
"""Log in as owner (browser UA) and hit /api/admin/reload to clear isolate cache."""
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("BASE", "https://moontv-plus.tarysoli33.workers.dev")
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

body = json.dumps({"username": os.environ["U"], "password": os.environ["P"]}).encode()
req = urllib.request.Request(
    f"{BASE}/api/login",
    data=body,
    headers={"Content-Type": "application/json", "User-Agent": UA,
             "Accept": "application/json", "Origin": BASE, "Referer": f"{BASE}/login"},
    method="POST",
)
try:
    with opener.open(req, timeout=40) as r:
        print("login HTTP", r.status, "| body:", r.read()[:160].decode("utf-8", "replace"))
except urllib.error.HTTPError as e:
    print("login HTTP", e.code, "|", e.read()[:200].decode("utf-8", "replace"))
    print(">>> login blocked/failed")
    sys.exit(0)
except Exception as e:
    print("login error:", type(e).__name__, e)
    sys.exit(0)

names = [c.name for c in cj]
print("cookies:", names)
if "auth" not in names:
    print(">>> no auth cookie")
    sys.exit(0)

for ep in ("reload", "reset"):
    try:
        r = urllib.request.Request(
            f"{BASE}/api/admin/{ep}",
            headers={"User-Agent": UA, "Accept": "application/json", "Referer": f"{BASE}/admin"},
        )
        with opener.open(r, timeout=90) as resp:
            print(f"{ep} HTTP", resp.status, "|", resp.read()[:200].decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        print(f"{ep} HTTP", e.code, "|", e.read()[:200].decode("utf-8", "replace"))
    except Exception as e:
        print(f"{ep} error:", type(e).__name__, e)
