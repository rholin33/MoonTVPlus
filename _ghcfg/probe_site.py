#!/usr/bin/env python3
"""Probe the live site with a browser UA and confirm it serves the app."""
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("BASE", "https://moontv-plus.tarysoli33.workers.dev")
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

for path in ("/api/server-config", "/"):
    try:
        req = urllib.request.Request(
            BASE + path, headers={"User-Agent": UA, "Accept": "*/*"}
        )
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read()
            print(f"{path} -> HTTP {r.status} ({len(body)} bytes)")
            if path.endswith("server-config"):
                print("   body:", body[:300].decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        print(f"{path} -> HTTP {e.code} |", e.read()[:200].decode("utf-8", "replace"))
    except Exception as e:
        print(f"{path} -> error {type(e).__name__}: {e}")
