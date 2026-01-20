# REST API Architecture for Power Automate

## HTTP Endpoints Overview

```
┌─────────────────────────────────────────────────────────────────┐
│           MCP Server (Port 8000)                                 │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              MCP Protocol Endpoints                        │ │
│  │                                                             │ │
│  │  GET  /sse        → SSE connection for MCP clients        │ │
│  │  POST /messages   → MCP protocol messages                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              REST API Endpoints (NEW)                      │ │
│  │                                                             │ │
│  │  GET  /api/health           → Health check                │ │
│  │  POST /api/extract-base64   → Extract images (REST)       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Power Automate Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Power Automate Flow                          │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Trigger                                                   │  │
│  │  • SharePoint file created                                │  │
│  │  • OneDrive file added                                    │  │
│  │  • Email with attachment                                  │  │
│  │  • Manual trigger                                         │  │
│  └────────────────────┬──────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Get File Content                                         │  │
│  │  → Returns binary file content                            │  │
│  └────────────────────┬──────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Compose: base64()                                        │  │
│  │  → base64(body('Get_file_content'))                       │  │
│  └────────────────────┬──────────────────────────────────────┘  │
│                       │                                          │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        │ HTTP POST
                        │ Base64 document data
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MCP Server (REST API)                           │
│                                                                   │
│  POST /api/extract-base64                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Request Body:                                            │  │
│  │  {                                                        │  │
│  │    "document_base64": "<base64_string>",                 │  │
│  │    "document_name": "invoice.pdf",                       │  │
│  │    "return_images_as_base64": true                       │  │
│  │  }                                                        │  │
│  └────────────────────┬──────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Process Document                                         │  │
│  │  1. Decode base64 → temp file                            │  │
│  │  2. Extract images (PDF/DOCX)                            │  │
│  │  3. Create ZIP archive                                   │  │
│  │  4. Encode results to base64                             │  │
│  │  5. Cleanup temp files                                   │  │
│  └────────────────────┬──────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Response Body:                                           │  │
│  │  {                                                        │  │
│  │    "status": "success",                                  │  │
│  │    "extracted_images_count": 3,                          │  │
│  │    "images": [                                           │  │
│  │      {                                                   │  │
│  │        "filename": "page_1_image_1.png",                │  │
│  │        "mime_type": "image/png",                        │  │
│  │        "base64": "<image_data>"                         │  │
│  │      }                                                   │  │
│  │    ],                                                    │  │
│  │    "zip": {...}                                          │  │
│  │  }                                                        │  │
│  └────────────────────┬──────────────────────────────────────┘  │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        │ HTTP Response
                        │ JSON with base64 images
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Power Automate Flow                          │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Parse JSON                                               │  │
│  │  → Extract structured data from response                 │  │
│  └────────────────────┬──────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Apply to Each: images                                    │  │
│  │                                                            │  │
│  │  For each image:                                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Convert: base64ToBinary()                         │  │  │
│  │  │  → Decode base64 back to binary                    │  │  │
│  │  └──────────────────┬─────────────────────────────────┘  │  │
│  │                     │                                      │  │
│  │                     ▼                                      │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Action (Choose one):                              │  │  │
│  │  │  • Save to SharePoint                              │  │  │
│  │  │  • Save to OneDrive                                │  │  │
│  │  │  • Upload to Azure Blob                            │  │  │
│  │  │  • Send via email                                  │  │  │
│  │  │  • Store in database                               │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Comparison

### Traditional File Path Method
```
Power Automate                     MCP Server
     │                                  │
     │  File path reference            │
     ├─────────────────────────────────►│
     │                                  │
     │                                  ├─ Read from file system
     │                                  │
     │                                  ├─ Extract images
     │                                  │
     │                                  ├─ Write to file system
     │                                  │
     │  File paths                     │
     ◄─────────────────────────────────┤
     │                                  │
     └─ Access files on shared drive
```
❌ **Problem:** Requires shared file system

### New REST API Method (Base64)
```
Power Automate                     MCP Server
     │                                  │
     │  File binary                    │
     ├─ Read file                      │
     │                                  │
     │  Base64 string                  │
     ├─────────────────────────────────►│
     │                                  │
     │                                  ├─ Decode to temp file
     │                                  │
     │                                  ├─ Extract images
     │                                  │
     │                                  ├─ Encode to base64
     │                                  │
     │                                  ├─ Cleanup temp files
     │                                  │
     │  Base64 images                  │
     ◄─────────────────────────────────┤
     │                                  │
     ├─ Decode base64                  │
     │                                  │
     └─ Save anywhere
```
✅ **Solution:** No shared file system needed!

## REST API Request/Response Format

### Request Format
```json
POST /api/extract-base64
Content-Type: application/json

