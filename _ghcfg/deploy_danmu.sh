#!/usr/bin/env bash
# Deploy huangxd-/danmu_api to Cloudflare Workers, then verify it live.
set -uo pipefail

SRC=/tmp/danmu
UPSTREAM_SHA="ea88a15a7a1990cb62a2dbaf637061f6a4249679"

echo "=== 1. fetch upstream source ==="
rm -rf "$SRC" && mkdir -p "$SRC" && cd "$SRC"
curl -sL --max-time 120 \
  "https://github.com/huangxd-/danmu_api/archive/${UPSTREAM_SHA}.tar.gz" -o d.tgz
tar xzf d.tgz --strip-components=1
echo "files: $(find . -type f | wc -l)"
test -f danmu_api/worker.js && echo "worker.js: OK" || { echo "worker.js MISSING"; exit 1; }

echo "=== 2. install deps ==="
npm install --omit=dev --no-audit --no-fund >/tmp/npm.log 2>&1 || { tail -20 /tmp/npm.log; exit 1; }
echo "deps installed: $(ls node_modules | wc -l) packages"
npm i -g wrangler@4.60.0 >/dev/null 2>&1

echo "=== 3. write wrangler.toml ==="
cat > wrangler.toml <<'TOML'
name = "danmu-api"
main = "danmu_api/worker.js"
compatibility_date = "2025-09-13"
keep_vars = true
compatibility_flags = ["nodejs_compat"]
TOML
{
  printf '\n[vars]\n'
  printf 'TOKEN = "%s"\n' "$DANMAKU_TOKEN"
  printf 'SOURCE_ORDER = "douban,360,renren,hanjutv,dandan,tencent,youku,iqiyi,bilibili"\n'
  printf 'RATE_LIMIT_MAX_REQUESTS = "120"\n'
  printf 'LOG_LEVEL = "warn"\n'
} >> wrangler.toml
echo "--- wrangler.toml (token masked) ---"
sed -E 's/(TOKEN = ").*(")/\1***\2/' wrangler.toml

echo "=== 4. dry-run build ==="
wrangler deploy --dry-run --outdir=/tmp/out 2>&1 | tail -6

echo "=== 5. deploy ==="
wrangler deploy 2>&1 | tail -25

echo "=== 6. verify live ==="
BASE="https://danmu-api.tarysoli33.workers.dev"
for i in 1 2 3 4 5 6; do
  sleep 6
  CODE=$(curl -s -o /tmp/v.json -w '%{http_code}' --max-time 25 \
    "$BASE/${DANMAKU_TOKEN}/api/v2/search/anime?keyword=%E5%BA%86%E4%BD%99%E5%B9%B4" || echo 000)
  echo "attempt $i -> HTTP $CODE"
  if [ "$CODE" = "200" ]; then break; fi
done
echo "--- response ---"
head -c 700 /tmp/v.json
echo
python3 - <<'PY'
import json
try:
    d = json.load(open('/tmp/v.json'))
except Exception as e:
    print("parse failed:", e); raise SystemExit(0)
animes = d.get('animes') or []
print(f"\n>>> success={d.get('success')} errorCode={d.get('errorCode')} animes={len(animes)}")
for a in animes[:6]:
    print("   -", a.get('animeTitle'), "| type:", a.get('type'), "| id:", a.get('animeId'))
PY
