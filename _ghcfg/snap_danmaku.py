#!/usr/bin/env python3
"""Print the danmaku-related bits of admin_config before patching."""
import json

cfg = json.loads(json.load(open("/tmp/c.json"))[0]["results"][0]["config"])
sc = cfg.get("SiteConfig") or {}
print("SourceConfig count:", len(cfg.get("SourceConfig") or []))
print("DanmakuSourceType:", sc.get("DanmakuSourceType"))
print("DanmakuApiBase:", sc.get("DanmakuApiBase"))
tok = sc.get("DanmakuApiToken")
print("DanmakuApiToken:", (tok[:6] + "…") if tok else tok)
