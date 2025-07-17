"""
Document Image Extractor MCP Server
Provides tools for extracting images from PDF and Word documents via Model Context Protocol.
"""

import asyncio
import os
import json
import logging
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

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