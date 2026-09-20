#!/usr/bin/env python3
"""Log in as owner and hit /api/admin/reset (or /api/admin/reload)."""
import json
import os
import sys
import urllib.request
import urllib.error
import http.cookiejar

BASE = os.environ.get("BASE", "https://moontv-plus.tarysoli33.workers.dev")
endpoint = "reset"
if len(sys.argv) > 1:
    endpoint = sys.argv[1]

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

body = json.dumps(
    {"username": os.environ["U"], "password": os.environ["P"]}
).encode()

req = urllib.request.Request(
    f"{BASE}/api/login",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    with opener.open(req, timeout=40) as r:
        print("login HTTP", r.status)
        print("login body:", r.read()[:200].decode("utf-8", "replace"))
except urllib.error.HTTPError as e:
    print("login HTTP", e.code, e.read()[:200].decode("utf-8", "replace"))
    print(">>> login failed")
    raise SystemExit(0)
except Exception as e:
    print("login error:", type(e).__name__, e)
    print(">>> login failed")
    raise SystemExit(0)

names = [c.name for c in cj]
print("cookies:", names)
if "auth" not in names:
    print(">>> no auth cookie")
    raise SystemExit(0)

try:
    with opener.open(f"{BASE}/api/admin/{endpoint}", timeout=90) as r:
        print(f"{endpoint} HTTP", r.status)
        print(f"{endpoint} body:", r.read()[:300].decode("utf-8", "replace"))
except urllib.error.HTTPError as e:
    print(f"{endpoint} HTTP", e.code, e.read()[:300].decode("utf-8", "replace"))
except Exception as e:
    print(f"{endpoint} error:", type(e).__name__, e)
