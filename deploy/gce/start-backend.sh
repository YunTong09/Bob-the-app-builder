#!/usr/bin/env bash
# Hosted FastAPI backend (invite-code mode). Run by r2r-backend.service.
# Secrets are read from Secret Manager at start-up and exist only in this
# process's environment; nothing is written to disk.
set -euo pipefail
export PATH="$PATH:/snap/bin"
cd "${R2R_APP_DIR:?Set R2R_APP_DIR in /etc/r2r/r2r.env}"

secret() { gcloud secrets versions access latest --secret="$1"; }

export ANTHROPIC_API_KEY="$(secret anthropic-api-key)"
export R2R_INVITES="$(secret r2r-invites)"
export R2R_SESSION_SECRET="$(secret r2r-session-secret)"
export R2R_IDENTITY_MODE=invite_code

# --proxy-headers lets sign-in throttling see the visitor's address from Caddy.
exec backend/.venv/bin/python -m uvicorn backend.api.main:app \
  --host 127.0.0.1 --port 8000 \
  --proxy-headers --forwarded-allow-ips 127.0.0.1
