# Power Automate Integration Guide

## Overview

The Document Image Extractor MCP server now includes **REST API endpoints** specifically designed for Power Automate and other HTTP clients. You can extract images from PDF/Word documents directly from your Power Automate flows!

## Quick Start

### Endpoint URL
```
POST http://your-server:8000/api/extract-base64
```

### Simple Example Request
```json
{
  "document_base64": "<your_base64_encoded_document>",
  "document_name": "invoice.pdf",
  "min_image_size": 10,
  "return_images_as_base64": true
}
```

### Simple Example Response
```json
{
  "status": "success",
  "document_name": "invoice.pdf",
  "extracted_images_count": 3,
  "image_files": ["page_1_image_1.png", "page_2_image_1.png", "page_3_image_1.png"],
  "images": [
    {
      "filename": "page_1_image_1.png",
      "mime_type": "image/png",
      "base64": "iVBORw0KGgoAAAANSUhEU..."
    }
  ],
  "zip": {
    "filename": "invoice_Document_and_Images.zip",
    "mime_type": "application/zip",
    "base64": "UEsDBBQAAAAIAA..."
  }
}
```

## Power Automate Flow Setup

### Flow Structure

```
┌─────────────────────────────────────────────┐
│  1. Trigger (e.g., File added to SharePoint)│
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  2. Get File Content                        │
│     (Binary content of PDF/DOCX)            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  3. Compose - Convert to Base64             │
│     base64(body('Get_file_content'))        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  4. HTTP - Extract Images                   │
│     POST /api/extract-base64                │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  5. Parse JSON Response                     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  6. Apply to Each Image                     │
│     - Save to SharePoint/OneDrive           │
│     - Send email                            │
│     - Further processing                    │
└─────────────────────────────────────────────┘
```

### Step-by-Step Configuration

#### Step 1: Trigger
Choose any trigger that provides a file:
- **SharePoint:** "When a file is created"
- **OneDrive:** "When a file is created"
- **Email:** "When a new email arrives" (with attachments)
- **Manual trigger:** "Manually trigger a flow" (with file input)

#### Step 2: Get File Content
Action: **Get file content**
- **Site Address:** Your SharePoint site
- **File Identifier:** Use dynamic content from trigger

#### Step 3: Compose Base64
Action: **Compose**
- **Inputs:** `base64(body('Get_file_content'))`

This converts the binary file to base64 string.

#### Step 4: HTTP Request
Action: **HTTP**

**Method:** `POST`

**URI:** `http://YOUR-SERVER-IP:8000/api/extract-base64`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "document_base64": @{outputs('Compose_Base64')},
  "document_name": @{triggerOutputs()?['body/{FilenameWithExtension}']},
  "min_image_size": 10,
  "return_images_as_base64": true
}
```

> **Note:** Replace `YOUR-SERVER-IP` with your actual server IP address or hostname.

#### Step 5: Parse JSON Response
Action: **Parse JSON**

**Content:** `body('HTTP')`

**Schema:**
```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string"
    },
    "document_name": {
      "type": "string"
    },
    "extracted_images_count": {
      "type": "integer"
    },
    "image_files": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "images": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "filename": {
            "type": "string"
          },
          "mime_type": {
            "type": "string"
          },
          "base64": {
            "type": "string"
          }
        }
      }
    },
    "zip": {
      "type": "object",
      "properties": {
        "filename": {
          "type": "string"
        },
        "mime_type": {
          "type": "string"
        },
        "base64": {
          "type": "string"
        }
      }
    }
  }
}
```

#### Step 6: Apply to Each Image
Action: **Apply to each**

**Select an output from previous steps:** `body('Parse_JSON')?['images']`

Inside the loop, you can:

##### Option A: Save to SharePoint
Action: **Create file**
- **Site Address:** Your SharePoint site
- **Folder Path:** Target folder
- **File Name:** `items('Apply_to_each')?['filename']`
- **File Content:** `base64ToBinary(items('Apply_to_each')?['base64'])`

##### Option B: Save to OneDrive
Action: **Create file**
- **Folder Path:** Target folder
- **File Name:** `items('Apply_to_each')?['filename']`
- **File Content:** `base64ToBinary(items('Apply_to_each')?['base64'])`

##### Option C: Send Email with Attachments
Action: **Send an email (V2)**
- **To:** Recipient email
- **Subject:** "Extracted Images"
- **Attachments Name:** `items('Apply_to_each')?['filename']`
- **Attachments Content:** `base64ToBinary(items('Apply_to_each')?['base64'])`

## Complete Flow Examples

### Example 1: SharePoint PDF → Extract Images → Save to Folder

```
Trigger: When a file is created (SharePoint)
   ├─ Site: https://yourcompany.sharepoint.com/sites/Documents
   └─ Folder: /Shared Documents/Invoices

