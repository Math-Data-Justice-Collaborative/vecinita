# GCP Deployment Guide

This directory contains everything needed to deploy Vecinita on Google Cloud Platform.

## Architecture

```
Internet
    │
    ▼
[Cloud DNS / External IP]
    │
    ▼
[Nginx: port 80/443]  ──── serves ──── /opt/vecinita/frontend/dist  (React SPA)
    │
    ▼ /api/  and  /ask  /health  etc.
[vecinita-agent container :8000]  (FastAPI + LangGraph)
    │                 │
    ▼                 ▼
[Ollama :11434]   [ChromaDB container]
 (systemd)
    │                 │
    ▼                 ▼
[llama3.1:8b]   [Supabase + Cloud Run: vecinita-embed]
                 (all-MiniLM-L6-v2, scales to zero)
```

## Files

| File | Purpose |
|------|---------|
| `firewall-rules.sh` | Create GCP VM + firewall rules |
| `instance-setup.sh` | Bootstrap VM (Docker, Ollama, Nginx, repo clone) |
| `docker-compose.prod.yml` | Production container config for the agent |
| `nginx.conf` | Nginx virtual host (HTTP → HTTPS, SSE support) |
| `nginx-locations.conf` | Shared location blocks (included by nginx.conf) |
| `cloudrun-embed.sh` | Deploy embedding service to Cloud Run |
| `cloudbuild.yaml` | Cloud Build CI/CD pipeline |

## Quick Start

### 1. Create the VM

```bash
export PROJECT_ID=your-gcp-project
export ZONE=us-central1-a
bash deploy/gcp/firewall-rules.sh
```

### 2. Bootstrap the VM

```bash
gcloud compute ssh vecinita-vm --zone=us-central1-a
# On the VM:
export REPO_URL=https://github.com/YOUR_ORG/vecinita.git
export OLLAMA_MODEL=llama3.1:8b
curl -sSL https://raw.githubusercontent.com/YOUR_ORG/vecinita/main/deploy/gcp/instance-setup.sh | bash
```

### 3. Fill in secrets

```bash
nano /opt/vecinita/backend/.env
```

Ensure these Chroma settings exist in `.env` (or are injected by compose):

```bash
CHROMA_HOST=chroma
CHROMA_PORT=8000
CHROMA_SSL=false
CHROMA_COLLECTION_CHUNKS=vecinita_chunks
CHROMA_COLLECTION_SOURCES=vecinita_sources
CHROMA_COLLECTION_QUEUE=vecinita_queue
```

### 4. Deploy embedding service (from local machine)

```bash
export PROJECT_ID=your-gcp-project
export REGION=us-central1
bash deploy/gcp/cloudrun-embed.sh
# Copy the Service URL output to EMBEDDING_SERVICE_URL in .env
```

### 5. Restart the agent

```bash
# On the VM:
sudo systemctl restart vecinita
```

### 6. (Optional) Enable TLS

```bash
# On the VM — replace with your domain:
export DOMAIN=chat.yoursite.com
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@yoursite.com
```

## CI/CD (Cloud Build)

Connect the repo in the [Cloud Build triggers console](https://console.cloud.google.com/cloud-build/triggers) and point it to `deploy/gcp/cloudbuild.yaml`.

**Required substitution variables** (set in the trigger):
- `_VM_NAME` — VM name (default: `vecinita-vm`)
- `_ZONE` — GCP zone (default: `us-central1-a`)
- `_REGION` — Cloud Run region (default: `us-central1`)
- `_EMBED_SERVICE` — Cloud Run service name (default: `vecinita-embed`)

## Machine Type Recommendations

| Use case | Machine type | Cost (~) |
|----------|-------------|----------|
| CPU-only (llama3.1:8b ~10 t/s) | `n2-standard-4` (4 vCPU, 16 GB) | ~$100/mo |
| Faster CPU (llama3.1:8b ~25 t/s) | `c2-standard-8` (8 vCPU, 32 GB) | ~$200/mo |
| GPU T4 (llama3.1:8b ~60 t/s) | `n1-standard-8` + T4 | ~$250/mo |

To use a GPU, add `--accelerator=type=nvidia-tesla-t4,count=1 --maintenance-policy=TERMINATE` when creating the VM, and install the NVIDIA drivers before running `instance-setup.sh`.

## Setting Admin Role in Supabase

```sql
UPDATE auth.users
SET raw_app_meta_data = jsonb_set(
  COALESCE(raw_app_meta_data, '{}'),
  '{role}',
  '"admin"'
)
WHERE email = 'your-admin@example.com';
```
