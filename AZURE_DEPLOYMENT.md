# Azure Deployment Guide

## Recommended Deployment Options

### Option 1: Azure Container Apps (Recommended) ⭐

**Best for:**
- Modern microservices architecture
- Auto-scaling based on HTTP requests
- Cost-effective (pay only for what you use)
- Built-in HTTPS with custom domains
- Easy integration with Azure services

**Pros:**
- ✅ Automatic scaling (including to zero)
- ✅ Built-in load balancing
- ✅ Managed infrastructure
- ✅ Container-based (easy updates)
- ✅ Cost-effective for variable workloads

**Cons:**
- ⚠️ Requires Docker knowledge
- ⚠️ Slightly more setup than App Service

**Estimated Cost:** $0-50/month (depends on usage)

---

### Option 2: Azure App Service (Easiest)

**Best for:**
- Quick deployment without Docker
- Traditional web app hosting
- Direct deployment from GitHub
- Built-in CI/CD

**Pros:**
- ✅ Easiest to deploy
- ✅ No container knowledge needed
- ✅ Built-in GitHub integration
- ✅ Automatic HTTPS
- ✅ Easy scaling

**Cons:**
- ⚠️ Always running (higher minimum cost)
- ⚠️ Less flexible than containers

**Estimated Cost:** $13-200/month (depends on tier)

---

### Option 3: Azure Container Instances

**Best for:**
- Simple container deployment
- Development/testing
- Low-traffic scenarios

**Pros:**
- ✅ Simple container deployment
- ✅ Pay per second
- ✅ Quick startup

**Cons:**
- ⚠️ No auto-scaling
- ⚠️ Manual load balancing needed
- ⚠️ No built-in custom domains

**Estimated Cost:** $10-30/month

---

### Option 4: Azure Functions (Not Recommended)

**Why not?**
- Long-running document processing may exceed timeout limits
- Not ideal for HTTP server architecture
- Better suited for event-driven workloads

---

## Comparison Table

| Feature | Container Apps | App Service | Container Instances |
|---------|---------------|-------------|---------------------|
| **Setup Complexity** | Medium | Easy | Easy |
| **Auto-scaling** | ✅ Yes | ✅ Yes | ❌ No |
| **Scale to zero** | ✅ Yes | ❌ No | ❌ No |
| **Custom domains** | ✅ Yes | ✅ Yes | ⚠️ Manual |
| **HTTPS** | ✅ Built-in | ✅ Built-in | ⚠️ Manual |
| **Cost (low traffic)** | $5-20 | $13+ | $10-30 |
| **Cost (high traffic)** | Scales | Fixed | Fixed |
| **Deployment** | Docker | Direct/GitHub | Docker |

---

## Our Recommendation: Azure Container Apps

For your document image extractor, we recommend **Azure Container Apps** because:

1. ✅ **Cost-effective**: Scales to zero when not in use
2. ✅ **HTTP-optimized**: Perfect for REST API and MCP server
3. ✅ **Auto-scaling**: Handles Power Automate traffic bursts
4. ✅ **Modern**: Container-based deployment
5. ✅ **Integrated**: Works well with Azure services

---

## Quick Start: Deploy to Azure Container Apps

### Prerequisites
- Azure subscription
- Azure CLI installed
- Docker installed (for building image)

### Step 1: Install Azure CLI
```bash
# Windows
winget install Microsoft.AzureCLI

# Verify installation
az --version
```

### Step 2: Login to Azure
```bash
az login
```

### Step 3: Deploy Using Our Script
```powershell
# See deploy-azure-container-apps.ps1 for automated deployment
.\deploy\deploy-azure-container-apps.ps1 `
    -ResourceGroupName "mcp-extractor-rg" `
    -Location "eastus" `
    -ContainerAppName "doc-image-extractor"
```

### Step 4: Access Your Deployment
```
Your API will be available at:
https://<your-app>.azurecontainerapps.io

