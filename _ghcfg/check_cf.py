#!/usr/bin/env python3
"""Verify the CF API token can list accounts, Workers and deploy."""
import json
import os
import urllib.error
import urllib.request

TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]
ACCT = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
API = "https://api.cloudflare.com/client/v4"


def call(path, method="GET", data=None):
    url = API + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"_err": f"{type(e).__name__}: {e}"}


print("=== token verify ===")
st, d = call("/user/tokens/verify")
print("  HTTP", st, "| success:", d.get("success"), "|", (d.get("result") or {}).get("status"),
      d.get("errors") or "")

print("=== accounts ===")
st, d = call("/accounts")
accts = d.get("result") or []
print("  HTTP", st, "| count:", len(accts))
for a in accts:
    print("   -", a.get("id"), a.get("name"))

print("=== workers subdomain ===")
st, d = call(f"/accounts/{ACCT}/workers/subdomain")
print("  HTTP", st, "| subdomain:", (d.get("result") or {}).get("subdomain"), d.get("errors") or "")

print("=== existing worker scripts ===")
st, d = call(f"/accounts/{ACCT}/workers/scripts")
scripts = d.get("result") or []
print("  HTTP", st, "| count:", len(scripts))
for s in scripts[:15]:
    print("   -", s.get("id"))

print("=== token permission groups (probe via /memberships) ===")
st, d = call(f"/accounts/{ACCT}/memberships")
print("  HTTP", st, "| roles:", [m.get("roles") for m in (d.get("result") or [])])
