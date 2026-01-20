<#
.SYNOPSIS
    Deploy Document Image Extractor MCP to Azure Container Apps

.DESCRIPTION
    This script automates the deployment of the MCP server to Azure Container Apps.
    It creates all necessary Azure resources and deploys the containerized application.

.PARAMETER ResourceGroupName
    Name of the Azure resource group (will be created if it doesn't exist)

.PARAMETER Location
    Azure region for deployment (e.g., eastus, westus2, westeurope)

.PARAMETER ContainerAppName
    Name for the Container App

.PARAMETER ContainerRegistryName
    Name for Azure Container Registry (ACR)

.PARAMETER EnvironmentName
    Name for Container Apps Environment

.EXAMPLE
    .\deploy-azure-container-apps.ps1 -ResourceGroupName "mcp-extractor-rg" -Location "eastus"

.EXAMPLE
    .\deploy-azure-container-apps.ps1 -ResourceGroupName "mcp-rg" -Location "westus2" -ContainerAppName "my-extractor"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$Location,
    
    [Parameter(Mandatory=$false)]
    [string]$ContainerAppName = "doc-image-extractor",
    
    [Parameter(Mandatory=$false)]
    [string]$ContainerRegistryName = "",
    
    [Parameter(Mandatory=$false)]
    [string]$EnvironmentName = "mcp-extractor-env"
)

# Auto-generate registry name if not provided (must be globally unique)
if ([string]::IsNullOrEmpty($ContainerRegistryName)) {
    $random = Get-Random -Minimum 1000 -Maximum 9999
    $ContainerRegistryName = "mcpextractor$random"
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Azure Container Apps Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Resource Group: $ResourceGroupName"
Write-Host "  Location: $Location"
Write-Host "  Container App: $ContainerAppName"
Write-Host "  Container Registry: $ContainerRegistryName"
Write-Host "  Environment: $EnvironmentName`n"

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

# Install/upgrade Container Apps extension
Write-Host "Installing Container Apps extension..." -ForegroundColor Yellow
az extension add --name containerapp --upgrade --only-show-errors
Write-Host "✓ Container Apps extension ready`n" -ForegroundColor Green

# Create resource group
Write-Host "Creating resource group..." -ForegroundColor Yellow
az group create --name $ResourceGroupName --location $Location --output none
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Resource group created/verified`n" -ForegroundColor Green
}

# Create Azure Container Registry
Write-Host "Creating Azure Container Registry..." -ForegroundColor Yellow
az acr create `
    --resource-group $ResourceGroupName `
    --name $ContainerRegistryName `
    --sku Basic `
    --admin-enabled true `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Container Registry created: $ContainerRegistryName`n" -ForegroundColor Green
}

# Get ACR credentials
Write-Host "Getting ACR credentials..." -ForegroundColor Yellow
$acrServer = az acr show --name $ContainerRegistryName --resource-group $ResourceGroupName --query loginServer -o tsv
$acrUsername = az acr credential show --name $ContainerRegistryName --query username -o tsv
$acrPassword = az acr credential show --name $ContainerRegistryName --query "passwords[0].value" -o tsv
Write-Host "✓ ACR credentials retrieved`n" -ForegroundColor Green

# Build and push Docker image
Write-Host "Building Docker image..." -ForegroundColor Yellow
$imageName = "$acrServer/${ContainerAppName}:latest"

# Login to ACR
az acr login --name $ContainerRegistryName

# Build image
Push-Location ..
docker build -t $imageName .
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "✓ Docker image built`n" -ForegroundColor Green

# Push image
Write-Host "Pushing image to ACR..." -ForegroundColor Yellow
docker push $imageName
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker push failed" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location
Write-Host "✓ Image pushed to ACR`n" -ForegroundColor Green

# Create Container Apps environment
Write-Host "Creating Container Apps environment..." -ForegroundColor Yellow
az containerapp env create `
    --name $EnvironmentName `
    --resource-group $ResourceGroupName `
    --location $Location `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Container Apps environment created`n" -ForegroundColor Green
}

# Create Container App
Write-Host "Deploying Container App..." -ForegroundColor Yellow
az containerapp create `
    --name $ContainerAppName `
    --resource-group $ResourceGroupName `
    --environment $EnvironmentName `
    --image $imageName `
    --registry-server $acrServer `
    --registry-username $acrUsername `
    --registry-password $acrPassword `
    --target-port 8000 `
    --ingress external `
    --min-replicas 1 `
    --max-replicas 10 `
    --cpu 0.5 `
    --memory 1.0Gi `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Container App deployed!`n" -ForegroundColor Green
}

# Get the app URL
Write-Host "Getting application URL..." -ForegroundColor Yellow
$appUrl = az containerapp show `
    --name $ContainerAppName `
    --resource-group $ResourceGroupName `
    --query properties.configuration.ingress.fqdn `
    -o tsv

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment Successful!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "Application URL: https://$appUrl`n" -ForegroundColor Cyan

Write-Host "Endpoints:" -ForegroundColor Yellow
Write-Host "  Health Check:  https://$appUrl/api/health" -ForegroundColor White
Write-Host "  Extract Base64: https://$appUrl/api/extract-base64" -ForegroundColor White
Write-Host "  MCP SSE:       https://$appUrl/sse`n" -ForegroundColor White

Write-Host "Testing health endpoint..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
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
Write-Host "  https://portal.azure.com/#resource/subscriptions/$((az account show --query id -o tsv))/resourceGroups/$ResourceGroupName/providers/Microsoft.App/containerApps/$ContainerAppName`n"

Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  az containerapp logs show --name $ContainerAppName --resource-group $ResourceGroupName --follow`n"