↓

Get file content
   └─ File Identifier: ID from trigger

↓

Compose: Base64
   └─ Inputs: base64(body('Get_file_content'))

↓

HTTP: Extract Images
   ├─ Method: POST
   ├─ URI: http://192.168.1.100:8000/api/extract-base64
   └─ Body: {
         "document_base64": @{outputs('Compose_Base64')},
         "document_name": @{triggerOutputs()?['body/{FilenameWithExtension}']},
         "return_images_as_base64": true
       }

↓

Parse JSON
   └─ Content: body('HTTP')

↓

Apply to each: body('Parse_JSON')?['images']
   └─ Create file (SharePoint)
       ├─ Folder: /Shared Documents/Extracted Images
       ├─ File Name: items('Apply_to_each')?['filename']
       └─ File Content: base64ToBinary(items('Apply_to_each')?['base64'])
```

### Example 2: Email Attachment → Extract → Send Results

```
Trigger: When a new email arrives (V3)
   └─ Has Attachments: Yes

↓

Apply to each: Attachments
   
   ├─ Condition: ends with '.pdf' or '.docx'
   
   └─ HTTP: Extract Images
       ├─ Method: POST
       ├─ URI: http://192.168.1.100:8000/api/extract-base64
       └─ Body: {
             "document_base64": @{base64(items('Apply_to_each')?['contentBytes'])},
             "document_name": @{items('Apply_to_each')?['name']},
             "return_images_as_base64": true
           }
   
   └─ Parse JSON
   
   └─ Send email with extracted images
```

### Example 3: OneDrive → Extract → Azure Blob Storage

```
Trigger: When a file is created (OneDrive)

↓

Get file content

↓

Compose: Base64

↓

HTTP: Extract Images

↓

Parse JSON

↓

Apply to each: Images
   └─ Create blob (Azure Blob Storage)
       ├─ Storage account: Your account
       ├─ Container: extracted-images
       ├─ Blob name: items('Apply_to_each')?['filename']
       └─ Blob content: base64ToBinary(items('Apply_to_each')?['base64'])
