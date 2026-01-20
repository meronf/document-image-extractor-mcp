# Code Comparison: stdio vs HTTP Transport

## Key Code Changes

### 1. Imports

**Before (stdio):**
```python
import mcp.server.stdio
```

**After (HTTP):**
```python
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
```

---

### 2. Main Entry Point

**Before (stdio):**
```python
async def main():
    """Main entry point for the server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="document-image-extractor-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
```

**After (HTTP):**
```python
# Create SSE transport handler
sse = SseServerTransport("/messages")


async def handle_sse(request):
    """Handle SSE connections."""
    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send,
    ) as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name="document-image-extractor-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
    return Response()


async def handle_messages(request):
    """Handle incoming messages."""
    await sse.handle_post_message(request.scope, request.receive, request._send)
    return Response()


# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ],
)


async def main():
    """Main entry point for the HTTP server."""
    import uvicorn
    
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()
```

---

### 3. Dependencies (pyproject.toml)

**Before:**
```toml
dependencies = [
 "mcp>=1.11.0",
 "pillow>=11.3.0",
 "pymupdf>=1.26.3",
]
```

**After:**
```toml
dependencies = [
 "mcp>=1.11.0",
 "pillow>=11.3.0",
 "pymupdf>=1.26.3",
 "starlette>=0.27.0",
 "uvicorn>=0.23.0",
]
```

---

### 4. MCP Client Configuration

**Before (stdio):**
```json
{
  "mcpServers": {
    "document-image-extractor": {
      "command": "document-image-extractor-mcp",
      "args": []
    }
  }
}
```

**After (HTTP):**
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

---

### 5. Running the Server

**Before (stdio):**
The server was spawned automatically by the MCP client when needed. No manual startup required.

**After (HTTP):**
The server must be started manually and runs continuously:

```bash
document-image-extractor-mcp
```

Or:

```bash
python -m document_image_extractor_mcp
```

---

## What Stayed the Same

✓ All tool handlers (`@server.call_tool()`)
✓ Tool definitions (`@server.list_tools()`)
✓ Document extraction logic
✓ Tool parameters and return values
✓ Error handling
✓ Logging

## Summary

The conversion primarily affects:
1. **Transport layer**: stdio → HTTP/SSE
2. **Server initialization**: stdio streams → Starlette HTTP app
3. **Dependencies**: Added starlette and uvicorn
4. **Deployment**: Process spawn → Network service

The core MCP server logic and tool implementations remain unchanged.
