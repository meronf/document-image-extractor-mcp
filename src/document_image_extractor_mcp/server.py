"""
Document Image Extractor MCP Server
Provides tools for extracting images from PDF and Word documents via Model Context Protocol.
"""

import asyncio
import os
import json
import logging
import base64
import tempfile
import shutil
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response, JSONResponse

# Document processing imports
import fitz  # PyMuPDF
from PIL import Image
import zipfile


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("document-extractor-server")

# Create server instance
server = Server("document-image-extractor-mcp")


# Utility Classes (simplified versions of our original utils)
class FileUtils:
    """Utility functions for file operations."""
    
    @staticmethod
    def validate_file_exists(file_path: str) -> bool:
        """Check if a file exists."""
        return os.path.exists(file_path)
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get file extension in lowercase."""
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def is_supported_document(file_path: str) -> bool:
        """Check if file is a supported document type."""
        ext = FileUtils.get_file_extension(file_path)
        return ext in ['.pdf', '.docx']
    
    @staticmethod
    def create_output_directory(output_dir: str) -> None:
        """Create output directory if it doesn't exist."""
        os.makedirs(output_dir, exist_ok=True)


class Base64Utils:
    """Utility functions for base64 encoding/decoding."""
    
    @staticmethod
    def decode_base64_to_file(base64_data: str, output_path: str) -> None:
        """Decode base64 string and save to file."""
        # Remove data URL prefix if present (e.g., 'data:application/pdf;base64,')
        if ',' in base64_data and base64_data.startswith('data:'):
            base64_data = base64_data.split(',', 1)[1]
        
        decoded_data = base64.b64decode(base64_data)
        with open(output_path, 'wb') as f:
            f.write(decoded_data)
    
    @staticmethod
    def encode_file_to_base64(file_path: str) -> str:
        """Encode file to base64 string."""
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """Get MIME type from file extension."""
        ext = FileUtils.get_file_extension(file_path)
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.zip': 'application/zip'
        }
        return mime_types.get(ext, 'application/octet-stream')


class PDFImageExtractor:
    """Extract images from PDF documents."""
    
    def __init__(self, min_image_size: int = 10):
        self.min_image_size = min_image_size
    
    def extract_images(self, pdf_path: str, output_dir: str) -> List[str]:
        """Extract all images from a PDF file."""
        FileUtils.create_output_directory(output_dir)
        extracted_files = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    # Filter small images
                    if pix.width >= self.min_image_size and pix.height >= self.min_image_size:
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            output_file = os.path.join(output_dir, f"page_{page_num + 1}_image_{img_index + 1}.png")
                            pix.save(output_file)
                            extracted_files.append(output_file)
                        else:  # CMYK: convert to RGB
                            pix1 = fitz.Pixmap(fitz.csRGB, pix)
                            output_file = os.path.join(output_dir, f"page_{page_num + 1}_image_{img_index + 1}.png")
                            pix1.save(output_file)
                            extracted_files.append(output_file)
                            pix1 = None
                    
                    pix = None
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {str(e)}")
            raise
        
        return extracted_files
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """Get information about a PDF document."""
        try:
            doc = fitz.open(pdf_path)
            info = {
                'page_count': len(doc),
                'metadata': doc.metadata,
                'file_size': os.path.getsize(pdf_path),
                'image_count_by_page': {}
            }
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                info['image_count_by_page'][page_num + 1] = len(image_list)
            
            doc.close()
            return info
            
        except Exception as e:
            logger.error(f"Error getting PDF info: {str(e)}")
            raise