```

## API Reference

### POST /api/extract-base64

Extract images from a base64-encoded document.

**Request Body Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `document_base64` | string | ✅ Yes | - | Base64-encoded PDF or DOCX document |
| `document_name` | string | ✅ Yes | - | Original filename with extension |
| `min_image_size` | integer | No | 10 | Minimum image dimension (PDF only) |
| `return_images_as_base64` | boolean | No | true | Return images as base64 strings |

**Success Response (200):**

```json
{
  "status": "success",
  "document_name": "document.pdf",
  "extracted_images_count": 3,
  "image_files": ["page_1_image_1.png", "page_2_image_1.png", "page_3_image_1.png"],
  "images": [
    {
      "filename": "page_1_image_1.png",
      "mime_type": "image/png",
      "base64": "<base64_data>"
    }
  ],
  "zip": {
    "filename": "document_Document_and_Images.zip",
    "mime_type": "application/zip",
    "base64": "<base64_data>"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "error": "document_base64 is required"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Error message details"
}
```

### GET /api/health

Health check endpoint to verify server is running.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "document-image-extractor-mcp",
  "version": "0.1.0",
  "endpoints": {
    "mcp_sse": "/sse",
    "mcp_messages": "/messages",
    "rest_extract_base64": "/api/extract-base64",
    "rest_health": "/api/health"
  }
}
```

## Testing with Power Automate

### Test with Manual Trigger

1. Create a new flow with **Manually trigger a flow**
2. Add file input: Click **+ Add an input** → **File**
3. Follow the steps above using `triggerBody()['file']` for content
4. Test with a sample PDF or DOCX file

### Test with HTTP Tool (PowerShell)

```powershell
# First, encode a test document
$fileContent = [System.IO.File]::ReadAllBytes("C:\test.pdf")
$base64String = [System.Convert]::ToBase64String($fileContent)

# Create request body
$body = @{
    document_base64 = $base64String
    document_name = "test.pdf"
    min_image_size = 10
    return_images_as_base64 = $true
} | ConvertTo-Json

# Make request
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/extract-base64" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# View results
$response | ConvertTo-Json -Depth 10
```

## Common Use Cases

### 1. Invoice Processing
**Flow:** SharePoint invoice uploads → Extract images → OCR processing → Store results

### 2. Document Archival
**Flow:** Email attachments → Extract images → Store in Azure Blob → Archive original

### 3. Image Extraction Service
**Flow:** OneDrive upload → Extract → Share extracted images → Notify user

### 4. Automated Reporting
**Flow:** Daily PDF reports → Extract charts/graphs → Upload to Power BI → Send summary

### 5. Legal Document Processing
**Flow:** Case documents → Extract exhibits → Organize by case number → Store

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to server
**Solution:** 
- Verify server is running: `http://server:8000/api/health`
- Check firewall rules allow port 8000
- Ensure server IP is accessible from Power Automate

### Large Documents

**Problem:** Timeout on large PDFs
**Solution:**
- Increase HTTP action timeout in Power Automate
- Consider splitting large documents
- Process in batches

### Base64 Encoding

**Problem:** Invalid base64 error
**Solution:**
- Use `base64(body('Get_file_content'))` exactly
- Ensure file content is binary, not text
- Check file is not corrupted

### Memory Issues

**Problem:** Server runs out of memory
**Solution:**
- Process documents sequentially, not in parallel
- Restart server periodically
- Consider document size limits

## Security Considerations

### For Production

1. **HTTPS:** Use HTTPS instead of HTTP
   ```
   https://your-server.com:443/api/extract-base64
   ```

2. **Authentication:** Add API key authentication
   ```json
   Headers: {
     "Authorization": "Bearer YOUR-API-KEY"
   }
   ```

3. **Network:** Use VPN or private network
   - Don't expose server to public internet
   - Use Azure Virtual Network if hosted in Azure

4. **Size Limits:** Implement document size restrictions
   - Reject files over 10 MB
   - Prevent abuse and resource exhaustion

## Performance Tips

### Optimize Flow Performance

1. **Parallel Processing:** For multiple documents, use parallel branches
2. **Error Handling:** Add try-catch scopes for robustness
3. **Logging:** Add actions to log start/end times
4. **Notifications:** Send notifications only on failure

### Server Performance

1. **Keep server close to Power Automate:** Same region/network
2. **Monitor resources:** CPU, memory, disk space
3. **Regular restarts:** Schedule weekly restarts if needed
4. **Scaling:** Consider multiple server instances for high volume

## Cost Considerations

### Power Automate Actions

- **HTTP action:** Standard action, counts toward limits
- **Parse JSON:** Standard action
- **Apply to each:** Counts as one action per iteration
- **File operations:** Standard actions

**Tip:** Use Power Automate Premium for unlimited actions in high-volume scenarios.

## Next Steps

1. ✅ Start the server: `document-image-extractor-mcp`
2. ✅ Test health endpoint: `http://your-server:8000/api/health`
3. ✅ Create a test flow in Power Automate
4. ✅ Test with sample PDF/DOCX documents
5. ✅ Deploy to production with security measures

## Support

For issues or questions:
- Check server logs for errors
- Test with PowerShell script first
- Verify JSON schema in Parse JSON action
- Use Power Automate's test feature to debug

---

🎉 **You're now ready to extract images from documents in Power Automate!**
