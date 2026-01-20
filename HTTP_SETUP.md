# HTTP MCP Server Setup

The Document Image Extractor MCP server now runs as an HTTP server using Server-Sent Events (SSE) transport.

## Installation

Install the package with its dependencies:

```bash
pip install -e .
```

Or install dependencies manually:

```bash
pip install mcp pillow pymupdf starlette uvicorn
```

## Running the Server

### Option 1: Using the package entry point

```bash
document-image-extractor-mcp
```

### Option 2: Using Python directly

```bash
python -m document_image_extractor_mcp
```

### Option 3: Running the server module directly

```bash
python -c "from document_image_extractor_mcp.server import main; import asyncio; asyncio.run(main())"
```

## Server Configuration

- **Host**: `0.0.0.0` (accessible from any network interface)
- **Port**: `8000`
- **Endpoints**:
  - `GET /sse` - SSE connection endpoint for MCP communication
  - `POST /messages` - Message handling endpoint

## Connecting MCP Clients

To connect an MCP client to this HTTP server, configure the client to use:

```
http://localhost:8000/sse
```

### Example MCP Client Configuration

For tools like Claude Desktop or other MCP clients, use this configuration:

```json
{
  "mcpServers": {
    "document-image-extractor": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    }
  }
}
```

## Available Tools

1. **extract_document_images** - Extract images from PDF/Word documents
2. **get_document_info** - Get document metadata and image count
3. **list_supported_formats** - List supported document formats
4. **validate_document** - Validate if a document is supported

## Testing the Server

You can test if the server is running by checking the SSE endpoint:

```bash
curl http://localhost:8000/sse
```

## Customization

To change the host or port, modify the `main()` function in `server.py`:

```python
config = uvicorn.Config(
    app,
    host="127.0.0.1",  # Change to bind to localhost only
    port=3000,         # Change port number
    log_level="info",
)
```

## Troubleshooting

- **Port already in use**: Change the port number in the `main()` function
- **Connection refused**: Ensure the server is running and firewall allows connections
- **Module not found**: Reinstall the package with `pip install -e .`
