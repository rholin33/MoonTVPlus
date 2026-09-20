#!/usr/bin/env python3
"""Verify admin_config.SourceConfig; touch /tmp/need_fallback when empty."""
import json
import os
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/c.json"
try:
    cfg = json.loads(json.load(open(path))[0]["results"][0]["config"])
except Exception as e:
    print("PARSE_FAIL:", e)
    open("/tmp/need_fallback", "w").write("1")
    sys.exit(0)

sc = cfg.get("SourceConfig") or []
print("SourceConfig count:", len(sc))
for s in sc:
    print("   -", s.get("key"), "|", s.get("name"), "|", s.get("api"))
print("ConfigFile length:", len(cfg.get("ConfigFile") or ""))
print("SubURL:", (cfg.get("ConfigSubscribtion") or {}).get("URL"))

if not sc:
    open("/tmp/need_fallback", "w").write("1")
    print(">>> empty -> fallback needed")
else:
    if os.path.exists("/tmp/need_fallback"):
        os.remove("/tmp/need_fallback")
    print(">>> OK")