{
  "document_base64": "JVBERi0xLjQKJe...",
  "document_name": "invoice.pdf",
  "min_image_size": 10,
  "return_images_as_base64": true
}
```

### Response Format
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "document_name": "invoice.pdf",
  "extracted_images_count": 3,
  "image_files": [
    "page_1_image_1.png",
    "page_2_image_1.png",
    "page_3_image_1.png"
  ],
  "images": [
    {
      "filename": "page_1_image_1.png",
      "mime_type": "image/png",
      "base64": "iVBORw0KGgoAAAANSUhEU..."
    },
    {
      "filename": "page_2_image_1.png",
      "mime_type": "image/png",
      "base64": "iVBORw0KGgoAAAANSUhEU..."
    },
    {
      "filename": "page_3_image_1.png",
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

## Power Automate Actions Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│  Power Automate Action       →  Purpose                         │
├─────────────────────────────────────────────────────────────────┤
│  Get file content            →  Get binary document             │
│  Compose                     →  Convert to base64               │
│  HTTP (POST)                 →  Call REST API                   │
│  Parse JSON                  →  Structure response data         │
│  Apply to each               →  Loop through images             │
│  base64ToBinary()            →  Convert image to binary         │
│  Create file (SharePoint)    →  Save image                      │
│  Create file (OneDrive)      →  Save image                      │
│  Send email (V2)             →  Email with attachments          │
│  Create blob (Azure)         →  Upload to cloud storage         │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
Power Automate                     MCP Server
     │                                  │
     │  Request                         │
     ├─────────────────────────────────►│
     │                                  │
     │                                  ├─ Validate request
     │                                  │
     │                                  ├─ Check file type
     │                                  │
     │                                  ├─ Process document
     │                                  │
     │                                  └─ Any errors?
     │                                     │
     │                                     ├─ Yes → Error response
     │  Error (400/500)                   │
     ◄────────────────────────────────────┘
     │  {"error": "message"}
     │
     ├─ Catch error
     │
     ├─ Log error
     │
     └─ Send notification/retry
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Security Layers                           │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Network Layer                                            │  │
│  │  • Firewall rules (port 8000)                            │  │
│  │  • VPN/Private network                                   │  │
│  │  • IP whitelisting                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Transport Layer                                          │  │
│  │  • HTTPS (recommended)                                   │  │
│  │  • TLS 1.2+                                              │  │
│  │  • Certificate validation                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Authentication Layer (to be added)                      │  │
│  │  • API key validation                                    │  │
│  │  • OAuth 2.0                                             │  │
│  │  • Azure AD integration                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Application Layer                                        │  │
│  │  • Input validation                                      │  │
│  │  • File type checking                                    │  │
│  │  • Size limits                                           │  │
│  │  • Rate limiting                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Processing Layer                                         │  │
│  │  • Isolated temp directories                             │  │
│  │  • Automatic cleanup                                     │  │
│  │  • Error handling                                        │  │
│  │  • Logging                                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### Request Size
```
Original PDF: 1 MB
    ↓ base64 encode (+33%)
Base64 string: 1.33 MB
    ↓ HTTP POST
Server receives: 1.33 MB
```

### Response Size
```
Extracted images: 3 × 100 KB = 300 KB
    ↓ base64 encode (+33%)
Base64 images: 3 × 133 KB = 399 KB

ZIP archive: 150 KB
    ↓ base64 encode (+33%)
Base64 ZIP: 200 KB

Total response: ~600 KB
```

### Processing Time
```
HTTP Request           : ~10 ms
Base64 Decode         : ~20 ms
Extract Images (PDF)  : ~500 ms
Create ZIP           : ~100 ms
Base64 Encode Results: ~30 ms
HTTP Response        : ~10 ms
Cleanup              : ~50 ms
─────────────────────────────
Total                : ~720 ms
```

## Scalability Options

### Horizontal Scaling
```
┌──────────────┐
│ Power        │
│ Automate     │
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌─────────────┐
│ Load         │────►│ MCP Server 1│
│ Balancer     │     └─────────────┘
│ (nginx)      │     ┌─────────────┐
│              │────►│ MCP Server 2│
└──────────────┘     └─────────────┘
                     ┌─────────────┐
                    ►│ MCP Server 3│
                     └─────────────┘
```

### Vertical Scaling
```
┌─────────────────────────────────┐
│  Increase server resources:     │
│  • More CPU cores               │
│  • More RAM                     │
│  • Faster disk I/O              │
│  • SSD storage                  │
└─────────────────────────────────┘
```

## Summary

The REST API provides:
- ✅ Simple HTTP interface for Power Automate
- ✅ No shared file system required
- ✅ Base64 encoding for easy data transfer
- ✅ Clean JSON request/response format
- ✅ Automatic resource cleanup
- ✅ Comprehensive error handling
- ✅ Easy to test and debug
- ✅ Production-ready architecture