class WordImageExtractor:
    """Extract images from Word documents."""
    
    def extract_images(self, docx_path: str, output_dir: str) -> List[str]:
        """Extract all images from a Word document."""
        FileUtils.create_output_directory(output_dir)
        extracted_files = []
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as docx_zip:
                # Look for images in the media folder
                for file_info in docx_zip.infolist():
                    if file_info.filename.startswith('word/media/'):
                        # Extract image file
                        image_data = docx_zip.read(file_info.filename)
                        image_name = os.path.basename(file_info.filename)
                        output_file = os.path.join(output_dir, image_name)
                        
                        with open(output_file, 'wb') as f:
                            f.write(image_data)
                        
                        extracted_files.append(output_file)
            
        except Exception as e:
            logger.error(f"Error extracting images from Word document: {str(e)}")
            raise
        
        return extracted_files
    
    def get_docx_info(self, docx_path: str) -> dict:
        """Get information about a Word document."""
        try:
            image_count = 0
            image_files = []
            
            with zipfile.ZipFile(docx_path, 'r') as docx_zip:
                for file_info in docx_zip.infolist():
                    if file_info.filename.startswith('word/media/'):
                        image_count += 1
                        image_files.append(file_info.filename)
            
            return {
                'file_size': os.path.getsize(docx_path),
                'image_count': image_count,
                'image_files': image_files
            }
            
        except Exception as e:
            logger.error(f"Error getting Word document info: {str(e)}")
            raise


