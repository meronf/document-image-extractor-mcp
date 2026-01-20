# Base64 Document Upload - Architecture

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Side                              │
│                                                                   │
│  ┌────────────────┐                                             │
│  │  PDF Document  │                                             │
│  │   (Binary)     │                                             │
│  └────────┬───────┘                                             │
│           │                                                      │
│           │ Read binary data                                    │
│           ▼                                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         base64.b64encode()                              │    │
│  │  Binary → Base64 String                                │    │
│  └────────┬───────────────────────────────────────────────┘    │
│           │                                                      │
│           │ "JVBERi0xLjQKJe..."                                │
│           │                                                      │
└───────────┼──────────────────────────────────────────────────────┘
            │
            │ HTTP POST
            │ {tool: "extract_document_images_base64",
            │  arguments: {document_base64: "...", ...}}
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Server Side                              │
│                      (MCP HTTP Server)                           │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Step 1: Receive Base64 String                           │  │
│  │  - Validate document_name extension                       │  │
│  │  - Create temporary directory                             │  │
│  └────────┬──────────────────────────────────────────────────┘  │
│           │                                                      │
│           ▼                                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Step 2: Decode to Temporary File                         │  │
│  │  - base64.b64decode()                                     │  │
│  │  - Save to /tmp/mcp_doc_extract_<id>/document.pdf        │  │
│  └────────┬──────────────────────────────────────────────────┘  │
│           │                                                      │
│           ▼                                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Step 3: Extract Images (Existing Logic)                  │  │
│  │  - PDFImageExtractor or WordImageExtractor                │  │
│  │  - Save images to temp directory                          │  │
│  │  - Create ZIP archive                                     │  │
│  └────────┬──────────────────────────────────────────────────┘  │
│           │                                                      │
│           ▼                                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Step 4: Encode Results (if requested)                    │  │
│  │  - For each image: base64.b64encode()                     │  │
│  │  - Encode ZIP file: base64.b64encode()                    │  │
│  │  - Attach metadata (filename, mime_type)                  │  │
│  └────────┬──────────────────────────────────────────────────┘  │
│           │                                                      │
│           ▼                                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Step 5: Cleanup                                          │  │
│  │  - Delete temporary directory                             │  │
│  │  - shutil.rmtree(temp_dir)                               │  │
│  └────────┬──────────────────────────────────────────────────┘  │
│           │                                                      │
│           │ Response JSON                                       │
└───────────┼──────────────────────────────────────────────────────┘
            │
            │ HTTP Response (SSE)
            │ {status: "success",
            │  images_base64: [...],
            │  zip_base64: {...}}
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Client Side                              │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Receive Base64 Images                                    │  │
│  │  [{filename: "img1.png", base64: "..."}, ...]            │  │
│  └────────┬──────────────────────────────────────────────────┘  │
│           │                                                      │
│           │ Process as needed                                   │
│           ▼                                                      │
│  ┌─────────────────────┬─────────────────────┐                 │
│  │   Save to Disk      │   Display in UI     │                 │
│  │  base64.b64decode() │  <img src="data:    │                 │
│  │  Write to file      │  image/png;base64   │                 │
│  └─────────────────────┴─────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

## Sequence Diagram

```
Client                    MCP Server                  File System
  │                           │                             │
  │ 1. Read PDF file          │                             │
  ├──────────────────────────►│                             │
  │                           │                             │
  │ 2. Encode to base64       │                             │
  │    (client-side)          │                             │
  │                           │                             │
  │ 3. POST /messages         │                             │
  │    extract_document_      │                             │
  │    images_base64          │                             │
  ├──────────────────────────►│                             │
  │                           │                             │
  │                           │ 4. Create temp directory    │
  │                           ├────────────────────────────►│
  │                           │                             │
  │                           │ 5. Decode base64 to file    │
  │                           ├────────────────────────────►│
  │                           │    /tmp/mcp.../doc.pdf      │
  │                           │                             │
  │                           │ 6. Extract images           │
  │                           ├────────────────────────────►│
  │                           │    /tmp/mcp.../img1.png     │
  │                           │    /tmp/mcp.../img2.png     │
  │                           │                             │
  │                           │ 7. Create ZIP archive       │
  │                           ├────────────────────────────►│
  │                           │    /tmp/mcp.../archive.zip  │
  │                           │                             │
  │                           │ 8. Read extracted images    │
  │                           │◄────────────────────────────┤
  │                           │                             │
  │                           │ 9. Encode images to base64  │
  │                           │    (server-side)            │
  │                           │                             │
  │                           │ 10. Cleanup temp files      │
  │                           ├────────────────────────────►│
  │                           │     Delete /tmp/mcp.../     │
  │                           │                             │
  │ 11. Response with         │                             │
  │     base64 images         │                             │
  │◄──────────────────────────┤                             │
  │                           │                             │
  │ 12. Decode & use images   │                             │
  │     (client-side)         │                             │
  │                           │                             │
```

## Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                    Client Application                            │
│                                                                   │
│  ┌─────────────────┐         ┌──────────────────┐              │
│  │  File Reader    │────────►│  Base64 Encoder  │              │
│  │  (Browser/App)  │         │  (client-side)   │              │
│  └─────────────────┘         └─────────┬────────┘              │
│                                         │                        │
└─────────────────────────────────────────┼────────────────────────┘
                                          │
                                          │ Base64 String
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      HTTP Transport Layer                        │
│                      (Starlette + SSE)                           │
│                                                                   │
│  POST /messages                                                  │
│  Content-Type: application/json                                 │
│  Body: {tool: "extract_document_images_base64", args: {...}}   │
└─────────────────────────────────────────┬───────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Server Core                             │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Tool Handler: extract_document_images_base64            │   │
│  │                                                           │   │
│  │  1. Validate inputs                                      │   │
│  │  2. Call Base64Utils.decode_base64_to_file()            │   │
│  │  3. Call DocumentExtractor.extract_images()              │   │
│  │  4. Call Base64Utils.encode_file_to_base64()            │   │
│  │  5. Format response                                      │   │
│  │  6. Cleanup temporary files                              │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                              │
└───────────────────┼──────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Document Processing Layer                       │
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │ Base64Utils  │         │  Document    │                     │
│  │              │         │  Extractor   │                     │
│  │ • decode     │────────►│              │                     │
│  │ • encode     │◄────────│ • extract    │                     │
│  │ • mime type  │         │ • create zip │                     │
│  └──────────────┘         └──────┬───────┘                     │
│                                   │                              │
│                                   ▼                              │
│                          ┌────────────────┐                     │
│                          │ PDF/Word       │                     │
│                          │ Extractors     │                     │
│                          │                │                     │
│                          │ • PyMuPDF      │                     │
│                          │ • zipfile      │                     │
│                          └────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## File System Layout During Processing

```
/tmp/                                    (System temp directory)
  └── mcp_doc_extract_abc123/           (Unique temp directory)
      ├── report.pdf                    (Decoded document)
      ├── extracted_images/             (Output directory)
      │   ├── page_1_image_1.png       (Extracted image 1)
      │   ├── page_2_image_1.png       (Extracted image 2)
      │   └── page_3_image_1.png       (Extracted image 3)
      └── report_Document_and_Images.zip (ZIP archive)

After processing: Entire /tmp/mcp_doc_extract_abc123/ is deleted
```

## Memory Flow

```
Client Memory                Server Memory               File System
─────────────               ─────────────               ─────────────

PDF Binary                                              
(1 MB)                      
    │                       
    ▼                       
Base64 String               Base64 String               
(~1.33 MB)    ────────────► (~1.33 MB)                 
                                │                       
                                ▼                       
                            Decoded Binary              Temp PDF
                            (1 MB)        ─────────────► (1 MB)
                                                            │
                                                            ▼
                                                        Extract
                                                            │
                                                            ▼
                                                        Images
                                                        (100 KB each)
                                                            │
                            ┌───────────────────────────────┘
                            │
                            ▼
                        Image Binary                    
                        (100 KB)                        
                            │
                            ▼
                        Base64 Images                   
Base64 Images           (~133 KB each)                  
(~133 KB each) ◄────────                               
    │                                                   
    ▼                                                   
Display/Save                                            Cleanup
                                                        (Delete all)
```

## Comparison: File Path vs Base64 Architecture

### File Path Method
```
Client ──(file_path)──► Server
                          │
                          ▼
                    Read from FS
                          │
                          ▼
                       Extract
                          │
                          ▼
                    Write to FS
                          │
                          ▼
Client ◄──(file_paths)─── Server
```

### Base64 Method
```
Client ──(base64)──► Server
                       │
                       ▼
                  Decode to Temp
                       │
                       ▼
                    Extract
                       │
                       ▼
                  Encode Result
                       │
                       ▼
                     Cleanup
                       │
                       ▼
Client ◄──(base64)─── Server
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      Input Validation                        │
│  • Check document_name has valid extension (.pdf/.docx)     │
│  • Validate base64 format (with data URL prefix handling)   │
│  • Check for required parameters                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Isolated Processing                        │
│  • Unique temporary directory per request                   │
│  • No access to other temp directories                      │
│  • Processing in sandboxed temp location                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Automatic Cleanup                          │
│  • try/finally ensures cleanup even on error                │
│  • Complete directory removal (shutil.rmtree)               │
│  • No leftover files in temp storage                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            Recommendations for Production                    │
│  • Add size limits (e.g., max 10MB base64 input)           │
│  • Implement rate limiting per client                       │
│  • Add authentication/authorization                         │
│  • Monitor temp directory usage                             │
│  • Log all operations for audit                             │
└─────────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### Request Size
- Original PDF: 1 MB
- Base64 encoded: ~1.33 MB (+33% overhead)
- Network transfer: 1.33 MB uploaded

### Response Size
- 3 images × 100 KB = 300 KB binary
- Base64 encoded: 3 × ~133 KB = 399 KB
- ZIP file: ~150 KB → ~200 KB base64
- Total response: ~600 KB

### Processing Time
1. **Base64 decode**: ~10ms (1 MB)
2. **Extract images**: ~500ms (PDF-dependent)
3. **Create ZIP**: ~100ms
4. **Base64 encode**: ~30ms (300 KB images)
5. **Cleanup**: ~50ms
**Total**: ~700ms for typical document

### Memory Usage
- Input base64 string: ~1.33 MB
- Decoded document: 1 MB
- Extracted images: ~300 KB
- Response JSON: ~600 KB
**Peak memory**: ~2-3 MB per request

## Summary

The base64 upload architecture provides:
- ✅ Clean separation of concerns
- ✅ Automatic resource management
- ✅ Isolated processing per request
- ✅ Efficient memory usage
- ✅ Complete cleanup guarantees
- ✅ HTTP-friendly design
