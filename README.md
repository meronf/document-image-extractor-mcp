# Document Image Extractor MCP Server

A Model Context Protocol (MCP) server that provides tools for extracting images from PDF and Word documents. This server exposes document image extraction capabilities to AI assistants and other MCP clients.

## Features

- **PDF Image Extraction**: Extract embedded images from PDF files with size filtering
- **Word Document Processing**: Extract images from .docx files  
- **Document Analysis**: Get metadata and image counts without extraction
- **Format Validation**: Check document compatibility before processing
- **Flexible Output**: Configurable output directories and file naming
- **ZIP Archive Creation**: Automatically create ZIP files containing original document and extracted images

## Available Tools

### `extract_document_images`

Extract all images from a PDF or Word document, save them as separate files, and create a ZIP archive containing both the original document and extracted images.

**Parameters:**
- `document_path` (required): Path to the document file (.pdf or .docx)
- `output_dir` (optional): Directory to save extracted images
- `min_image_size` (optional): Minimum image dimension for PDF extraction (default: 10)

**Returns:** List of extracted image files with paths, metadata, and ZIP archive location

### `get_document_info`
Get information about a document without extracting images.

**Parameters:**
- `document_path` (required): Path to the document file

**Returns:** Document metadata including page count, file size, and image count

### `validate_document`
Check if a document file is valid and supported for image extraction.

**Parameters:**
- `document_path` (required): Path to the document file

**Returns:** Validation status and file information

### `list_supported_formats`
List all supported document formats for image extraction.

**Returns:** Information about supported file types and their capabilities

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd document-image-extractor-mcp
```

2. Install dependencies using uv:
```bash
uv sync
```

## Configuration

### Claude Desktop

Add the server to your Claude Desktop configuration:

**MacOS:** `~/Library/Application\ Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "document-image-extractor": {
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/b/Users/cjdua/Github/document-image-extractor-mcp",
        "run",
        "document-image-extractor-mcp"
      ]
    }
  }
}
```

Replace the path with the actual location of this directory on your system.

## Usage

### Running the Server

The MCP server communicates over stdio. You can run it directly:

```bash
uv run document-image-extractor-mcp
```

### Example Usage

Once connected to an MCP client, you can use the tools like this:

**Extract images from a PDF:**
```json
{
  "tool": "extract_document_images",
  "arguments": {
    "document_path": "/path/to/document.pdf",
    "output_dir": "/path/to/output",
    "min_image_size": 50
  }
}
```

**Get document information:**
```json
{
  "tool": "get_document_info",
  "arguments": {
    "document_path": "/path/to/document.docx"
  }
}
```

**Validate a document:**
```json
{
  "tool": "validate_document",
  "arguments": {
    "document_path": "/path/to/document.pdf"
  }
}
```

## Supported Formats

- **PDF (.pdf)**: Extracts raster images embedded in pages
- **Word Documents (.docx)**: Extracts images from the document's media archive

## Dependencies

- `mcp>=1.11.0`: Model Context Protocol framework
- `PyMuPDF>=1.23.0`: PDF processing library
- `Pillow>=9.0.0`: Image processing library

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

3. Publish to PyPI:
```bash
uv publish
```

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging experience, use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector uv --directory /mnt/b/Users/cjdua/Github/document-image-extractor-mcp run document-image-extractor-mcp
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

## License

This project is part of the Leet_Vibe repository and follows the same licensing terms.

## Related Projects

This MCP server is based on the [document-image-extractor](../document-image-extractor/) package, which provides the core extraction functionality in a standalone Python package format.