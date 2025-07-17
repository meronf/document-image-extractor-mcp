# GitHub Copilot MCP Server Integration Guide

Your local document image extractor MCP server is now configured for GitHub Copilot Chat!

## ✅ Configuration Complete

The MCP server has been added to `.vscode/settings.json` with the following configuration:

```json
{
    "github.copilot.mcp.servers": {
        "document-image-extractor": {
            "command": "uv",
            "args": [
                "--directory",
                "/mnt/b/Users/cjdua/Github/document-image-extractor-mcp",
                "run",
                "document-image-extractor-mcp"
            ],
            "cwd": "/mnt/b/Users/cjdua/Github/document-image-extractor-mcp",
            "env": {}
        }
    }
}
```

## 🚀 How to Use

### Step 1: Restart VS Code
Restart VS Code to load the new MCP server configuration.

### Step 2: Open GitHub Copilot Chat
- Use `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
- Type "GitHub Copilot: Open Chat"
- Or use the chat icon in the activity bar

### Step 3: Use Your MCP Tools

Your MCP server provides 4 tools that Copilot can now use:

#### 1. **Extract Document Images**

```
"Extract all images from this PDF document: /path/to/document.pdf"
"Can you extract images from my Word document and save them to a specific folder?"
"Process this document and create a ZIP archive with the original and extracted images"
```

#### 2. **Get Document Information**
```
"What information can you tell me about this document: /path/to/document.docx?"
"How many images are in this PDF file?"
```

#### 3. **Validate Documents**
```
"Is this file supported for image extraction: /path/to/document.pdf?"
"Check if this document format is valid for processing"
```

#### 4. **List Supported Formats**
```
"What document formats do you support for image extraction?"
"Show me all the file types you can process"
```

## 📋 Example Conversations

### Extract Images from PDF
```
You: "I have a PDF at /home/user/report.pdf. Can you extract all images from it?"

Copilot: "I'll extract the images from your PDF document using the document image extractor."
[Uses extract_document_images tool]
```

### Get Document Metadata
```
You: "Tell me about this Word document: /home/user/presentation.docx"

Copilot: "Let me analyze that document for you."
[Uses get_document_info tool]
```

### Batch Processing
```
You: "I need to extract images from multiple PDFs in my folder. How can I do this?"

Copilot: "I can help you extract images from multiple documents. Let me start with validating the files..."
[Uses validate_document and extract_document_images tools]
```

## 🔧 Troubleshooting

### If the MCP server doesn't work:

1. **Check VS Code Output Panel**
   - View → Output
   - Select "GitHub Copilot" from dropdown
   - Look for MCP server errors

2. **Verify Configuration**
   - Check that `.vscode/settings.json` contains the MCP configuration
   - Ensure the path to your MCP server is correct

3. **Test MCP Server Manually**
   ```bash
   cd /mnt/b/Users/cjdua/Github/document-image-extractor-mcp
   uv run document-image-extractor-mcp
   ```

4. **Check Dependencies**
   ```bash
   cd /mnt/b/Users/cjdua/Github/document-image-extractor-mcp
   uv sync
   ```

## 🎯 Key Benefits

- **Seamless Integration**: Ask Copilot in natural language to extract images
- **No Manual Commands**: No need to run terminal commands
- **Context Aware**: Copilot understands your intent and uses the right tool
- **Error Handling**: Graceful error messages if files don't exist or aren't supported

## 📝 Notes

- The MCP server runs locally and processes files on your machine
- Supports PDF (.pdf) and Word (.docx) documents
- Extracted images are saved to configurable output directories
- All processing happens locally - no data sent to external services

Happy document processing with GitHub Copilot! 🎉
