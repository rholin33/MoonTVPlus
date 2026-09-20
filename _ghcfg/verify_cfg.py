#!/usr/bin/env python3
"""Print admin_config.SourceConfig; exit 1 when empty so CI fails loudly."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/c.json"
try:
    cfg = json.loads(json.load(open(path))[0]["results"][0]["config"])
except Exception as e:
    print("PARSE_FAIL:", e)
    sys.exit(1)

sc = cfg.get("SourceConfig") or []
print("SourceConfig count:", len(sc))
for s in sc:
    print("   -", s.get("key"), "|", s.get("name"), "|", s.get("api"))
print("ConfigFile length:", len(cfg.get("ConfigFile") or ""))
print("SubURL:", (cfg.get("ConfigSubscribtion") or {}).get("URL"))

if not sc:
    print(">>> EMPTY - no playback sources")
    sys.exit(1)
print(">>> OK")
