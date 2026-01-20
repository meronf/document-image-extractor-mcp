# Quick Start Guide - HTTP MCP Server

## What Changed?

The Document Image Extractor MCP server has been converted from **stdio transport** to **HTTP transport** with Server-Sent Events (SSE). This makes it accessible via HTTP/HTTPS and allows multiple clients to connect simultaneously.

## Key Differences

### Before (stdio)
- Server communicated via standard input/output streams
- Only accessible through direct process spawning
- One client per server instance

### After (HTTP)
- Server runs as an HTTP service on port 8000
- Accessible via network (localhost or remote)
- Multiple clients can connect simultaneously
- Uses SSE for real-time bidirectional communication

## Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

This will install the new dependencies: `starlette` and `uvicorn`

### 2. Start the Server

```bash
document-image-extractor-mcp
```

You should see output like:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 3. Test the Server (Optional)

In a new terminal:

```bash
python tests/test_http_server.py
```

### 4. Connect Your MCP Client

Configure your MCP client (e.g., Claude Desktop) to connect to:

```
http://localhost:8000/sse
```

## Example: Claude Desktop Configuration

Edit your Claude Desktop MCP configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add or update:

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

## Usage Example

Once connected, you can use the same tools as before:

```python
# Extract images from a PDF
extract_document_images(
    document_path="C:/Documents/sample.pdf",
    output_dir="C:/Output",
    min_image_size=10
)

# Get document information
get_document_info(
    document_path="C:/Documents/sample.docx"
)
```

## Network Access

The server binds to `0.0.0.0:8000` by default, making it accessible from:
- `http://localhost:8000` (local machine)
- `http://127.0.0.1:8000` (local machine)
- `http://<your-ip>:8000` (from other machines on your network)

### Security Note

For production use, consider:
- Using HTTPS with proper certificates
- Implementing authentication
- Restricting access with firewall rules
- Binding to `127.0.0.1` only if remote access is not needed

## Troubleshooting

### Port 8000 already in use

Modify `server.py` line ~465:
```python
config = uvicorn.Config(
    app,
    host="0.0.0.0",
    port=3000,  # Change to any available port
    log_level="info",
)
```

### Cannot connect from remote machine

Check firewall settings and ensure port 8000 is open:

**Windows PowerShell (as Admin):**
```powershell
New-NetFirewallRule -DisplayName "MCP Server" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

### Module import errors

Reinstall the package:
```bash
pip uninstall document-image-extractor-mcp
pip install -e .
```

## Development

To modify server configuration, edit `src/document_image_extractor_mcp/server.py`:

```python
async def main():
    """Main entry point for the HTTP server."""
    import uvicorn
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",      # Bind address
        port=8000,            # Port number
        log_level="info",     # Log level: debug, info, warning, error
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()
```

## Next Steps

- Read `HTTP_SETUP.md` for detailed configuration options
- Check `tests/test_http_server.py` for testing examples
- See MCP documentation for advanced client integration
