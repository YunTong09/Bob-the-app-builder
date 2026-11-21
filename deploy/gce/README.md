# Hosted demo on a Compute Engine VM

This guide puts the Web App on one Ubuntu 24.04 VM at an HTTPS domain for invited users, such as hackathon organisers and judges. Each invited person signs in with a personal invite code, and each code has separate history. The session behaviour is defined in [API_CONTRACT.md](../../docs/API_CONTRACT.md#identity-and-ownership). The component layout is in [ARCHITECTURE.md](../../docs/ARCHITECTURE.md#8-web-deployment-and-integration-milestones).

```text
browser ──HTTPS──> Caddy :443 ──/api/*──> FastAPI 127.0.0.1:8000 (invite_code mode)
                              └─other──> Next.js 127.0.0.1:3000
```

The Claude key, the invite list and the session-signing secret are stored in Secret Manager. They are loaded into the backend process at start-up and are never written to the repository, the VM disk or the browser bundle.

## Prerequisites

- A VM with Python, Node.js and this repository installed, plus a service account that can read the project's secrets (`roles/secretmanager.secretAccessor`).
- A domain, for example one registered with Porkbun.
- The Secret Manager secret `anthropic-api-key`.
- A monthly spend limit set in the Claude Console.

Run the `gcloud` commands from Cloud Shell. Run the remaining commands on the VM, in the repository directory.

## 1. Static IP, firewall and DNS

```bash
REGION=australia-southeast1; ZONE=australia-southeast1-b
# Reserve the VM's current external IP so it survives restarts.
IP=$(gcloud compute instances describe r2r-vm --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
gcloud compute addresses create r2r-ip --addresses=$IP --region=$REGION
gcloud compute firewall-rules create r2r-allow-web --allow=tcp:80,tcp:443 --target-tags=r2r-web
gcloud compute instances add-tags r2r-vm --zone=$ZONE --tags=r2r-web
echo $IP
```

In Porkbun, open **Domain Management → DNS** for the domain. Delete any default `ALIAS`, `CNAME` or `A` records for the root host. Then add an **A** record with an empty host and the IP as the answer. Ports 3000 and 8000 stay closed; only Caddy is public.

## 2. Secrets for invites and sessions

The VM's service account can only read secrets. Create and update them from Cloud Shell.

Create the session-signing secret once (Cloud Shell):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48), end='')" | \
  gcloud secrets create r2r-session-secret --replication-policy=automatic --data-file=-
```

Create one invite per person (VM, in the repository directory). Share each code privately:

```bash
backend/.venv/bin/python -m backend.api.invite_auth organizer
backend/.venv/bin/python -m backend.api.invite_auth judge-1
```

Each command prints a code (`R2R-XXXX-XXXX-XXXX-XXXX`) and an `R2R_INVITES entry` line. When `R2R_PUBLIC_ORIGIN` is set, the command also prints a personal sign-in link, `https://<your domain>/login#<code>`, which signs the person in without typing. You can also build the link yourself from an existing code. Treat each link like a password: anyone with it can use that person's workspace. The entry lines contain only hashes. Copy them into a file in Cloud Shell, store the file as a secret and delete it:

```bash
nano invites.txt          # paste one "label:hash" line per person
gcloud secrets create r2r-invites --replication-policy=automatic --data-file=invites.txt
rm invites.txt
```

Grant the VM's service account access to both new secrets (Cloud Shell):

```bash
for s in r2r-invites r2r-session-secret; do
  gcloud secrets add-iam-policy-binding $s \
    --member="serviceAccount:r2r-vm-sa@$(gcloud config get-value project).iam.gserviceaccount.com" \
    --role=roles/secretmanager.secretAccessor
done
```

To add or revoke an invite later, add a new version of `r2r-invites` with the full updated list from Cloud Shell (`gcloud secrets versions add r2r-invites --data-file=invites.txt`). Then run `sudo systemctl restart r2r-backend` on the VM. A removed or regenerated code signs out that person's existing sessions.

## 3. Configuration, Caddy and services

```bash
sudo mkdir -p /etc/r2r
sudo cp deploy/gce/r2r.env.example /etc/r2r/r2r.env
sudo nano /etc/r2r/r2r.env   # set R2R_APP_DIR and R2R_PUBLIC_ORIGIN=https://<your domain>

sudo apt install -y caddy
sudo cp deploy/gce/Caddyfile /etc/caddy/Caddyfile
sudo sed -i "s/example.com/<your domain>/" /etc/caddy/Caddyfile
sudo systemctl reload caddy

for unit in r2r-backend r2r-frontend; do
  sed "s|__USER__|$USER|g; s|__APP_DIR__|$PWD|g" deploy/gce/$unit.service | sudo tee /etc/systemd/system/$unit.service >/dev/null
done
sudo systemctl daemon-reload
sudo systemctl enable r2r-backend r2r-frontend
bash deploy/gce/update.sh   # installs dependencies, builds with the hosted settings and restarts
```

Do not keep a `backend/.env` containing `R2R_WEB_ORIGIN` on the VM: invite mode refuses to start with the local-only setting.

## 4. Verify

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<your domain>/api/session   # 401 before sign-in
curl -sI https://<your domain>/ | head -3                                      # 307 redirect to /login
```

Then open the domain from a phone or a computer that is not on the team's network. Sign in with an invite code, generate a reply, and import, search and delete history. Then sign in with a second code and confirm that the first person's history is not visible.

## Operations

- **Update:** `bash deploy/gce/update.sh` pulls the checked-out branch, rebuilds and restarts. Python syntax is checked before the backend restarts. If the pull, the checks or the build fail, the script restores the previous commit and build and exits with an error, and the site keeps running the previous version. Fix the problem on `main`, then run the script again.
- **Roll back manually:** `git checkout <good commit>`, then build and restart with the commands in `update.sh` (skip `git pull`). Return with `git checkout main` before the next update.
- **Logs:** `journalctl -u r2r-backend -n 50 --no-pager` (also `r2r-frontend` and `caddy`). The logs contain no codes, cookies or drafts.
- **Cost controls:** each invite can generate at most `R2R_GENERATE_LIMIT_PER_HOUR` replies (default 30). An address is locked out after `R2R_LOGIN_FAILURES_PER_15_MIN` failed sign-ins. The Claude Console spend limit caps the total.
- **Slack preview:** leave `SLACK_BOT_TOKEN` unset on the hosted VM. The preview is a local-demo extension. With a token set, every signed-in invite could read the allowlisted channel, because the server checks the session but not the person's Slack access. Hosted import awaits the Slack account binding in [SLACK-03](../../docs/progress/slack-integration-tracker.md#slack-03--website-import-by-channel-id). Test it locally with the [README steps](../../README.md#preview-and-import-a-slack-test-channel).
