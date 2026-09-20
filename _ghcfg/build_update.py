#!/usr/bin/env python3
"""Build /tmp/update.sql that injects api_site sources into admin_config.

Replicates src/lib/config.ts refineConfig() derivation exactly:
  SourceConfig entry = {key, name, api, from:'config', disabled:false}
"""
import base64
import json
import os
import time

A = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(s):
    n = 0
    for c in s:
        n = n * 58 + A.index(c)
    return n.to_bytes((n.bit_length() + 7) // 8, "big")


sub_url = os.environ["SUBURL"]
raw = open("/tmp/enc.b58").read()
api_site = json.loads(b58decode(raw))["api_site"]

cfg = json.loads(json.load(open("/tmp/c.json"))[0]["results"][0]["config"])

cfg["ConfigFile"] = json.dumps(
    {"cache_time": 7200, "api_site": api_site},
    ensure_ascii=False,
    separators=(",", ":"),
)
cfg["SourceConfig"] = [
    {
        "key": k,
        "name": v["name"],
        "api": v["api"],
        "from": "config",
        "disabled": False,
    }
    for k, v in api_site.items()
]
cfg["ConfigSubscribtion"] = {
    "URL": sub_url,
    "AutoUpdate": False,
    "LastCheck": "",
}

payload = json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))
sql = "UPDATE admin_config SET config='%s', updated_at=%d WHERE id=1;" % (
    payload.replace("'", "''"),
    int(time.time() * 1000),
)
open("/tmp/update.sql", "w").write(sql)
print("sources:", len(cfg["SourceConfig"]), "| sql bytes:", len(sql))
