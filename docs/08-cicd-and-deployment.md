# CI/CD, images, nginx, and production rollout

This is the runbook for: **push to GitHub → GitHub Actions builds images → server pulls images → nginx maps domains → you test production.**

```text
Developer
   │  git push origin main
   ▼
GitHub Actions
   ├── CI: pytest + flutter test
   └── Build: Docker images → GHCR
              ghcr.io/<you>/fieldopsai/api:<sha>
              ghcr.io/<you>/fieldopsai/web:<sha>
   │
   │  (when ENABLE_DEPLOY=true)
   ▼
Your VPS
   ├── git checkout that commit
   ├── docker login ghcr.io
   ├── docker compose -f docker-compose.prod.yml pull
   └── docker compose up -d
              │
              ▼
         nginx :80/:443
              ├── app.example.com      → Flutter web
              ├── api.example.com      → FastAPI
              └── grafana.example.com  → Grafana
```

Nothing in this flow copies `.env` from GitHub. **Secrets live only on the server.**

---

## 1. Put the repo on GitHub

```powershell
cd B:\Projects\fieldOpsAi
git init
git add .
git commit -m "Initial FieldOps AI platform"
gh repo create fieldOpsAi --private --source=. --remote=origin --push
```

Or create the empty repo in the GitHub UI, then:

```powershell
git remote add origin https://github.com/YOUR_USER/fieldOpsAi.git
git branch -M main
git push -u origin main
```

---

## 2. GitHub settings (do this once)

### Packages

After the first successful **Build and push images** run, open:

`GitHub → your repo → Packages`

Open `api` and `web`. If the repo is private, either:

- set each package visibility to **Public**, or
- leave them private (the deploy job logs into GHCR with `GITHUB_TOKEN`)

### Variables (Settings → Secrets and variables → Actions → Variables)

| Variable | Example | When |
|----------|---------|------|
| `PRODUCTION_API_URL` | `https://api.yourdomain.com` | Before building the web image for real users |
| `ENABLE_DEPLOY` | `true` | Only after the VPS exists |
| `DOMAIN_API` | `api.yourdomain.com` | Optional smoke test after deploy |
| `DOMAIN_APP` | `app.yourdomain.com` | Optional smoke test after deploy |

Until `ENABLE_DEPLOY=true`, pushes only **test + publish images**. That is what you want before the server exists.

### Environment `production` (Settings → Environments → New)

Create an environment named **`production`**. Put deploy secrets there:

| Secret | Meaning |
|--------|---------|
| `DEPLOY_HOST` | VPS public IP or hostname |
| `DEPLOY_USER` | SSH user (`root` or a sudo user in the docker group) |
| `DEPLOY_SSH_KEY` | **Private** key whose public half is in the server `~/.ssh/authorized_keys` |
| `DEPLOY_PATH` | `/opt/fieldops` |

Generate a deploy key on your PC (do not reuse your daily GitHub key if you can avoid it):

```powershell
ssh-keygen -t ed25519 -f fieldops-deploy -N ""
```

Put `fieldops-deploy.pub` on the server. Paste the **private** `fieldops-deploy` file into `DEPLOY_SSH_KEY`.

---

## 3. First-time server (Ubuntu)

SSH in as root, then:

```bash
export REPO_URL="git@github.com:YOUR_USER/fieldOpsAi.git"   # or HTTPS
curl -fsSL https://raw.githubusercontent.com/YOUR_USER/fieldOpsAi/main/scripts/server-bootstrap.sh | bash
# or, after a manual clone:
#   bash /opt/fieldops/scripts/server-bootstrap.sh
```

The script installs Docker Engine + Compose plugin, opens **22 / 80 / 443**, clones the repo to `/opt/fieldops`, and copies `deploy/env.production.example` to `/opt/fieldops/.env`.

Edit that file **before** the first compose up:

```bash
nano /opt/fieldops/.env
```

You must set:

- `GHCR_IMAGE_PREFIX=ghcr.io/your-user/fieldopsai` (all lowercase)
- `DOMAIN_APP` / `DOMAIN_API` / `DOMAIN_GRAFANA`
- `SECRET_KEY`, `POSTGRES_PASSWORD`, `GF_SECURITY_ADMIN_PASSWORD`
- `CORS_ORIGINS=https://app.yourdomain.com`
- `SEED_DEMO_DATA=false` in a real customer install (`true` is fine for your own production rehearsal)

Give the deploy user permission to talk to Docker:

```bash
usermod -aG docker "$DEPLOY_USER"
```

If the GitHub repo is private, add a **read-only deploy key** to the repo so `git fetch` on the server works.

---

## 4. DNS — do this when the domains have arrived

At your registrar, create **A records** (not CNAME to a random host) pointing at the VPS IPv4:

| Host | Type | Value |
|------|------|-------|
| `app` | A | `YOUR.SERVER.IP` |
| `api` | A | `YOUR.SERVER.IP` |
| `grafana` | A | `YOUR.SERVER.IP` |

Wait until they resolve:

