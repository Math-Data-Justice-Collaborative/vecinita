#!/bin/bash
set -e

# Vecinita Single VM Deployment Script for GCP
# Deploys all services to one Compute Engine VM with Docker Compose

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${1:-}"
ZONE="${2:-us-east1-b}"
VM_NAME="vecinita-vm"
MACHINE_TYPE="e2-standard-2"  # 2 vCPU, 8GB RAM - good for all services

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: PROJECT_ID is required${NC}"
    echo "Usage: ./deploy_to_vm.sh PROJECT_ID [ZONE]"
    echo "Example: ./deploy_to_vm.sh my-project us-east1-b"
    exit 1
fi

echo -e "${GREEN}Starting Vecinita VM Deployment${NC}"
echo "Project: $PROJECT_ID"
echo "Zone: $ZONE"
echo "VM Name: $VM_NAME"
echo "Machine Type: $MACHINE_TYPE (2 vCPU, 8GB RAM)"
echo ""

# Set project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo -e "${YELLOW}Enabling Compute Engine API...${NC}"
gcloud services enable compute.googleapis.com

# Check if VM already exists
if gcloud compute instances describe "$VM_NAME" --zone="$ZONE" &>/dev/null; then
    echo -e "${YELLOW}VM $VM_NAME already exists. Do you want to recreate it? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deleting existing VM...${NC}"
        gcloud compute instances delete "$VM_NAME" --zone="$ZONE" --quiet
    else
        echo -e "${GREEN}Using existing VM${NC}"
        VM_EXISTS=true
    fi
fi

# Create VM if it doesn't exist
if [ -z "$VM_EXISTS" ]; then
    echo -e "${YELLOW}Creating VM instance...${NC}"
    gcloud compute instances create "$VM_NAME" \
        --zone="$ZONE" \
        --machine-type="$MACHINE_TYPE" \
        --image-family=ubuntu-2204-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=50GB \
        --boot-disk-type=pd-standard \
        --tags=http-server,https-server \
        --metadata=startup-script='#!/bin/bash
# Install Docker
apt-get update
apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker
systemctl enable docker
systemctl start docker

# Create vecinita user
useradd -m -s /bin/bash vecinita || true
usermod -aG docker vecinita
'

    echo -e "${GREEN}VM created successfully!${NC}"
    echo -e "${YELLOW}Waiting 60 seconds for startup script to complete...${NC}"
    sleep 60
fi

# Create firewall rules for HTTP/HTTPS
echo -e "${YELLOW}Setting up firewall rules...${NC}"
gcloud compute firewall-rules create allow-http-vecinita --allow tcp:80,tcp:8000,tcp:3000 --target-tags http-server --source-ranges 0.0.0.0/0 2>/dev/null || true
gcloud compute firewall-rules create allow-https-vecinita --allow tcp:443 --target-tags https-server --source-ranges 0.0.0.0/0 2>/dev/null || true

# Get VM IP
VM_IP=$(gcloud compute instances describe "$VM_NAME" --zone="$ZONE" --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo -e "${GREEN}VM IP Address: $VM_IP${NC}"

# Prepare deployment files
echo -e "${YELLOW}Preparing deployment files...${NC}"
cd "$(dirname "$0")/.."

# Create temporary deployment directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Copy necessary files
cp docker-compose.yml "$TEMP_DIR/"
cp .env "$TEMP_DIR/" 2>/dev/null || echo "Warning: .env file not found"
cp -r backend "$TEMP_DIR/"
cp -r frontend "$TEMP_DIR/"

# Create systemd service file
cat > "$TEMP_DIR/vecinita.service" << 'EOF'
[Unit]
Description=Vecinita Docker Compose Services
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/vecinita/app
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=vecinita

[Install]
WantedBy=multi-user.target
EOF

# Create deployment script for VM
cat > "$TEMP_DIR/setup.sh" << 'EOF'
#!/bin/bash
set -e

echo "Setting up Vecinita on VM..."

# Create app directory
sudo mkdir -p /home/vecinita/app
sudo chown vecinita:vecinita /home/vecinita/app

# Copy files
cd /home/vecinita/app
cp /tmp/vecinita-deploy/* . -r

# Install systemd service
sudo cp vecinita.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vecinita.service

# Start services
echo "Starting Docker Compose services..."
sudo -u vecinita docker compose pull
sudo -u vecinita docker compose up -d

echo "Vecinita deployment complete!"
echo ""
echo "Services:"
echo "  Frontend: http://$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H "Metadata-Flavor: Google"):3000"
echo "  Backend API: http://$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H "Metadata-Flavor: Google"):8000"
echo "  API Docs: http://$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H "Metadata-Flavor: Google"):8000/docs"
echo ""
echo "Check status: sudo systemctl status vecinita"
echo "View logs: docker compose logs -f"
EOF

chmod +x "$TEMP_DIR/setup.sh"

# Copy files to VM
echo -e "${YELLOW}Copying files to VM...${NC}"
gcloud compute scp --recurse "$TEMP_DIR"/* "$VM_NAME:/tmp/vecinita-deploy/" --zone="$ZONE"

# Run setup script on VM
echo -e "${YELLOW}Running setup script on VM...${NC}"
gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="bash /tmp/vecinita-deploy/setup.sh"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services are now running at:"
echo "  Frontend: http://$VM_IP:3000"
echo "  Backend API: http://$VM_IP:8000"
echo "  API Docs: http://$VM_IP:8000/docs"
echo ""
echo "Useful commands:"
echo "  SSH to VM: gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "  Check status: gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo systemctl status vecinita'"
echo "  View logs: gcloud compute ssh $VM_NAME --zone=$ZONE --command='cd /home/vecinita/app && docker compose logs -f'"
echo "  Restart: gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo systemctl restart vecinita'"
echo "  Stop VM: gcloud compute instances stop $VM_NAME --zone=$ZONE"
echo "  Start VM: gcloud compute instances start $VM_NAME --zone=$ZONE"
echo ""
echo -e "${YELLOW}Cost estimate: ~\$25-35/month for e2-standard-2 (always on)${NC}"
echo -e "${YELLOW}To reduce costs, stop VM when not in use: gcloud compute instances stop $VM_NAME --zone=$ZONE${NC}"
