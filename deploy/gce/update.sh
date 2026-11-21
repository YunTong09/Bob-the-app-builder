#!/usr/bin/env bash
# Pull the checked-out branch, rebuild and restart the hosted services.
#
# `next build` empties .next before compiling, so a failed build would
# otherwise leave the running site without its JavaScript and CSS. Any failure
# below restores the previous commit and build, so the site keeps working.
set -euo pipefail
set -a
source "${R2R_ENV_FILE:-/etc/r2r/r2r.env}"
set +a
cd "$R2R_APP_DIR"

previous=$(git rev-parse HEAD)
rm -rf .next.previous
if [ -d .next ]; then cp -a .next .next.previous; fi

rollback() {
  trap - ERR
  echo "Update failed. Restoring ${previous:0:7} and the previous build; the site keeps running." >&2
  git reset -q --hard "$previous"
  backend/.venv/bin/pip install -q -r backend/requirements.txt || true
  npm ci --no-audit --no-fund >/dev/null 2>&1 || true
  if [ -d .next.previous ]; then
    rm -rf .next
    mv .next.previous .next
  fi
  sudo systemctl restart r2r-frontend || true
  exit 1
}
trap rollback ERR

git pull --ff-only
backend/.venv/bin/pip install -q -r backend/requirements.txt
# Catch Python syntax errors (such as committed conflict markers) before the
# backend is restarted.
backend/.venv/bin/python -m compileall -q -x '[.]venv' backend >/dev/null
npm ci --no-audit --no-fund

# NEXT_PUBLIC_* values are compiled into the browser bundle at build time.
NEXT_PUBLIC_R2R_MOCK=false \
NEXT_PUBLIC_API_BASE_URL="$R2R_PUBLIC_ORIGIN" \
NEXT_PUBLIC_R2R_AUTH=invite \
  npm run build

trap - ERR
rm -rf .next.previous
sudo systemctl restart r2r-backend r2r-frontend
sleep 5
systemctl is-active r2r-backend r2r-frontend
