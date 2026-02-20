#!/usr/bin/env bash
# deploy/gcp/instance-setup.sh
# ─────────────────────────────────────────────────────────────────────────────
# Bootstrap a GCP Compute Engine VM to run:
#   • Ollama  (LLM host, CPU or GPU)
#   • Vecinita agent  (FastAPI, port 8000)
#   • Nginx reverse proxy (HTTPS on port 443, HTTP redirect on 80)
#
# Usage:
#   1. Create VM in GCP Console or with gcloud (see firewall-rules.sh)
#   2. SSH into the VM: gcloud compute ssh vecinita-vm --zone=us-central1-a
#   3. Run:  curl -sSL https://raw.githubusercontent.com/YOUR_ORG/vecinita/main/deploy/gcp/instance-setup.sh | bash
#
# Requirements: Debian / Ubuntu 22.04 LTS,  ≥ 4 vCPUs, ≥ 16 GB RAM
# For GPU: add  --accelerator type=nvidia-tesla-t4,count=1  when creating VM
#           and run  scripts/install-nvidia.sh  before this script.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.1:8b}"
DOMAIN="${DOMAIN:-}"          # Set to your domain to enable Let's Encrypt TLS
REPO_URL="${REPO_URL:-https://github.com/YOUR_ORG/vecinita.git}"
APP_DIR="/opt/vecinita"
NGINX_CONF_SRC="$APP_DIR/deploy/gcp/nginx.conf"

# ── System packages ────────────────────────────────────────────────────────────
echo "==> Updating system packages…"
sudo apt-get update -y
sudo apt-get install -y \
  git curl wget ca-certificates gnupg lsb-release \
  nginx certbot python3-certbot-nginx \
  python3 python3-pip

# ── Docker ────────────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "==> Installing Docker…"
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
fi

if ! command -v docker-compose &>/dev/null; then
  echo "==> Installing Docker Compose v2…"
  sudo apt-get install -y docker-compose-plugin
  # Compatibility shim
  sudo ln -sf /usr/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
fi

# ── Ollama ────────────────────────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
  echo "==> Installing Ollama…"
  curl -fsSL https://ollama.com/install.sh | sh
fi

sudo systemctl enable ollama
sudo systemctl start ollama

# Wait for Ollama to be ready
echo "==> Waiting for Ollama to start…"
for i in $(seq 1 30); do
  if curl -sf http://localhost:11434/api/version &>/dev/null; then
    echo "   Ollama is up."
    break
  fi
  sleep 2
done

# Pull the LLM model
echo "==> Pulling model: $OLLAMA_MODEL"
ollama pull "$OLLAMA_MODEL"

# ── Clone / update repo ───────────────────────────────────────────────────────
if [[ -d "$APP_DIR/.git" ]]; then
  echo "==> Updating repo at $APP_DIR…"
  git -C "$APP_DIR" pull
else
  echo "==> Cloning repo to $APP_DIR…"
  sudo git clone "$REPO_URL" "$APP_DIR"
  sudo chown -R "$USER:$USER" "$APP_DIR"
fi

# ── Environment file ──────────────────────────────────────────────────────────
if [[ ! -f "$APP_DIR/backend/.env" ]]; then
  echo "==> Creating placeholder .env — FILL IN YOUR SECRETS!"
  cat > "$APP_DIR/backend/.env" <<'EOF'
# Supabase
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY

# LLM providers (Ollama is primary, others are fallbacks)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

DEEPSEEK_API_KEY=
OPENAI_API_KEY=

# Embedding service (Cloud Run URL — set after cloudrun-embed.sh)
EMBEDDING_SERVICE_URL=https://YOUR_EMBED_SERVICE.run.app

# Guardrails
GUARDRAILS_ENABLED=true

# Optional: LangSmith tracing
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
EOF
  echo "   !!! Edit $APP_DIR/backend/.env with real credentials before starting. !!!"
fi

# ── Nginx ─────────────────────────────────────────────────────────────────────
echo "==> Configuring Nginx…"
sudo cp "$NGINX_CONF_SRC" /etc/nginx/sites-available/vecinita
sudo ln -sf /etc/nginx/sites-available/vecinita /etc/nginx/sites-enabled/vecinita
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Optional: TLS with Let's Encrypt
if [[ -n "$DOMAIN" ]]; then
  echo "==> Requesting Let's Encrypt certificate for $DOMAIN…"
  sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "admin@$DOMAIN"
fi

# ── Start containers ──────────────────────────────────────────────────────────
echo "==> Starting Vecinita agent container…"
cd "$APP_DIR"
docker-compose -f deploy/gcp/docker-compose.prod.yml up -d --build

# ── Systemd unit for auto-restart ─────────────────────────────────────────────
sudo tee /etc/systemd/system/vecinita.service > /dev/null <<EOF
[Unit]
Description=Vecinita Agent (docker-compose)
After=docker.service network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose -f deploy/gcp/docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f deploy/gcp/docker-compose.prod.yml down

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vecinita

echo ""
echo "==> Setup complete!"
echo "    Agent:  http://localhost:8000 (internal)"
echo "    Nginx:  http://$(curl -sf http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H 'Metadata-Flavor: Google' 2>/dev/null || echo '<EXTERNAL-IP>')"
echo ""
echo "    Next step: edit $APP_DIR/backend/.env with real credentials, then:"
echo "    sudo systemctl restart vecinita"
