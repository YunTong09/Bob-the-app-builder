#!/usr/bin/env bash
# Pull the checked-out branch, rebuild and restart the hosted services.
set -euo pipefail
set -a
source /etc/r2r/r2r.env
set +a
cd "$R2R_APP_DIR"

git pull --ff-only
backend/.venv/bin/pip install -q -r backend/requirements.txt
npm ci --no-audit --no-fund

# NEXT_PUBLIC_* values are compiled into the browser bundle at build time.
NEXT_PUBLIC_R2R_MOCK=false \
NEXT_PUBLIC_API_BASE_URL="$R2R_PUBLIC_ORIGIN" \
NEXT_PUBLIC_R2R_AUTH=invite \
  npm run build

sudo systemctl restart r2r-backend r2r-frontend
sleep 5
systemctl is-active r2r-backend r2r-frontend
