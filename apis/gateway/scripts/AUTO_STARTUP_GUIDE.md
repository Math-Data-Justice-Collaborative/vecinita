# VECINA Auto-Startup Guide for Google VM

Your VECINITA project is configured with multiple auto-startup mechanisms. Here's the complete guide:

## Quick Start

**Option 1: Systemd (Recommended for Google VM)**

```bash
sudo /path/to/scripts/startup.sh --install-systemd
sudo systemctl start vecinita-docker.service  # Test it
sudo journalctl -u vecinita-docker.service -f # View logs
```

**Option 2: Cron (@reboot)**

```bash
sudo /path/to/scripts/startup.sh --install-cron
tail -f /tmp/vecinita-startup.log  # View logs
```

**Option 3: Google Cloud Startup Script (Via VM Metadata)**

```bash
# In Google Cloud Console or gcloud CLI:
gcloud compute instances add-metadata INSTANCE_NAME \
  --metadata startup-script='#!/bin/bash
cd /path/to/vecinita
docker-compose up -d'
```

---

## How It Works: Three Layers of Resilience

### 1. **Docker Restart Policy** (Already Active ✓)

```yaml
# docker-compose.yml
restart: unless-stopped
```

- **Restarts containers** if they crash (even mid-boot)
- **Survives** `docker daemon` restarts
- **Doesn't restart** if you explicitly stop containers
- ✓ **Already configured** — no action needed

### 2. **Systemd Service** (Recommended for Google VM)

- Starts `docker-compose` on **OS boot**
- Ensures Docker is running before starting containers
- Provides journaling and monitoring
- Can retry on failure

### 3. **Cron @reboot Job** (Simple Alternative)

- Lightweight method using cron
- Runs after system startup
- Logs to `/tmp/vecinita-startup.log`

---

## Installation Method Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Docker Restart Policy** | Already active, zero setup | Doesn't restart on OS boot | Crash recovery |
| **Systemd** | Professional, robust logging, monitoring | Requires sudo | Production Google VMs |
| **Cron @reboot** | Simple, minimal overhead | Less reliable than systemd | Quick testing |
| **Google Cloud Metadata** | Native GCP integration, automatic | One-time setup per instance | Managed VMs |

---

## Recommended Setup for Google VM

### Step 1: Add Systemd Service

```bash
sudo /path/to/scripts/startup.sh --install-systemd
```

### Step 2: Verify Installation

```bash
# Check service is enabled
sudo systemctl status vecinita-docker.service

# Check if it would start on boot
sudo systemctl is-enabled vecinita-docker.service  # Should output: enabled
```

### Step 3: Test Startup Sequence

```bash
# Stop running services
docker-compose down

# Manually trigger startup
sudo systemctl start vecinita-docker.service

# Watch it start
sudo journalctl -u vecinita-docker.service -f
```

### Step 4: Monitor Logs

```bash
# View recent startup logs
sudo journalctl -u vecinita-docker.service --since "10 minutes ago"

# Follow in real-time
sudo journalctl -u vecinita-docker.service -f

# Filter by severity
sudo journalctl -u vecinita-docker.service -p err
```

---

## Troubleshooting

### Check what's running

```bash
docker-compose ps
docker ps

# Check port
lsof -i :8000
```

### View application logs

```bash
# Docker logs
docker-compose logs -f vecinita-app

# Systemd startup logs
sudo journalctl -u vecinita-docker.service -n 50 --no-pager

# Startup script logs
tail -50 /var/log/vecinita-startup.log  # or /tmp/vecinita-startup.log
```

### Service won't start?

```bash
# Check service status
sudo systemctl status vecinita-docker.service

# Check for recent errors
sudo journalctl -u vecinita-docker.service | grep -i error

# Manually test startup script
./scripts/startup.sh --start
```

### Docker daemon issues

```bash
# Restart Docker
sudo systemctl restart docker

# Check Docker status
sudo systemctl status docker
docker ps  # Should work if Docker is healthy
```

---

## Google Cloud Specific Tips

### Using Startup Scripts Metadata (Alternative to Systemd)

```bash
# Create a startup script in Cloud Storage
echo '#!/bin/bash
cd /path/to/vecinita
docker-compose up -d' > /tmp/startup.sh

# Add to VM instance metadata
gcloud compute instances add-metadata INSTANCE_NAME \
  --zone=YOUR_ZONE \
  --metadata-from-file startup-script=/tmp/startup.sh

# Or via console:
# VM instances > [Your Instance] > Edit > Custom metadata
# Key: startup-script
# Value: [your startup script]
```

### Pre-create Startup Script in Cloud Storage

```bash
gsutil cp /tmp/startup.sh gs://your-bucket/vecinita-startup.sh

gcloud compute instances add-metadata INSTANCE_NAME \
  --zone=YOUR_ZONE \
  --metadata startup-script-url=gs://your-bucket/vecinita-startup.sh
```

### Verify Startup Script Ran

```bash
# On VM instance
sudo journalctl -u google-startup-scripts.service
tail -50 /var/log/syslog | grep -i startup
```

---

## Production Recommendations

1. **Use Systemd** (or Google Cloud startup scripts if inside GCP)
2. **Keep Docker restart policy** = `unless-stopped` (already set)
3. **Enable healthchecks** on all services (already configured)
4. **Monitor logs** via systemd journal or Cloud Logging
5. **Test startup** by rebooting VM: `sudo reboot`

---

## Files Reference

- **Startup script**: `scripts/startup.sh`
- **Docker compose**: `docker-compose.yml` (has restart policies)
- **Logs** (Systemd): `sudo journalctl -u vecinita-docker.service`
- **Logs** (Cron): `/tmp/vecinita-startup.log`

---

## Quick Checklist

- [ ] Run `sudo scripts/startup.sh --install-systemd`
- [ ] Verify: `sudo systemctl status vecinita-docker.service`
- [ ] Test by rebooting VM: `sudo reboot`
- [ ] Confirm services running: `docker-compose ps`
- [ ] Check logs: `sudo journalctl -u vecinita-docker.service -f`
