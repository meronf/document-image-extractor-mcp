<#
.SYNOPSIS
    Deploy Document Image Extractor MCP to Azure App Service

.DESCRIPTION
    This script automates the deployment of the MCP server to Azure App Service.
    It creates all necessary Azure resources and deploys the application.

.PARAMETER ResourceGroupName
    Name of the Azure resource group (will be created if it doesn't exist)

.PARAMETER Location
    Azure region for deployment (e.g., eastus, westus2, westeurope)

.PARAMETER AppName
    Name for the App Service (must be globally unique)

.PARAMETER AppServicePlan
    Name for the App Service Plan

.PARAMETER Sku
    App Service Plan SKU (B1, B2, B3, S1, S2, S3, P1V2, P2V2, P3V2)

.EXAMPLE
    .\deploy-azure-app-service.ps1 -ResourceGroupName "mcp-extractor-rg" -Location "eastus" -AppName "doc-extractor-app"

.EXAMPLE
    .\deploy-azure-app-service.ps1 -ResourceGroupName "mcp-rg" -Location "westus2" -AppName "my-extractor" -Sku "P1V2"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$Location,
    
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    
    [Parameter(Mandatory=$false)]
    [string]$AppServicePlan = "$AppName-plan",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("F1", "B1", "B2", "B3", "S1", "S2", "S3", "P1V2", "P2V2", "P3V2")]
    [string]$Sku = "B1"
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Azure App Service Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Resource Group: $ResourceGroupName"
Write-Host "  Location: $Location"
Write-Host "  App Name: $AppName"
Write-Host "  App Service Plan: $AppServicePlan"
Write-Host "  SKU: $Sku`n"

# Check if Azure CLI is installed
Write-Host "Checking Azure CLI..." -ForegroundColor Yellow
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "✓ Azure CLI version: $($azVersion.'azure-cli')" -ForegroundColor Green
}
catch {
    Write-Host "✗ Azure CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "  winget install Microsoft.AzureCLI`n" -ForegroundColor White
    exit 1
}

# Check if logged in
Write-Host "`nChecking Azure login..." -ForegroundColor Yellow
try {
    $account = az account show 2>&1 | ConvertFrom-Json
    Write-Host "✓ Logged in as: $($account.user.name)" -ForegroundColor Green
    Write-Host "  Subscription: $($account.name)`n" -ForegroundColor Gray
}
catch {
    Write-Host "✗ Not logged in to Azure. Running az login..." -ForegroundColor Yellow
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Login failed" -ForegroundColor Red
        exit 1
    }
}

# Create resource group
Write-Host "Creating resource group..." -ForegroundColor Yellow
az group create --name $ResourceGroupName --location $Location --output none
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Resource group created/verified`n" -ForegroundColor Green
}

# Create App Service Plan
Write-Host "Creating App Service Plan..." -ForegroundColor Yellow
az appservice plan create `
    --name $AppServicePlan `
    --resource-group $ResourceGroupName `
    --location $Location `
    --sku $Sku `
    --is-linux `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ App Service Plan created`n" -ForegroundColor Green
}

# Create Web App
Write-Host "Creating Web App..." -ForegroundColor Yellow
az webapp create `
    --resource-group $ResourceGroupName `
    --plan $AppServicePlan `
    --name $AppName `
    --runtime "PYTHON:3.12" `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Web App created`n" -ForegroundColor Green
}

# Configure startup command
Write-Host "Configuring startup command..." -ForegroundColor Yellow
az webapp config set `
    --resource-group $ResourceGroupName `
    --name $AppName `
    --startup-file "python -m document_image_extractor_mcp" `
    --output none

Write-Host "✓ Startup command configured`n" -ForegroundColor Green

# Set app settings
Write-Host "Configuring app settings..." -ForegroundColor Yellow
az webapp config appsettings set `
    --resource-group $ResourceGroupName `
    --name $AppName `
    --settings `
        SCM_DO_BUILD_DURING_DEPLOYMENT=true `
        PYTHON_VERSION=3.12 `
        PORT=8000 `
    --output none

Write-Host "✓ App settings configured`n" -ForegroundColor Green

# Enable HTTPS only
Write-Host "Enabling HTTPS only..." -ForegroundColor Yellow
az webapp update `
    --resource-group $ResourceGroupName `
    --name $AppName `
    --https-only true `
    --output none

Write-Host "✓ HTTPS enforced`n" -ForegroundColor Green

# Deploy code
Write-Host "Deploying application code..." -ForegroundColor Yellow
Write-Host "(This may take a few minutes...)" -ForegroundColor Gray

Push-Location ..

# Create a temporary zip file
$tempZip = "$env:TEMP\mcp-deploy.zip"
if (Test-Path $tempZip) {
    Remove-Item $tempZip
}

# Compress project files
Compress-Archive -Path @(
    "src",
    "pyproject.toml"
) -DestinationPath $tempZip -Force

# Deploy zip
az webapp deploy `
    --resource-group $ResourceGroupName `
    --name $AppName `
    --src-path $tempZip `
    --type zip `
    --output none

Pop-Location

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Application deployed!`n" -ForegroundColor Green
}

# Remove temp zip
Remove-Item $tempZip -ErrorAction SilentlyContinue

# Get the app URL
$appUrl = az webapp show `
    --name $AppName `
    --resource-group $ResourceGroupName `
    --query defaultHostName `
    -o tsv

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment Successful!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "Application URL: https://$appUrl`n" -ForegroundColor Cyan

Write-Host "Endpoints:" -ForegroundColor Yellow
Write-Host "  Health Check:   https://$appUrl/api/health" -ForegroundColor White
Write-Host "  Extract Base64: https://$appUrl/api/extract-base64" -ForegroundColor White
Write-Host "  MCP SSE:        https://$appUrl/sse`n" -ForegroundColor White

Write-Host "Waiting for app to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "Testing health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "https://$appUrl/api/health"
    Write-Host "✓ Health check passed!" -ForegroundColor Green
    Write-Host "  Status: $($health.status)" -ForegroundColor Gray
    Write-Host "  Service: $($health.service)`n" -ForegroundColor Gray
}
catch {
    Write-Host "⚠ Health check not ready yet. It may take a few minutes." -ForegroundColor Yellow
    Write-Host "  Try: https://$appUrl/api/health`n" -ForegroundColor Gray
}

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the API endpoints above"
Write-Host "  2. Update your Power Automate flows with the new URL"
Write-Host "  3. Configure authentication if needed"
Write-Host "  4. Set up Application Insights for monitoring"
Write-Host "  5. Configure custom domain (optional)`n"

Write-Host "View in Azure Portal:" -ForegroundColor Yellow
Write-Host "  https://portal.azure.com/#resource/subscriptions/$((az account show --query id -o tsv))/resourceGroups/$ResourceGroupName/providers/Microsoft.Web/sites/$AppName`n"

Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  az webapp log tail --name $AppName --resource-group $ResourceGroupName`n"

Write-Host "To enable continuous deployment from GitHub:" -ForegroundColor Yellow
Write-Host "  az webapp deployment source config --name $AppName --resource-group $ResourceGroupName --repo-url <your-github-repo> --branch main`n"
