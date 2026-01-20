# Base64 Document Upload - User Guide

## Overview

The Document Image Extractor MCP server now supports **base64-encoded document uploads**. This feature is perfect for HTTP/remote scenarios where the client and server don't share the same file system.

## Why Base64 Support?

### Before (File Path Only)
- ❌ Client and server must share file system
- ❌ Limited to local or network drive access
- ❌ Not suitable for web-based clients

### After (Base64 Support Added)
- ✅ Works over pure HTTP without file system access
- ✅ Perfect for remote clients and web applications
- ✅ Images can be returned as base64 for immediate use
- ✅ No file system dependencies between client and server

## Two Methods Available

### Method 1: File Path (Original)
**Tool:** `extract_document_images`

```json
{
  "tool": "extract_document_images",
  "arguments": {
    "document_path": "C:/Documents/report.pdf",
    "output_dir": "C:/Output",
    "min_image_size": 10
  }
}
```

**Use when:**
- Server has direct access to document files
- Working with local file system or network drives
- Documents are already on the server

---

### Method 2: Base64 Upload (New)
**Tool:** `extract_document_images_base64`

```json
{
  "tool": "extract_document_images_base64",
  "arguments": {
    "document_base64": "<base64_encoded_document_data>",
    "document_name": "report.pdf",
    "min_image_size": 10,
    "return_images_as_base64": true
  }
}
```

**Use when:**
- Client is on a different machine than server
- Working with web-based applications
- Documents need to be uploaded to the server
- Want images returned as base64 for immediate use

## Using Base64 Upload

### Step 1: Encode Your Document

**Python Example:**
```python
import base64

def encode_document(file_path):
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

# Encode a PDF
pdf_base64 = encode_document("report.pdf")
```

**JavaScript Example:**
```javascript
async function encodeDocument(file) {
    const buffer = await file.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    return btoa(String.fromCharCode(...bytes));
}

// In a web app with file input
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];
const base64Data = await encodeDocument(file);
```

**PowerShell Example:**
```powershell
# Read and encode file to base64
$fileContent = [System.IO.File]::ReadAllBytes("C:\Documents\report.pdf")
$base64String = [System.Convert]::ToBase64String($fileContent)
```

### Step 2: Call the MCP Tool

**Full Example:**
```json
{
  "tool": "extract_document_images_base64",
  "arguments": {
    "document_base64": "JVBERi0xLjQKJeLjz9MKNCAwIG9iago8PC...",
    "document_name": "report.pdf",
    "min_image_size": 10,
    "return_images_as_base64": true
  }
}
```

### Step 3: Receive Extracted Images

**Response Structure:**
```json
{
  "status": "success",
  "document_name": "report.pdf",
  "extracted_images": 3,
  "image_files": [
    "page_1_image_1.png",
    "page_2_image_1.png",
    "page_3_image_1.png"
  ],
  "images_base64": [
    {
      "filename": "page_1_image_1.png",
      "mime_type": "image/png",
      "base64": "iVBORw0KGgoAAAANSUhEUgAA..."
    },
    {
      "filename": "page_2_image_1.png",
      "mime_type": "image/png",
      "base64": "iVBORw0KGgoAAAANSUhEUgAA..."
    },
    {
      "filename": "page_3_image_1.png",
      "mime_type": "image/png",
      "base64": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  ],
  "zip_base64": {
    "filename": "report_Document_and_Images.zip",
    "mime_type": "application/zip",
    "base64": "UEsDBBQAAAAIAKB+..."
  }
}
```

### Step 4: Decode Images (if needed)

**Python Example:**
```python
import base64

def save_base64_image(base64_data, output_path):
    image_data = base64.b64decode(base64_data)
    with open(output_path, 'wb') as f:
        f.write(image_data)

# Save each image
for img in response['images_base64']:
    save_base64_image(img['base64'], img['filename'])
```

**JavaScript Example:**
```javascript
function downloadBase64Image(base64Data, filename) {
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${base64Data}`;
    link.download = filename;
    link.click();
}

// Download each image
response.images_base64.forEach(img => {
    downloadBase64Image(img.base64, img.filename);
});
```

## Tool Parameters

### `extract_document_images_base64`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_base64` | string | ✅ Yes | Base64-encoded document data (PDF or DOCX) |
| `document_name` | string | ✅ Yes | Original filename with extension (e.g., 'report.pdf') |
| `min_image_size` | integer | No | Minimum image dimension for filtering (default: 10) |
| `return_images_as_base64` | boolean | No | Return images as base64 (true) or file paths (false). Default: true |

## Return Options

### Option 1: Return as Base64 (default)
```json
{
  "return_images_as_base64": true
}
```

**Returns:**
- `images_base64[]` - Array of base64-encoded images with metadata
- `zip_base64` - Base64-encoded ZIP archive with all files
- Perfect for web applications and immediate display

### Option 2: Return as File Paths
```json
{
  "return_images_as_base64": false
}
```

**Returns:**
- `output_directory` - Path where images were saved
- `full_paths[]` - Array of file paths to extracted images
- `zip_file` - Path to ZIP archive
- Useful when server wants to keep files temporarily

## Use Cases

### 1. Web Application Upload
```javascript
// User uploads document via web form
async function extractImagesFromUpload(file) {
    const base64 = await encodeFile(file);
    
    const response = await mcpClient.callTool({
        tool: 'extract_document_images_base64',
        arguments: {
            document_base64: base64,
            document_name: file.name,
            return_images_as_base64: true
        }
    });
    
    // Display images immediately
    response.images_base64.forEach(img => {
        const imgElement = document.createElement('img');
        imgElement.src = `data:${img.mime_type};base64,${img.base64}`;
        document.body.appendChild(imgElement);
    });
}
```