class DocumentExtractor:
    """Unified document image extractor for PDF and Word documents."""
    
    def __init__(self, min_image_size: int = 10, create_zip: bool = True):
        self.min_image_size = min_image_size
        self.create_zip = create_zip
        self.pdf_extractor = PDFImageExtractor(min_image_size=min_image_size)
        self.word_extractor = WordImageExtractor()
    
    def extract_images(self, document_path: str, output_dir: Optional[str] = None) -> Tuple[List[str], str, Optional[str]]:
        """Extract all images from a document and optionally create a ZIP file."""
        if not FileUtils.validate_file_exists(document_path):
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        if not FileUtils.is_supported_document(document_path):
            ext = FileUtils.get_file_extension(document_path)
            raise ValueError(f"Unsupported file type: {ext}. Supported types: .pdf, .docx")
        
        file_ext = FileUtils.get_file_extension(document_path)
        
        if output_dir is None:
            doc_name = os.path.splitext(os.path.basename(document_path))[0]
            if file_ext == '.pdf':
                output_dir = os.path.join(os.path.dirname(document_path), f"{doc_name}_pdf_images")
            else:
                output_dir = os.path.join(os.path.dirname(document_path), f"{doc_name}_word_images")
        
        if file_ext == '.pdf':
            extracted_images = self.pdf_extractor.extract_images(document_path, output_dir)
        else:  # .docx
            extracted_images = self.word_extractor.extract_images(document_path, output_dir)
        
        # Create ZIP file by default if images were extracted
        zip_path = None
        if self.create_zip and extracted_images:
            zip_path = self._create_zip_archive(document_path, extracted_images, output_dir)
        
        return extracted_images, output_dir, zip_path
    
    def _create_zip_archive(self, document_path: str, extracted_images: List[str], output_dir: str) -> str:
        """Create a ZIP archive containing the original document and extracted images."""
        doc_name = os.path.splitext(os.path.basename(document_path))[0]
        zip_name = f"{doc_name}_Document_and_Images.zip"
        zip_path = os.path.join(os.path.dirname(document_path), zip_name)
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add the original document
                zipf.write(document_path, f"original_document/{os.path.basename(document_path)}")
                
                # Add all extracted images
                for image_path in extracted_images:
                    image_name = os.path.basename(image_path)
                    zipf.write(image_path, f"extracted_images/{image_name}")
            
            logger.info(f"Created ZIP archive: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Error creating ZIP archive: {e}")
            return None
    
    def get_document_info(self, document_path: str) -> dict:
        """Get information about a document."""
        if not FileUtils.validate_file_exists(document_path):
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        file_ext = FileUtils.get_file_extension(document_path)
        
        if file_ext == '.pdf':
            return self.pdf_extractor.get_pdf_info(document_path)
        elif file_ext == '.docx':
            return self.word_extractor.get_docx_info(document_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")


# Global extractor instance
extractor = DocumentExtractor()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available document extraction tools."""
    return [
        types.Tool(
            name="extract_document_images",
            description="Extract all images from a PDF or Word document, save them as separate files, and create a ZIP archive containing both the original document and extracted images",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_path": {
                        "type": "string", 
                        "description": "Path to the document file (.pdf or .docx)"
                    },
                    "output_dir": {
                        "type": "string", 
                        "description": "Directory to save extracted images (optional, defaults to document directory)"
                    },
                    "min_image_size": {
                        "type": "integer",
                        "description": "Minimum image dimension for PDF extraction (filters decorative images)",
                        "default": 10
                    }
                },
                "required": ["document_path"],
            },
        ),
        types.Tool(
            name="extract_document_images_base64",
            description="Extract images from a base64-encoded PDF or Word document. Accepts the document as base64 string and returns extracted images as base64-encoded data. Perfect for HTTP/remote scenarios where file system access is not shared.",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_base64": {
                        "type": "string",
                        "description": "Base64-encoded document data (PDF or DOCX)"
                    },
                    "document_name": {
                        "type": "string",
                        "description": "Original filename with extension (e.g., 'document.pdf' or 'report.docx')"
                    },
                    "min_image_size": {
                        "type": "integer",
                        "description": "Minimum image dimension for PDF extraction (filters decorative images)",
                        "default": 10
                    },
                    "return_images_as_base64": {
                        "type": "boolean",
                        "description": "If true, return extracted images as base64 strings; if false, return file paths",
                        "default": True
                    }
                },
                "required": ["document_base64", "document_name"],
            },
        ),
        types.Tool(
            name="get_document_info",
            description="Get information about a document (page count, metadata, image count) without extracting images",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_path": {
                        "type": "string", 
                        "description": "Path to the document file (.pdf or .docx)"
                    }
                },
                "required": ["document_path"],
            },
        ),
        types.Tool(
            name="list_supported_formats",
            description="List all supported document formats for image extraction",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="validate_document",
            description="Check if a document file is valid and supported for image extraction",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_path": {
                        "type": "string", 
                        "description": "Path to the document file"
                    }
                },
                "required": ["document_path"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle document extraction tool calls."""
    
    if not arguments:
        arguments = {}
    
    if name == "extract_document_images":
        document_path = arguments.get("document_path")
        output_dir = arguments.get("output_dir", "")
        min_image_size = arguments.get("min_image_size", 10)
        
        if not document_path:
            raise ValueError("document_path is required")
        
        try:
            # Update extractor settings
            global extractor
            extractor = DocumentExtractor(min_image_size=min_image_size, create_zip=True)
            
            # Extract images
            extracted_images, actual_output_dir, zip_path = extractor.extract_images(
                document_path, 
                output_dir if output_dir else None
            )
            
            result = {
                "status": "success",
                "document_path": document_path,
                "output_directory": actual_output_dir,
                "extracted_images": len(extracted_images),
                "image_files": [os.path.basename(img) for img in extracted_images],
                "full_paths": extracted_images,
                "zip_file": zip_path
            }
            
            zip_info = f"\n📦 ZIP Archive: {zip_path}" if zip_path else ""
            
            return [types.TextContent(
                type="text", 
                text=f"Successfully extracted {len(extracted_images)} images from {os.path.basename(document_path)}\n" +
                     f"Output directory: {actual_output_dir}{zip_info}\n" +
                     f"Files: {', '.join([os.path.basename(img) for img in extracted_images])}\n\n" +
                     f"Full result: {json.dumps(result, indent=2)}"
            )]
            
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "extract_document_images_base64":
        document_base64 = arguments.get("document_base64")
        document_name = arguments.get("document_name")
        min_image_size = arguments.get("min_image_size", 10)
        return_images_as_base64 = arguments.get("return_images_as_base64", True)
        
        if not document_base64:
            raise ValueError("document_base64 is required")
        if not document_name:
            raise ValueError("document_name is required")
        
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix="mcp_doc_extract_")
        temp_doc_path = None
        
        try:
            # Validate file extension
            file_ext = FileUtils.get_file_extension(document_name)
            if file_ext not in ['.pdf', '.docx']:
                raise ValueError(f"Unsupported file type: {file_ext}. Supported types: .pdf, .docx")
            
            # Decode base64 to temporary file
            temp_doc_path = os.path.join(temp_dir, document_name)
            Base64Utils.decode_base64_to_file(document_base64, temp_doc_path)
            logger.info(f"Decoded base64 document to: {temp_doc_path}")
            
            # Create extractor with settings
            doc_extractor = DocumentExtractor(min_image_size=min_image_size, create_zip=True)
            
            # Create output directory within temp directory
            output_dir = os.path.join(temp_dir, "extracted_images")
            
            # Extract images
            extracted_images, actual_output_dir, zip_path = doc_extractor.extract_images(
                temp_doc_path,
                output_dir
            )
            
            result = {
                "status": "success",
                "document_name": document_name,
                "extracted_images": len(extracted_images),
                "image_files": [os.path.basename(img) for img in extracted_images]
            }
            
            # Return images as base64 if requested
            if return_images_as_base64:
                result["images_base64"] = []
                for img_path in extracted_images:
                    img_data = {
                        "filename": os.path.basename(img_path),
                        "mime_type": Base64Utils.get_mime_type(img_path),
                        "base64": Base64Utils.encode_file_to_base64(img_path)
                    }
                    result["images_base64"].append(img_data)
                
                # Also encode the ZIP file if it exists
                if zip_path and os.path.exists(zip_path):
                    result["zip_base64"] = {
                        "filename": os.path.basename(zip_path),
                        "mime_type": "application/zip",
                        "base64": Base64Utils.encode_file_to_base64(zip_path)
                    }
            else:
                result["output_directory"] = actual_output_dir
                result["full_paths"] = extracted_images
                result["zip_file"] = zip_path
            
            response_text = f"Successfully extracted {len(extracted_images)} images from {document_name}\n"
            if return_images_as_base64:
                response_text += f"Images returned as base64-encoded data\n"
                response_text += f"Files: {', '.join([os.path.basename(img) for img in extracted_images])}\n\n"
            else:
                response_text += f"Output directory: {actual_output_dir}\n"
                response_text += f"Files: {', '.join([os.path.basename(img) for img in extracted_images])}\n\n"
            
            response_text += f"Full result: {json.dumps(result, indent=2)}"
            
            return [types.TextContent(type="text", text=response_text)]
            
        except Exception as e:
            logger.error(f"Error extracting images from base64 document: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        
        finally:
            # Cleanup temporary files
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary directory: {str(e)}")
    
    elif name == "get_document_info":
        document_path = arguments.get("document_path")
        
        if not document_path:
            raise ValueError("document_path is required")
        
        try:
            info = extractor.get_document_info(document_path)
            info["document_path"] = document_path
            info["file_type"] = FileUtils.get_file_extension(document_path)
            
            return [types.TextContent(
                type="text", 
                text=f"Document Information for {os.path.basename(document_path)}:\n\n" +
                     json.dumps(info, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error getting document info: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "list_supported_formats":
        formats = {
            "supported_extensions": [".pdf", ".docx"],
            "pdf_description": "Portable Document Format - extracts embedded images",
            "docx_description": "Microsoft Word Document - extracts images from media folder",
            "notes": [
                "PDF files: Extracts raster images embedded in pages",
                "Word files: Extracts images from the document's media archive",
                "Minimum image size filtering available for PDF files"
            ]
        }
        
        return [types.TextContent(
            type="text", 
            text="Supported Document Formats:\n\n" + json.dumps(formats, indent=2)
        )]
    
    elif name == "validate_document":
        document_path = arguments.get("document_path")
        
        if not document_path:
            raise ValueError("document_path is required")
        
        try:
            exists = FileUtils.validate_file_exists(document_path)
            supported = FileUtils.is_supported_document(document_path)
            file_ext = FileUtils.get_file_extension(document_path)
            
            validation = {
                "document_path": document_path,
                "exists": exists,
                "file_extension": file_ext,
                "supported": supported,
                "status": "valid" if exists and supported else "invalid"
            }
            
            if not exists:
                validation["error"] = "File does not exist"
            elif not supported:
                validation["error"] = f"Unsupported file type: {file_ext}"
            
            return [types.TextContent(
                type="text", 
                text=f"Document Validation Result:\n\n" + json.dumps(validation, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error validating document: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


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


# REST API endpoints for Power Automate and simple HTTP clients

async def handle_health(request):
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "document-image-extractor-mcp",
        "version": "0.1.0",
        "endpoints": {
            "mcp_sse": "/sse",
            "mcp_messages": "/messages",
            "rest_extract_base64": "/api/extract-base64",
            "rest_health": "/api/health"
        }
    })


async def handle_extract_base64_rest(request):
    """
    REST API endpoint for extracting images from base64 documents.
    Simpler than MCP protocol - perfect for Power Automate, Zapier, etc.
    
    POST /api/extract-base64
    Content-Type: application/json
    
    Body:
    {
        "document_base64": "<base64_string>",
        "document_name": "report.pdf",
        "min_image_size": 10,
        "return_images_as_base64": true
    }
    """
    try:
        # Parse request body
        body = await request.json()
        
        document_base64 = body.get("document_base64")
        document_name = body.get("document_name")
        min_image_size = body.get("min_image_size", 10)
        return_images_as_base64 = body.get("return_images_as_base64", True)
        
        if not document_base64:
            return JSONResponse(
                {"error": "document_base64 is required"},
                status_code=400
            )
        if not document_name:
            return JSONResponse(
                {"error": "document_name is required"},
                status_code=400
            )
        
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix="mcp_doc_extract_")
        temp_doc_path = None
        
        try:
            # Validate file extension
            file_ext = FileUtils.get_file_extension(document_name)
            if file_ext not in ['.pdf', '.docx']:
                return JSONResponse(
                    {"error": f"Unsupported file type: {file_ext}. Supported: .pdf, .docx"},
                    status_code=400
                )
            
            # Decode base64 to temporary file
            temp_doc_path = os.path.join(temp_dir, document_name)
            Base64Utils.decode_base64_to_file(document_base64, temp_doc_path)
            logger.info(f"REST API: Decoded base64 document to: {temp_doc_path}")
            
            # Update extractor settings
            global extractor
            extractor = DocumentExtractor(min_image_size=min_image_size, create_zip=True)
            
            # Create output directory within temp directory
            output_dir = os.path.join(temp_dir, "extracted_images")
            
            # Extract images
            extracted_images, actual_output_dir, zip_path = extractor.extract_images(
                temp_doc_path,
                output_dir
            )
            
            result = {
                "status": "success",
                "document_name": document_name,
                "extracted_images_count": len(extracted_images),
                "image_files": [os.path.basename(img) for img in extracted_images]
            }
            
            # Return images as base64 if requested
            if return_images_as_base64:
                result["images"] = []
                for img_path in extracted_images:
                    img_data = {
                        "filename": os.path.basename(img_path),
                        "mime_type": Base64Utils.get_mime_type(img_path),
                        "base64": Base64Utils.encode_file_to_base64(img_path)
                    }
                    result["images"].append(img_data)
                
                # Also encode the ZIP file if it exists
                if zip_path and os.path.exists(zip_path):
                    result["zip"] = {
                        "filename": os.path.basename(zip_path),
                        "mime_type": "application/zip",
                        "base64": Base64Utils.encode_file_to_base64(zip_path)
                    }
            else:
                result["output_directory"] = actual_output_dir
                result["image_paths"] = extracted_images
                result["zip_path"] = zip_path
            
            return JSONResponse(result)
            
        except Exception as e:
            logger.error(f"REST API: Error extracting images: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=500
            )
        
        finally:
            # Cleanup temporary files
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"REST API: Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"REST API: Failed to cleanup: {str(e)}")
    
    except Exception as e:
        logger.error(f"REST API: Request error: {str(e)}")
        return JSONResponse(
            {"error": "Invalid request format"},
            status_code=400
        )


# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        # MCP protocol endpoints
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
        
        # REST API endpoints (for Power Automate, etc.)
        Route("/api/health", endpoint=handle_health, methods=["GET"]),
        Route("/api/extract-base64", endpoint=handle_extract_base64_rest, methods=["POST"]),
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