#!/usr/bin/env pwsh
# Deploy Supabase Edge Function for Retrieval
# This script deploys the search-similar-documents edge function to Supabase

param(
    [switch]$Local = $false,
    [switch]$Test = $false
)

$ErrorActionPreference = "Stop"

$functionName = "search-similar-documents"

Write-Host "🚀 Deploying Supabase Edge Function: $functionName" -ForegroundColor Cyan

# Check if Supabase CLI is installed
if (-not (Get-Command supabase -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Supabase CLI not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install Supabase CLI:" -ForegroundColor Yellow
    Write-Host "  npm install -g supabase"
    Write-Host "  OR download from: https://github.com/supabase/cli/releases"
    Write-Host ""
    exit 1
}

Write-Host "✅ Supabase CLI found: $(supabase --version)" -ForegroundColor Green

# Change to repository root
$repoRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $repoRoot
Set-Location $repoRoot

Write-Host "📁 Repository root: $repoRoot" -ForegroundColor Gray

# Check if .env exists for Supabase settings
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Write-Host "✅ Found .env file" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "   Create .env and add SUPABASE_URL/SUPABASE_KEY values" -ForegroundColor Yellow
}

if ($Local) {
    # Start local Supabase
    Write-Host ""
    Write-Host "🏠 Starting local Supabase..." -ForegroundColor Cyan
    supabase start
    
    Write-Host ""
    Write-Host "🔧 Serving edge function locally..." -ForegroundColor Cyan
    Write-Host "   Access at: http://127.0.0.1:54321/functions/v1/$functionName" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    supabase functions serve $functionName
    
} elseif ($Test) {
    # Test the deployed function
    Write-Host ""
    Write-Host "🧪 Testing edge function..." -ForegroundColor Cyan
    
    $testPayload = @{
        query = "housing support"
        query_embedding = @(0.01, 0.02, 0.03)
        match_threshold = 0.1
        match_count = 1
        tag_filter = @("housing")
        tag_match_mode = "any"
        include_untagged_fallback = $true
    } | ConvertTo-Json
    
    Write-Host "   Payload: $testPayload" -ForegroundColor Gray
    
    # Get Supabase URL from .env
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile -Raw
        if ($envContent -match "SUPABASE_URL=(.+)") {
            $supabaseUrl = $matches[1].Trim()
            if ($envContent -match "SUPABASE_KEY=(.+)") {
                $supabaseKey = $matches[1].Trim()
                
                $functionUrl = "$supabaseUrl/functions/v1/$functionName"
                Write-Host "   Calling: $functionUrl" -ForegroundColor Gray
                
                try {
                    $response = Invoke-RestMethod -Uri $functionUrl `
                        -Method Post `
                        -Headers @{
                            "Authorization" = "Bearer $supabaseKey"
                            "Content-Type" = "application/json"
                        } `
                        -Body $testPayload
                    
                    Write-Host ""
                    Write-Host "✅ Success! Response:" -ForegroundColor Green
                    if ($response.data) {
                        Write-Host "   Rows returned: $($response.data.Count)" -ForegroundColor Gray
                    } else {
                        Write-Host "   Response body: $($response | ConvertTo-Json -Depth 4)" -ForegroundColor Gray
                    }
                    
                } catch {
                    Write-Host ""
                    Write-Host "❌ Test failed: $_" -ForegroundColor Red
                    Write-Host $_.Exception.Message -ForegroundColor Red
                    exit 1
                }
            } else {
                Write-Host "❌ SUPABASE_KEY not found in .env" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "❌ SUPABASE_URL not found in .env" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ .env file not found" -ForegroundColor Red
        exit 1
    }
    
} else {
    # Deploy to production
    Write-Host ""
    Write-Host "🚢 Deploying to production Supabase..." -ForegroundColor Cyan
    Write-Host ""
    
    # Check if logged in
    try {
        supabase projects list 2>&1 | Out-Null
    } catch {
        Write-Host "❌ Not logged in to Supabase!" -ForegroundColor Red
        Write-Host "   Run: supabase login" -ForegroundColor Yellow
        exit 1
    }
    
    # Deploy
    Write-Host "📤 Deploying function..." -ForegroundColor Cyan
    supabase functions deploy $functionName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Deployment successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Confirm search_similar_documents RPC is available in database" -ForegroundColor White
        Write-Host ""
        Write-Host "2. Set DB_SEARCH_EDGE_FUNCTION=$functionName in runtime env" -ForegroundColor White
        Write-Host "   → Dashboard → vecinita-agent → Environment" -ForegroundColor Gray
        Write-Host ""
        Write-Host "3. Test the function:" -ForegroundColor White
        Write-Host "   .\backend\scripts\deploy_edge_function.ps1 -Test" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "❌ Deployment failed!" -ForegroundColor Red
        exit 1
    }
}
