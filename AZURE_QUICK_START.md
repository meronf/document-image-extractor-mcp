# 🚀 Azure Deployment - Quick Start

## TL;DR - Deploy Now!

### Azure App Service (Your Choice - Easiest!) ⭐

```powershell
# Install Azure CLI if needed
winget install Microsoft.AzureCLI

# Login to Azure
az login

# Deploy
cd deploy
.\deploy-azure-app-service.ps1 `
    -ResourceGroupName "mcp-extractor-rg" `
    -Location "eastus" `
    -AppName "doc-image-extractor-app"
```

**Done!** Your API will be at: `https://<your-app>.azurewebsites.net`

---

### Alternative: Azure Container Apps

```powershell
# Login to Azure
az login

# Deploy (requires Docker Desktop running)
cd deploy
.\deploy-azure-container-apps.ps1 `
    -ResourceGroupName "mcp-extractor-rg" `
    -Location "eastus" `
    -ContainerAppName "doc-image-extractor"
```

**Done!** Your API will be at: `https://<your-app>.azurecontainerapps.io`

---

## Why You Chose App Service ✅

### Benefits of Your Choice:
- ✅ **No Docker needed** - Direct deployment
- ✅ **Simplest setup** - Familiar web hosting
- ✅ **Always-on** - No cold starts
- ✅ **Predictable billing** - $13/month flat rate

**Cost:** ~$13/month (B1 tier) - always running

### Container Apps Alternative:
- 💰 Scales to $0 when idle
- 🚀 Modern cloud-native architecture
- 📊 Pay only for usage
- ⚡ Requires Docker Desktop

**Cost:** ~$5-20/month for variable traffic

---

## After Deployment

### 1. Test Your Deployment

```powershell
# Health check
Invoke-RestMethod -Uri "https://your-app-url/api/health"

# Extract images (with test PDF)
$pdf = [Convert]::ToBase64String([IO.File]::ReadAllBytes("test.pdf"))
$body = @{
    document_base64 = $pdf
    document_name = "test.pdf"
    return_images_as_base64 = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://your-app-url/api/extract-base64" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### 2. Update Power Automate

Change your HTTP action URL from:
```
http://localhost:8000/api/extract-base64
```

To:
```
https://your-app-url/api/extract-base64
```

### 3. Monitor Your App

**Container Apps:**
```powershell
az containerapp logs show --name <app-name> --resource-group <rg> --follow
```

**App Service:**
```powershell
az webapp log tail --name <app-name> --resource-group <rg>
```

---

## Cost Estimates

### Azure Container Apps (Recommended)

| Usage Level | Monthly Cost | Notes |
|-------------|-------------|-------|
| **Development** | $0-5 | Scales to zero when not used |
| **Low Traffic** | $5-20 | Few requests per day |
| **Medium Traffic** | $20-50 | Regular use throughout day |
| **High Traffic** | $50-200 | Constant high load |

### Azure App Service

| Tier | Monthly Cost | CPU | RAM | Notes |
|------|-------------|-----|-----|-------|
| **B1** | $13 | 1 core | 1.75 GB | Development/testing |
| **B2** | $26 | 2 cores | 3.5 GB | Small production |
| **P1V2** | $80 | 1 core | 3.5 GB | Production recommended |
| **P2V2** | $160 | 2 cores | 7 GB | High traffic |

---

## Security Setup (Important!)

### Enable HTTPS Only (Already configured)
✅ Automatically enabled in both options

### Add API Key Authentication

```powershell
# Set an API key
az containerapp update --name <app> --resource-group <rg> `
    --set-env-vars "API_KEY=your-secret-key"
```

Then modify server.py to check the API key in requests.

### Use Azure AD Authentication

```powershell
# Enable Azure AD
az webapp auth update --resource-group <rg> --name <app> `
    --enabled true --action LoginWithAzureActiveDirectory
```

---

## Monitoring Setup

### Enable Application Insights

```powershell
# Create Application Insights
az monitor app-insights component create `
    --app mcp-extractor-insights `
    --location eastus `
    --resource-group mcp-extractor-rg

# Get instrumentation key
$key = az monitor app-insights component show `
    --app mcp-extractor-insights `
    --resource-group mcp-extractor-rg `
    --query instrumentationKey -o tsv

# Configure app to use it
az containerapp update --name <app> --resource-group <rg> `
    --set-env-vars "APPLICATIONINSIGHTS_CONNECTION_STRING=$key"
```

---

## Scaling Configuration

### Container Apps Auto-scaling

```powershell
# Configure scaling rules
az containerapp update --name <app> --resource-group <rg> `
    --min-replicas 0 `
    --max-replicas 10 `
    --scale-rule-name http-requests `
    --scale-rule-type http `
    --scale-rule-http-concurrency 10
```

### App Service Scaling

```powershell
# Scale up (more power)
az appservice plan update --name <plan> --resource-group <rg> --sku P1V2

# Scale out (more instances)
az appservice plan update --name <plan> --resource-group <rg> --number-of-workers 3
```

---

## Continuous Deployment

### GitHub Actions (Recommended)

1. Copy the appropriate workflow file:
   - `deploy/github-actions-container-apps.yml` → `.github/workflows/deploy.yml`
   - `deploy/github-actions-app-service.yml` → `.github/workflows/deploy.yml`

2. Add Azure credentials to GitHub Secrets:
   - Go to your repo → Settings → Secrets
   - Add `AZURE_CREDENTIALS` (get from: `az ad sp create-for-rbac`)

3. Push to main branch → Automatic deployment!

---

## Troubleshooting

### Container won't start
```powershell
# Check logs
az containerapp logs show --name <app> --resource-group <rg> --follow
```

### App Service deployment fails
```powershell
# Check deployment logs
az webapp log deployment show --name <app> --resource-group <rg>
```

### Health check fails
- Wait 2-3 minutes after deployment
- Check if port 8000 is correctly configured
- Verify Python dependencies installed

### Out of memory
- Increase memory allocation in Container Apps
- Upgrade to higher App Service tier
- Implement document size limits

---

## Clean Up Resources

### Delete everything
```powershell
az group delete --name mcp-extractor-rg --yes
```

### Delete just the app
```powershell
# Container Apps
az containerapp delete --name <app> --resource-group <rg>

# App Service
az webapp delete --name <app> --resource-group <rg>
```

---

## Next Steps

1. ✅ Deploy using one of the scripts above
2. ✅ Test the health endpoint
3. ✅ Update Power Automate with new URL
4. ✅ Set up monitoring with Application Insights
5. ✅ Configure authentication for production
6. ✅ Set up CI/CD with GitHub Actions

---

## Getting Help

- **Azure Portal**: https://portal.azure.com
- **Azure CLI docs**: https://learn.microsoft.com/cli/azure/
- **Container Apps docs**: https://learn.microsoft.com/azure/container-apps/
- **App Service docs**: https://learn.microsoft.com/azure/app-service/

**For issues:** Check logs first, then review Azure Portal diagnostics.
