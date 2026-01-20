# HTTP MCP Server Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Client                               │
│                    (e.g., Claude Desktop)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ HTTP/SSE
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HTTP Server (Port 8000)                       │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Starlette Web Application                     │  │
│  │                                                             │  │
│  │  Routes:                                                   │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │  GET  /sse      → handle_sse()                       │ │  │
│  │  │  POST /messages → handle_messages()                  │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └────────────────────────┬──────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           SSE Server Transport Handler                     │  │
│  │         (SseServerTransport)                              │  │
│  └────────────────────────┬──────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              MCP Server Core                              │  │
│  │                                                            │  │
│  │  - Tool Registry                                          │  │
│  │  - Request Handler                                        │  │
│  │  - Response Formatter                                     │  │
│  └────────────────────────┬──────────────────────────────────┘  │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────┐
         │      Document Extraction Tools           │
         │                                           │
         │  • extract_document_images               │
         │  • get_document_info                     │
         │  • list_supported_formats                │
         │  • validate_document                     │
         └──────────────────┬───────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────┐
         │     Document Processing Layer            │
         │                                           │
         │  • PDFImageExtractor (PyMuPDF)          │
         │  • WordImageExtractor (zipfile)         │
         │  • FileUtils (file operations)          │
         └──────────────────┬───────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────┐
         │         File System                      │
         │                                           │
         │  • PDF Documents (.pdf)                  │
         │  • Word Documents (.docx)                │
         │  • Extracted Images (.png)               │
         │  • ZIP Archives (.zip)                   │
         └──────────────────────────────────────────┘
```

## Communication Flow

### 1. Initial Connection
```
Client                    Server
  │                         │
  ├─── GET /sse ──────────►│
  │                         │
  │◄─── SSE Stream ────────┤
  │    (Connection Open)    │
```

### 2. Tool Invocation
```
Client                    Server
  │                         │
  ├─ POST /messages ──────►│
  │  {tool: "extract..."}   │
  │                         │
  │                         ├─► Process Document
  │                         │
  │                         ├─► Extract Images
  │                         │
  │◄─ SSE Event ───────────┤
  │  {result: [...]}        │
```

### 3. Multiple Requests
```
Client                    Server
  │                         │
  ├─ POST /messages ──────►│ (Request 1)
  │◄─ SSE Event ───────────┤
  │                         │
  ├─ POST /messages ──────►│ (Request 2)
  │◄─ SSE Event ───────────┤
  │                         │
  │    (Connection persists)
```

## Component Details

### Starlette Application
- **Purpose**: HTTP request routing and handling
- **Endpoints**:
  - `/sse`: SSE connection endpoint (long-lived)
  - `/messages`: POST endpoint for tool requests

### SSE Transport
- **Purpose**: Bidirectional communication over HTTP
- **Features**:
  - Streaming responses
  - Event-based messaging
  - Connection persistence

### MCP Server Core
- **Purpose**: Tool management and request processing
- **Responsibilities**:
  - Register and list available tools
  - Route tool calls to handlers
  - Format responses according to MCP protocol

### Document Tools
- **Purpose**: Image extraction from documents
- **Supported Formats**:
  - PDF (via PyMuPDF/fitz)
  - DOCX (via zipfile)

## Network Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Network Layer                        │
│                                                       │
│  Internet/LAN                                        │
│       │                                               │
│       ▼                                               │
│  ┌─────────────┐                                     │
│  │  Firewall   │ (Port 8000)                         │
│  └──────┬──────┘                                     │
│         │                                             │
│         ▼                                             │
│  ┌─────────────┐                                     │
│  │   Server    │ (0.0.0.0:8000)                      │
│  │  Listening  │                                     │
│  └──────┬──────┘                                     │
│         │                                             │
│    ┌────┴────┐                                       │
│    ▼         ▼                                       │
│  Local    Remote                                     │
│  Client   Client                                     │
└──────────────────────────────────────────────────────┘
```

## Data Flow Example

### Extract Images from PDF

```
1. Client Request
   POST /messages
   {
     "tool": "extract_document_images",
     "arguments": {
       "document_path": "C:/docs/sample.pdf",
       "min_image_size": 10
     }
   }

2. Server Processing
   ├─► Validate file exists
   ├─► Open PDF with PyMuPDF
   ├─► Iterate through pages
   ├─► Extract images (filter by size)
   ├─► Save images as PNG files
   ├─► Create ZIP archive
   └─► Format response

3. Server Response (via SSE)
   {
     "status": "success",
     "extracted_images": 5,
     "image_files": ["page_1_image_1.png", ...],
     "zip_file": "sample_Document_and_Images.zip"
   }
```

## Deployment Scenarios

### Local Development
```
Server: localhost:8000
Client: localhost
Network: 127.0.0.1
```

### LAN Deployment
```
Server: 192.168.1.100:8000
Client: 192.168.1.x
Network: Private LAN
```

### Remote Deployment
```
Server: example.com:8000 (HTTPS recommended)
Client: Internet
Network: Public (use authentication!)
```

## Security Layers

```
┌────────────────────────────────────────┐
│         Application Layer              │
│  • Input validation                    │
│  • File path sanitization              │
│  • Error handling                      │
└──────────────┬─────────────────────────┘
               │
┌──────────────▼─────────────────────────┐
│         Transport Layer                │
│  • HTTPS (recommended for production)  │
│  • Authentication (to be implemented)  │
│  • Rate limiting (to be implemented)   │
└──────────────┬─────────────────────────┘
               │
┌──────────────▼─────────────────────────┐
│         Network Layer                  │
│  • Firewall rules                      │
│  • Port restrictions                   │
│  • IP whitelisting (optional)          │
└────────────────────────────────────────┘
```