### 2. Remote API Integration
```python
import requests
import base64

def extract_images_via_api(pdf_path):
    # Encode document
    with open(pdf_path, 'rb') as f:
        pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Call MCP server via HTTP
    response = requests.post('http://remote-server:8000/messages', json={
        'tool': 'extract_document_images_base64',
        'arguments': {
            'document_base64': pdf_base64,
            'document_name': 'report.pdf',
            'return_images_as_base64': True
        }
    })
    
    # Process images
    result = response.json()
    for img in result['images_base64']:
        # Save or process each image
        save_image(img['base64'], img['filename'])
```

### 3. Automated Processing Pipeline
```python
def batch_process_documents(document_list):
    """Process multiple documents via base64 upload."""
    results = []
    
    for doc_path in document_list:
        # Encode document
        with open(doc_path, 'rb') as f:
            doc_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Extract images
        result = mcp_client.call_tool(
            'extract_document_images_base64',
            document_base64=doc_base64,
            document_name=os.path.basename(doc_path),
            return_images_as_base64=True
        )
        
        results.append(result)
    
    return results
```

## Comparison: File Path vs Base64

| Feature | File Path Method | Base64 Method |
|---------|------------------|---------------|
| **Network Transfer** | No document transfer | Document uploaded as base64 |
| **File System Access** | Required | Not required |
| **Remote Clients** | ❌ Difficult | ✅ Easy |
| **Web Applications** | ❌ Not suitable | ✅ Perfect fit |
| **Large Documents** | ✅ Efficient | ⚠️ Larger payload size |
| **Setup Complexity** | Simple (if shared FS) | Simple (HTTP only) |
| **Return Format** | File paths | Base64 or file paths |

## Performance Considerations

### Base64 Overhead
- Base64 encoding increases data size by ~33%
- A 1 MB PDF becomes ~1.33 MB when encoded
- Consider this for large documents over slow networks

### Recommendations
- **Small documents (<5 MB)**: Base64 method works great
- **Large documents (>10 MB)**: Consider file path method if possible
- **Many small documents**: Base64 is efficient
- **Few large documents**: File path is more efficient

## Data URL Format (Optional)

The tool accepts both plain base64 and data URL format:

**Plain base64:**
```
JVBERi0xLjQKJeLjz9MKNCAwIG9iago8PC...
```

**Data URL format:**
```
data:application/pdf;base64,JVBERi0xLjQKJeLjz9MKNCAwIG9iago8PC...
```

Both are automatically handled by the server.

## Security Notes

⚠️ **Important Security Considerations:**

1. **Size Limits**: Implement size limits on base64 uploads to prevent memory exhaustion
2. **Validation**: Server validates file type from extension, not content
3. **Cleanup**: Temporary files are automatically cleaned up after processing
4. **Rate Limiting**: Consider implementing rate limiting for base64 uploads
5. **Authentication**: Add authentication for production deployments

## Error Handling

### Common Errors

**Missing document_base64:**
```json
{
  "error": "document_base64 is required"
}
```

**Invalid file type:**
```json
{
  "error": "Unsupported file type: .txt. Supported types: .pdf, .docx"
}
```

**Invalid base64:**
```json
{
  "error": "Invalid base64 encoding"
}
```

**Decoding failure:**
```json
{
  "error": "Error extracting images from base64 document: <details>"
}
```

## Testing

Run the base64 extraction test:
```bash
python tests/test_base64_extraction.py
```

This demonstrates:
- How to encode documents
- Expected request format
- Response structure
- Decoding images

## Complete Example: Python Client

```python
import base64
import json
import requests

class MCPDocumentExtractor:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
    
    def encode_document(self, file_path):
        """Encode document file to base64."""
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def extract_images_base64(self, file_path, return_as_base64=True):
        """Extract images from document via base64 upload."""
        # Encode document
        doc_base64 = self.encode_document(file_path)
        doc_name = os.path.basename(file_path)
        
        # Call MCP tool
        response = requests.post(f"{self.server_url}/messages", json={
            'tool': 'extract_document_images_base64',
            'arguments': {
                'document_base64': doc_base64,
                'document_name': doc_name,
                'return_images_as_base64': return_as_base64
            }
        })
        
        return response.json()
    
    def save_base64_images(self, images_base64, output_dir):
        """Save base64-encoded images to directory."""
        os.makedirs(output_dir, exist_ok=True)
        
        for img in images_base64:
            output_path = os.path.join(output_dir, img['filename'])
            img_data = base64.b64decode(img['base64'])
            with open(output_path, 'wb') as f:
                f.write(img_data)
            print(f"Saved: {output_path}")

# Usage
client = MCPDocumentExtractor()
result = client.extract_images_base64('report.pdf')
client.save_base64_images(result['images_base64'], 'output/')
```

## Summary

The base64 upload feature enables:
- ✅ Document upload without shared file system
- ✅ Perfect for HTTP/remote scenarios
- ✅ Web application integration
- ✅ Images returned as base64 for immediate use
- ✅ Automatic cleanup of temporary files
- ✅ Support for both PDF and DOCX files

Use **file path method** for local/network storage scenarios.
Use **base64 method** for remote clients and web applications.
