# PowerShell Script to Get Azure DevOps Repository ID
# Usage: .\get-azure-repo-id.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Azure DevOps Repository ID Finder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Prompt for PAT
Write-Host "Step 1: Enter your Azure DevOps Personal Access Token (PAT)" -ForegroundColor Yellow
Write-Host "Create one at: https://dev.azure.com/prakashranjan0943/_usersSettings/tokens" -ForegroundColor Gray
Write-Host ""
$pat = Read-Host "Enter PAT" -AsSecureString
$patText = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pat))

if ([string]::IsNullOrWhiteSpace($patText)) {
    Write-Host "❌ PAT cannot be empty!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔍 Fetching repositories..." -ForegroundColor Cyan

# Encode PAT for Basic Auth
$base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$patText"))
$headers = @{
    Authorization = "Basic $base64"
}

# API URL
$apiUrl = "https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_apis/git/repositories?api-version=7.1"

try {
    # Call Azure DevOps API
    $response = Invoke-RestMethod -Uri $apiUrl -Headers $headers -Method Get
    
    Write-Host ""
    Write-Host "✅ Found $($response.count) repositories:" -ForegroundColor Green
    Write-Host ""
    
    foreach ($repo in $response.value) {
        Write-Host "Repository: $($repo.name)" -ForegroundColor White
        Write-Host "  ID: $($repo.id)" -ForegroundColor Yellow
        Write-Host "  URL: $($repo.webUrl)" -ForegroundColor Gray
        Write-Host ""
        
        # Save the one we need
        if ($repo.name -eq "Internal Deployment Portal") {
            $targetRepoId = $repo.id
            $targetRepoName = $repo.name
        }
    }
    
    if ($targetRepoId) {
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✅ FOUND YOUR REPOSITORY!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Repository Name: $targetRepoName" -ForegroundColor White
        Write-Host "Repository ID: $targetRepoId" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Add this to your .env file:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "AZDO_REPOSITORY_ID=$targetRepoId" -ForegroundColor White
        Write-Host "AZDO_PAT=$patText" -ForegroundColor White
        Write-Host ""
        
        # Offer to create .env file
        Write-Host "Would you like to create the .env file now? (Y/N)" -ForegroundColor Yellow
        $createEnv = Read-Host
        
        if ($createEnv -eq "Y" -or $createEnv -eq "y") {
            $envContent = @"
# Internal Developers Platform - Production Configuration
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
DEMO_MODE=false

# AWS Configuration
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514
DYNAMODB_ENDPOINT_URL=http://dynamodb-local:8000
DYNAMODB_TABLE_PREFIX=internal-dev-portal

# Azure DevOps Configuration
AZDO_ORGANIZATION=prakashranjan0943
AZDO_PROJECT=Internal Deployment Portal
AZDO_REPOSITORY_ID=$targetRepoId
AZDO_PIPELINE_ID=1
AZDO_PAT=$patText

# Git Configuration
GIT_REPOSITORY=https://dev.azure.com/prakashranjan0943/Internal%20Deployment%20Portal/_git/Internal%20Deployment%20Portal
GIT_BRANCH=main

# Backend Configuration
BACKEND_API_URL=http://corridors:8100
TERRAFORM_MODULES_PATH=/terraform-modules

# Frontend Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8100

# S3 Configuration (optional)
S3_BUCKET=internal-dev-portal-artifacts
S3_TFSTATE_BUCKET=internal-dev-portal-tfstate
DYNAMODB_LOCK_TABLE=internal-dev-portal-tfstate-lock
"@
            
            Set-Content -Path ".env" -Value $envContent
            Write-Host ""
            Write-Host "✅ Created .env file successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "⚠️  IMPORTANT: Never commit .env to Git!" -ForegroundColor Red
            Write-Host "    It contains your PAT token!" -ForegroundColor Red
            Write-Host ""
            Write-Host "Next steps:" -ForegroundColor Cyan
            Write-Host "1. Copy .env to your VPS (use SCP or copy manually)" -ForegroundColor White
            Write-Host "2. Run: docker-compose down" -ForegroundColor White
            Write-Host "3. Run: docker-compose build --no-cache backend" -ForegroundColor White
            Write-Host "4. Run: docker-compose up -d" -ForegroundColor White
            Write-Host ""
        } else {
            Write-Host ""
            Write-Host "Copy the values above to your .env file manually." -ForegroundColor Cyan
        }
    } else {
        Write-Host "❌ Repository 'Internal Deployment Portal' not found!" -ForegroundColor Red
        Write-Host "Available repositories are listed above." -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Error accessing Azure DevOps API!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible issues:" -ForegroundColor Yellow
    Write-Host "1. Invalid PAT token" -ForegroundColor White
    Write-Host "2. PAT doesn't have 'Code: Read' permission" -ForegroundColor White
    Write-Host "3. Network connectivity issue" -ForegroundColor White
    Write-Host ""
    Write-Host "Create a new PAT at:" -ForegroundColor Cyan
    Write-Host "https://dev.azure.com/prakashranjan0943/_usersSettings/tokens" -ForegroundColor Gray
    Write-Host "Ensure it has 'Code: Read & write' permission" -ForegroundColor Gray
    exit 1
}
