# Vecinita Single VM Deployment Script for GCP (PowerShell)
# Deploys all services to one Compute Engine VM with Docker Compose

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Zone = "us-east1-b",
    
    [Parameter(Mandatory=$false)]
    [string]$VmName = "vecinita-vm",
    
    [Parameter(Mandatory=$false)]
    [string]$MachineType = "e2-standard-2"  # 2 vCPU, 8GB RAM
)

Write-Host "Starting Vecinita VM Deployment" -ForegroundColor Green
Write-Host "Project: $ProjectId"
Write-Host "Zone: $Zone"
Write-Host "VM Name: $VmName"
Write-Host "Machine Type: $MachineType (2 vCPU, 8GB RAM)"
Write-Host ""

# Set project
Write-Host "Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Enable required APIs
Write-Host "Enabling Compute Engine API..." -ForegroundColor Yellow
gcloud services enable compute.googleapis.com

# Check if VM already exists
$vmExists = $false
try {
    gcloud compute instances describe $VmName --zone=$Zone 2>$null
    $vmExists = $true
    Write-Host "VM $VmName already exists. Recreate it? (y/N): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -match '^[Yy]$') {
        Write-Host "Deleting existing VM..." -ForegroundColor Yellow
        gcloud compute instances delete $VmName --zone=$Zone --quiet
        $vmExists = $false
    } else {
        Write-Host "Using existing VM" -ForegroundColor Green
    }
} catch {
    # VM doesn't exist, continue
}

# Create VM if it doesn't exist
if (-not $vmExists) {
    Write-Host "Creating VM instance..." -ForegroundColor Yellow
    
    $startupScript = @'
#!/bin/bash
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
'@

    gcloud compute instances create $VmName `
        --zone=$Zone `
        --machine-type=$MachineType `
        --image-family=ubuntu-2204-lts `
        --image-project=ubuntu-os-cloud `
        --boot-disk-size=50GB `
        --boot-disk-type=pd-standard `
        --tags=http-server,https-server `
        --metadata=startup-script=$startupScript

    Write-Host "VM created successfully!" -ForegroundColor Green
    Write-Host "Waiting 60 seconds for startup script to complete..." -ForegroundColor Yellow
    Start-Sleep -Seconds 60
}

# Create firewall rules
Write-Host "Setting up firewall rules..." -ForegroundColor Yellow
gcloud compute firewall-rules create allow-http-vecinita --allow tcp:80,tcp:8000,tcp:3000 --target-tags http-server --source-ranges 0.0.0.0/0 2>$null
gcloud compute firewall-rules create allow-https-vecinita --allow tcp:443 --target-tags https-server --source-ranges 0.0.0.0/0 2>$null

# Get VM IP
$vmIp = gcloud compute instances describe $VmName --zone=$Zone --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
Write-Host "VM IP Address: $vmIp" -ForegroundColor Green

# Clone repository and setup on VM
Write-Host "Cloning Vecinita repository on VM..." -ForegroundColor Yellow
gcloud compute ssh $VmName --zone=$Zone --command="cd /tmp && rm -rf vecinita-repo && git clone https://github.com/acadiagit/vecinita.git vecinita-repo"

# Copy .env file to VM
Write-Host "Uploading .env file..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
if (Test-Path "$rootDir\.env") {
    gcloud compute scp "$rootDir\.env" "${VmName}:/tmp/vecinita-repo/" --zone=$Zone
} else {
    Write-Host "Warning: .env file not found - you'll need to manually add it" -ForegroundColor Yellow
}

# Create setup script content
$setupScript = @"
#!/bin/bash
set -e

echo "Setting up Vecinita on VM..."

# Create vecinita user if it doesn't exist
id -u vecinita >/dev/null 2>&1 || (sudo useradd -m -s /bin/bash vecinita && sudo usermod -aG docker vecinita)

# Create app directory
sudo mkdir -p /home/vecinita/app
sudo chown vecinita:vecinita /home/vecinita/app

# Copy repository
cp -r /tmp/vecinita-repo/* /home/vecinita/app/

# Create systemd service
sudo tee /etc/systemd/system/vecinita.service > /dev/null << 'SERVICEEOF'
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
SERVICEEOF

sudo systemctl daemon-reload
sudo systemctl enable vecinita.service

# Start services
echo "Starting Docker Compose services..."
cd /home/vecinita/app
sudo -u vecinita docker compose pull
sudo -u vecinita docker compose up -d

echo "Vecinita deployment complete!"
"@

# Write setup script to temporary file on local machine with Unix line endings and NO BOM
$localSetupScript = Join-Path $env:TEMP "vecinita_setup.sh"
# Convert to Unix line endings (LF only, no CRLF)
$unixScript = $setupScript -replace "`r`n", "`n"
# Write UTF-8 without BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($localSetupScript, $unixScript, $utf8NoBom)

# Copy setup script to VM
Write-Host "Uploading setup script to VM..." -ForegroundColor Yellow
gcloud compute scp $localSetupScript "${VmName}:/tmp/vecinita_setup.sh" --zone=$Zone

# Execute setup script on VM
Write-Host "Setting up Docker Compose on VM..." -ForegroundColor Yellow
gcloud compute ssh $VmName --zone=$Zone --command="bash /tmp/vecinita_setup.sh"

# Cleanup local setup script
Remove-Item $localSetupScript -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services are now running at:"
Write-Host "  Frontend: http://${vmIp}:3000"
Write-Host "  Backend API: http://${vmIp}:8000"
Write-Host "  API Docs: http://${vmIp}:8000/docs"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  SSH to VM: gcloud compute ssh $VmName --zone=$Zone"
Write-Host "  Check status: gcloud compute ssh $VmName --zone=$Zone --command='sudo systemctl status vecinita'"
Write-Host "  View logs: gcloud compute ssh $VmName --zone=$Zone --command='cd /home/vecinita/app && docker compose logs -f'"
Write-Host "  Restart: gcloud compute ssh $VmName --zone=$Zone --command='sudo systemctl restart vecinita'"
Write-Host "  Stop VM: gcloud compute instances stop $VmName --zone=$Zone"
Write-Host "  Start VM: gcloud compute instances start $VmName --zone=$Zone"
Write-Host ""
Write-Host "Cost estimate: ~`$25-35/month for e2-standard-2 (always on)" -ForegroundColor Yellow
Write-Host "To reduce costs, stop VM when not in use" -ForegroundColor Yellow

Read-Host "Press Enter to exit"