Endpoints:
- Health: https://<your-app>.azurecontainerapps.io/api/health
- Extract: https://<your-app>.azurecontainerapps.io/api/extract-base64
- MCP SSE: https://<your-app>.azurecontainerapps.io/sse
```

---

## Quick Start: Deploy to Azure App Service

### Option A: Deploy from VS Code

1. Install Azure App Service extension
2. Right-click on project folder
3. Select "Deploy to Web App..."
4. Follow prompts

### Option B: Deploy using Azure CLI

```bash
# See deploy-azure-app-service.ps1 for automated deployment
.\deploy\deploy-azure-app-service.ps1 `
    -ResourceGroupName "mcp-extractor-rg" `
    -Location "eastus" `
    -AppName "doc-image-extractor"
```

---

## Security Considerations for Azure

### 1. Enable Azure AD Authentication
```bash
az webapp auth update --resource-group <rg> --name <app> \
    --enabled true --action LoginWithAzureActiveDirectory
```

### 2. Use Managed Identity
- Access Azure services without storing credentials
- Automatically rotates secrets

### 3. Configure App Settings (Environment Variables)
```bash
az containerapp update --name <app> --resource-group <rg> \
    --set-env-vars "MAX_DOCUMENT_SIZE=10485760"
```

### 4. Use Azure Key Vault for Secrets
- Store API keys securely
- Integrate with Managed Identity

### 5. Enable HTTPS Only
- Automatically configured in both services
- Custom domains with SSL certificates

---

## Integration with Power Automate

### After Deployment

Update your Power Automate HTTP action:

**Before:**
```
http://localhost:8000/api/extract-base64
```

**After:**
```
https://your-app.azurecontainerapps.io/api/extract-base64
```

### Add Authentication Header (if enabled)
```json
{
  "Authorization": "Bearer <your-azure-ad-token>"
}
```

---

## Monitoring and Logging

### Azure Application Insights (Recommended)

```bash
# Enable Application Insights
az monitor app-insights component create \
    --app your-app-insights \
    --location eastus \
    --resource-group mcp-extractor-rg
```

**Benefits:**
- Track request rates and response times
- Monitor errors and exceptions
- View dependency calls
- Custom metrics and logs

### View Logs
```bash
# Container Apps
az containerapp logs show --name <app> --resource-group <rg>

# App Service
az webapp log tail --name <app> --resource-group <rg>
```

---

## Scaling Configuration

### Container Apps - Auto-scaling
```yaml
scale:
  minReplicas: 0  # Scale to zero
  maxReplicas: 10
  rules:
  - name: http-rule
    http:
      metadata:
        concurrentRequests: "10"
```

### App Service - Scaling
```bash
# Scale up (more CPU/RAM)
az appservice plan update --name <plan> --resource-group <rg> --sku P1V2

# Scale out (more instances)
az appservice plan update --name <plan> --resource-group <rg> --number-of-workers 3
```

---

## Cost Optimization

### Container Apps
- **Scale to zero**: Enable for dev/test environments
- **Right-size resources**: Start with 0.5 vCPU, 1GB RAM
- **Use consumption plan**: Pay only for execution time

### App Service
- **Use B1 tier** for development ($13/month)
- **Use P1V2 tier** for production ($80/month)
- **Enable auto-shutdown** for dev environments

---

## Deployment Files Provided

We've created the following deployment files for you:

1. **`Dockerfile`** - Container image definition
2. **`.dockerignore`** - Exclude unnecessary files
3. **`deploy/deploy-azure-container-apps.ps1`** - Automated Container Apps deployment
4. **`deploy/deploy-azure-app-service.ps1`** - Automated App Service deployment
5. **`deploy/azure-pipelines.yml`** - CI/CD pipeline (Azure DevOps)
6. **`deploy/github-actions.yml`** - CI/CD pipeline (GitHub Actions)

---

## Next Steps

1. ✅ **Choose deployment option** (we recommend Container Apps)
2. ✅ **Review deployment script** for your chosen option
3. ✅ **Run deployment script** with your Azure subscription
4. ✅ **Test deployed endpoints** using test scripts
5. ✅ **Update Power Automate** flows with new Azure URL
6. ✅ **Set up monitoring** with Application Insights
7. ✅ **Configure authentication** for production use

---

## Getting Help

- **Azure Container Apps docs**: https://learn.microsoft.com/azure/container-apps/
- **Azure App Service docs**: https://learn.microsoft.com/azure/app-service/
- **Deployment issues**: Check deployment logs in Azure Portal
- **Runtime issues**: Enable Application Insights for debugging
