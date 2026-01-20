"""
Test script for base64 document extraction functionality.
Demonstrates encoding a document to base64 and extracting images.
"""

import base64
import json
import os


def encode_document_to_base64(file_path: str) -> str:
    """Encode a document file to base64."""
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def test_base64_extraction():
    """
    Example test for base64 document extraction.
    
    This demonstrates how to:
    1. Encode a PDF/DOCX to base64
    2. Send it to the MCP server
    3. Receive extracted images as base64
    """
    
    # Example: Load a test document (you'll need to provide a real path)
    test_doc_path = "path/to/your/test_document.pdf"
    
    if not os.path.exists(test_doc_path):
        print("⚠️  Please provide a valid document path in the script")
        print("   Update 'test_doc_path' variable with an actual PDF or DOCX file")
        return
    
    print("=" * 60)
    print("Base64 Document Extraction Test")
    print("=" * 60)
    print(f"\n1. Encoding document: {test_doc_path}")
    
    # Encode document to base64
    document_base64 = encode_document_to_base64(test_doc_path)
    document_name = os.path.basename(test_doc_path)
    
    print(f"   ✓ Document encoded to base64 ({len(document_base64)} characters)")
    print(f"   Document name: {document_name}")
    
    # Example MCP tool call payload
    tool_call = {
        "tool": "extract_document_images_base64",
        "arguments": {
            "document_base64": document_base64,
            "document_name": document_name,
            "min_image_size": 10,
            "return_images_as_base64": True
        }
    }
    
    print(f"\n2. Tool call prepared:")
    print(f"   Tool: {tool_call['tool']}")
    print(f"   Arguments:")
    print(f"     - document_name: {document_name}")
    print(f"     - min_image_size: 10")
    print(f"     - return_images_as_base64: True")
    print(f"     - document_base64: <{len(document_base64)} chars>")
    
    print(f"\n3. Example tool call JSON (truncated base64):")
    example_call = {
        "tool": tool_call["tool"],
        "arguments": {
            **tool_call["arguments"],
            "document_base64": document_base64[:100] + "..." + document_base64[-100:]
        }
    }
    print(json.dumps(example_call, indent=2))
    
    print(f"\n4. Expected response structure:")
    expected_response = {
        "status": "success",
        "document_name": document_name,
        "extracted_images": "N (number of images)",
        "image_files": ["image1.png", "image2.png", "..."],
        "images_base64": [
            {
                "filename": "page_1_image_1.png",
                "mime_type": "image/png",
                "base64": "<base64_encoded_image_data>"
            }
        ],
        "zip_base64": {
            "filename": "document_Document_and_Images.zip",
            "mime_type": "application/zip",
            "base64": "<base64_encoded_zip_data>"
        }
    }
    print(json.dumps(expected_response, indent=2))
    
    print("\n" + "=" * 60)
    print("To actually test this:")
    print("1. Start the MCP server: document-image-extractor-mcp")
    print("2. Use an MCP client to call: extract_document_images_base64")
    print("3. Pass the base64-encoded document data")
    print("=" * 60)


def example_decode_base64_image(base64_string: str, output_path: str):
    """
    Example: Decode a base64 image back to a file.
    """
    image_data = base64.b64decode(base64_string)
    with open(output_path, 'wb') as f:
        f.write(image_data)
    print(f"Decoded image saved to: {output_path}")


if __name__ == "__main__":
    print("\n🔍 Base64 Document Extraction Test\n")
    test_base64_extraction()
    
    print("\n\n📝 Usage Notes:")
    print("=" * 60)
    print("1. File Path Method (existing):")
    print("   - Use: extract_document_images")
    print("   - Requires: Server has file system access")
    print("   - Best for: Local deployments, shared drives")
    print()
    print("2. Base64 Method (new):")
    print("   - Use: extract_document_images_base64")
    print("   - Requires: Document encoded as base64 string")
    print("   - Best for: HTTP/remote clients, web applications")
    print("   - Returns: Images as base64 (or file paths)")
    print("=" * 60)
