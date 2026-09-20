#!/usr/bin/env python3
"""Patch danmaku settings into admin_config (D1).

Why: getInitConfig() reads DANMAKU_API_BASE/_TOKEN from env, but getConfig()
only calls it when admin_config is EMPTY. Our table already has rows, so the
secrets are ignored. We must write SiteConfig directly.

Mirrors src/lib/danmaku/config.ts getDanmakuApiBaseUrl():
  builtin -> BUILTIN_DANMAKU_API_BASE (the dead netlify instance)
  custom  -> `${DanmakuApiBase}/${DanmakuApiToken}` (token appended when != 87654321)
"""
import json
import os
import sys
import time

cfg = json.loads(json.load(open("/tmp/c.json"))[0]["results"][0]["config"])
sc = cfg.setdefault("SiteConfig", {})

base = os.environ["DM_BASE"].rstrip("/")
token = os.environ["DM_TOKEN"].strip()

print("--- BEFORE ---")
for k in ("DanmakuSourceType", "DanmakuApiBase", "DanmakuApiToken"):
    print(f"  {k}: {sc.get(k)!r}")

sc["DanmakuSourceType"] = "custom"
sc["DanmakuApiBase"] = base
sc["DanmakuApiToken"] = token
sc.setdefault("DanmakuAutoLoadDefault", True)

print("--- AFTER (intended) ---")
for k in ("DanmakuSourceType", "DanmakuApiBase", "DanmakuApiToken"):
    v = sc.get(k)
    if k == "DanmakuApiToken":
        v = v[:6] + "…" if v else v
    print(f"  {k}: {v!r}")

effective = base if token == "87654321" else f"{base}/{token}"
print(f"  effective base URL: {effective}")

payload = json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))
sql = "UPDATE admin_config SET config='%s', updated_at=%d WHERE id=1;" % (
    payload.replace("'", "''"), int(time.time() * 1000)
)
open("/tmp/update_dm.sql", "w").write(sql)
print("sql bytes:", len(sql))
