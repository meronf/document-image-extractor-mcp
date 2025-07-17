#!/usr/bin/env python3
"""
Simple test script to verify the MCP server tools are working.
This test uses uv run to properly test the server in its environment.
"""

import subprocess
import sys
import json
from pathlib import Path

def test_server():
    """Test the MCP server functionality using uv run."""
    print("🔧 Testing Document Image Extractor MCP Server")
    print("=" * 60)
    
    # Get the MCP server directory
    mcp_dir = Path(__file__).parent.parent
    
    # Test script that will be run with uv
    test_script = '''
import asyncio
import sys
from src.document_image_extractor_mcp.server import handle_list_tools, handle_call_tool

async def test_server():
    print("1. Testing list_tools:")
    try:
        tools = await handle_list_tools()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"❌ Error listing tools: {e}")
        return False
    
    print("\\n2. Testing list_supported_formats tool:")
    try:
        result = await handle_call_tool("list_supported_formats", {})
        print("✅ Supported formats:")
        print(result[0].text)
    except Exception as e:
        print(f"❌ Error testing list_supported_formats: {e}")
        return False
    
    print("\\n3. Testing validate_document tool:")
    try:
        result = await handle_call_tool("validate_document", {
            "document_path": "/non/existent/file.pdf"
        })
        print("✅ Validation result:")
        print(result[0].text)
    except Exception as e:
        print(f"❌ Error testing validate_document: {e}")
        return False
    
    print("\\n🎉 MCP Server test completed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
'''
    
    # Write test script to temporary file
    temp_script = mcp_dir / "temp_test.py"
    try:
        with open(temp_script, 'w') as f:
            f.write(test_script)
        
        # Run the test with uv
        result = subprocess.run([
            "uv", "run", "--directory", str(mcp_dir),
            "python", str(temp_script)
        ], capture_output=True, text=True, timeout=60)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False
    finally:
        # Clean up temporary file
        if temp_script.exists():
            temp_script.unlink()

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)
