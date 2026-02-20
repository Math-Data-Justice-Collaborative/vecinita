#!/usr/bin/env bash
# deploy/gcp/firewall-rules.sh
# ─────────────────────────────────────────────────────────────────────────────
# Set up GCP firewall rules and create the Compute Engine VM.
#
# Usage:
#   export PROJECT_ID=your-gcp-project
#   export ZONE=us-central1-a
#   bash deploy/gcp/firewall-rules.sh
#
# For GPU support, use MACHINE_TYPE=n1-standard-8 and uncomment the
# --accelerator flag.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID}"
ZONE="${ZONE:-us-central1-a}"
VM_NAME="${VM_NAME:-vecinita-vm}"
MACHINE_TYPE="${MACHINE_TYPE:-n2-standard-4}"   # 4 vCPU, 16 GB — CPU-only Ollama
# GPU option: n1-standard-8 + --accelerator=type=nvidia-tesla-t4,count=1

echo "==> Setting default project: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# ── Firewall rules ─────────────────────────────────────────────────────────

echo "==> Creating firewall rules…"

# Allow HTTP (80) and HTTPS (443) from everywhere
gcloud compute firewall-rules create vecinita-allow-http \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:80,tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=vecinita-server \
  2>/dev/null || echo "   (firewall rule already exists)"

# Allow SSH
gcloud compute firewall-rules create vecinita-allow-ssh \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=vecinita-server \
  2>/dev/null || echo "   (ssh rule already exists)"

# ── Create VM ─────────────────────────────────────────────────────────────

echo "==> Creating VM: $VM_NAME ($MACHINE_TYPE) in $ZONE…"
gcloud compute instances create "$VM_NAME" \
  --zone="$ZONE" \
  --machine-type="$MACHINE_TYPE" \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-balanced \
  --tags=vecinita-server \
  --metadata=startup-script='#!/bin/bash
    echo "Startup script ran at $(date)" >> /var/log/vecinita-startup.log' \
  2>/dev/null || echo "   (VM may already exist)"

# Wait for the VM to be ready
echo "==> Waiting for VM to become accessible…"
sleep 10

EXTERNAL_IP=$(gcloud compute instances describe "$VM_NAME" \
  --zone="$ZONE" \
  --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo "==> VM ready!"
echo "    External IP: $EXTERNAL_IP"
echo "    SSH:  gcloud compute ssh $VM_NAME --zone=$ZONE"
echo ""
echo "    Next steps:"
echo "    1. gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "    2. Run instance-setup.sh on the VM"
echo "    3. Edit /opt/vecinita/backend/.env with your credentials"
echo "    4. bash deploy/gcp/cloudrun-embed.sh  (from your local machine)"
