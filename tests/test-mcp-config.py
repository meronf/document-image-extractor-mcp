#!/usr/bin/env python3
"""
Test script to verify MCP server is accessible from different configurations.
"""

import subprocess
import sys
import os
from pathlib import Path

def test_mcp_server():
    """Test if the MCP server can be started."""
    print("🔧 Testing MCP Server Accessibility")
    print("=" * 50)
    
    # Get the path to the MCP server
    mcp_path = Path("/mnt/b/Users/cjdua/Github/Leet_Vibe/document-image-extractor-mcp")
    
    print(f"📁 MCP Server Path: {mcp_path}")
    print(f"📁 Path exists: {mcp_path.exists()}")
    
    if not mcp_path.exists():
        print("❌ MCP server path does not exist!")
        return False
    
    # Test if uv is available
    try:
        result = subprocess.run(["uv", "--version"], 
                              capture_output=True, text=True, timeout=10)
        print(f"✅ UV available: {result.stdout.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ UV not found in PATH")
        return False
    
    # Test if the MCP server can be imported
    try:
        result = subprocess.run([
            "uv", "run", "--directory", str(mcp_path),
            "python", "-c", 
            "import document_image_extractor_mcp; print('✅ MCP server package imported successfully')"
        ], capture_output=True, text=True, timeout=30, cwd=str(mcp_path))
        
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print(f"❌ Error importing MCP server: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout testing MCP server import")
        return False
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False
    
    print("\n📋 Configuration Summary:")
    print("For Claude Desktop, add this to your config:")
    print(f"""
{{
  "mcpServers": {{
    "document-image-extractor": {{
      "command": "uv",
      "args": [
        "--directory",
        "{mcp_path}",
        "run",
        "document-image-extractor-mcp"
      ]
    }}
  }}
}}
""")
    
    print("🎉 MCP Server is ready for configuration!")
    return True

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)