```bash
dig +short app.yourdomain.com
dig +short api.yourdomain.com
```

Set GitHub variable `PRODUCTION_API_URL=https://api.yourdomain.com`, then rebuild images (push or **Run workflow**) so the Flutter web build bakes in that API URL.

---

## 5. First production bring-up (HTTP)

On the server:

```bash
cd /opt/fieldops
bash scripts/render-nginx.sh
docker compose --env-file .env -f docker-compose.prod.yml pull
docker compose --env-file .env -f docker-compose.prod.yml up -d
docker compose --env-file .env -f docker-compose.prod.yml ps
```

Or push to `main` with `ENABLE_DEPLOY=true` and let Actions SSH in.

**HTTP test (before certificates):**

```bash
curl -i http://api.yourdomain.com/health
curl -i http://app.yourdomain.com/healthz
curl -i http://api.yourdomain.com/docs
```

In the browser:

1. Open `http://app.yourdomain.com`
2. Confirm the API URL on the login screen is `https://api.yourdomain.com` (or HTTP until TLS exists)
3. Sign in with a real user (not demo, if you turned seed off)
4. Walk T-104 if seed is still on

---

## 6. TLS with nginx + Let's Encrypt

HTTP must already answer on port 80 (step 5). Then:

```bash
cd /opt/fieldops
bash scripts/issue-certs.sh
```

That issues **one** certificate with three names (app, api, grafana), re-renders nginx for HTTPS, and reloads the proxy.

Renewal (cron, twice a day is the certbot default; once a week is enough):

```bash
crontab -e
# 04:17 every day
17 4 * * * cd /opt/fieldops && bash scripts/issue-certs.sh >> /var/log/fieldops-certbot.log 2>&1
```

**HTTPS test:**

```bash
curl -i https://api.yourdomain.com/health
curl -i https://app.yourdomain.com/healthz
```

You should see `301` from HTTP to HTTPS after the HTTPS config is active.

---

## 7. What GitHub Actions actually does

| Workflow | File | Trigger | Result |
|----------|------|---------|--------|
| CI | `.github/workflows/ci.yml` | Pull requests | pytest + Flutter analyze/test |
| Images | `.github/workflows/images.yml` | Push to `main` / tags / manual | Tests, then push `api` + `web` to GHCR |
| Deploy | same file, `deploy` job | Only if `ENABLE_DEPLOY=true` | SSH → pull images → compose up → optional curl smoke |

Images are tagged with the **git SHA (12 chars)** and `latest`.

---

## 8. Production test checklist

After DNS + TLS:

- [ ] `https://api.yourdomain.com/health` → `{"status":"ok",...}`
- [ ] `https://api.yourdomain.com/ready` → database is up
- [ ] `https://api.yourdomain.com/docs` → OpenAPI (disable later if you do not want it public)
- [ ] `https://app.yourdomain.com` loads the Flutter UI
- [ ] Login works against the production API (not `localhost`)
- [ ] Map tiles load (outbound HTTPS from the browser to OSM)
- [ ] Submit T-104 (or a real asset) → risk + AI insight
- [ ] `https://grafana.yourdomain.com` with the password from `.env`
- [ ] `docker compose -f docker-compose.prod.yml logs -f api` shows no secret leakage
- [ ] `SEED_DEMO_DATA=false` and demo passwords rotated for a real customer
- [ ] Firewall: only 22, 80, 443. Postgres is **not** published

---

## 9. Typical failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| Web talks to `api.example.com` | `PRODUCTION_API_URL` was empty at image build | Set the variable, push again, deploy the new `web` tag |
| `401` pulling from GHCR | Private package, no login | Deploy job already logs in; manually: `echo $TOKEN \| docker login ghcr.io` |
| nginx 503 placeholder | Config not rendered | `bash scripts/render-nginx.sh` then `compose up -d proxy` |
| Certbot fails | DNS not pointing here, or port 80 blocked | Fix A records, `ufw allow 80` |
| CORS error in the browser | `CORS_ORIGINS` missing the app origin | Set `https://app.yourdomain.com` (no trailing slash) |
| Deploy skipped | `ENABLE_DEPLOY` not `true` | Add the repository variable |
| Deploy job waits forever | Environment `production` has required reviewers | Approve it, or remove protection while rehearsing |

---

## 10. Manual deploy (no Actions)

```bash
cd /opt/fieldops
git fetch origin && git reset --hard origin/main
export GHCR_TOKEN=ghp_...          # if packages are private
bash scripts/server-deploy.sh
```

---

## 11. Local rehearsal of the production compose file

On your PC this is optional and still needs Docker. It will **not** get public certificates.

```powershell
copy deploy\env.production.example .env
# set GHCR_IMAGE_PREFIX after the first Actions build, or let Compose build locally:
docker compose -f docker-compose.prod.yml build
bash scripts/render-nginx.sh   # Git Bash / WSL
docker compose -f docker-compose.prod.yml up -d
```

Use `docker-compose.yml` (not prod) for day-to-day laptop demos.
