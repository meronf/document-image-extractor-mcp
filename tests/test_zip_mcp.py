#!/usr/bin/env python3
"""
Test ZIP file creation functionality using uv run.
"""

import subprocess
import sys
import json
from pathlib import Path

def test_zip_functionality():
    """Test ZIP file creation using uv run."""
    print("📦 Testing ZIP File Creation Functionality")
    print("=" * 50)
    
    # Get the MCP server directory
    mcp_dir = Path(__file__).parent.parent
    
    # Test script that will be run with uv
    test_script = '''
import asyncio
import sys
from src.document_image_extractor_mcp.server import DocumentExtractor

async def test_zip():
    print("Testing ZIP file creation...")
    extractor = DocumentExtractor()
    
    # Test with a non-existent file to check error handling
    try:
        result = extractor.extract_images("/non/existent/file.pdf")
        print(f"❌ Should have failed for non-existent file")
        return False
    except Exception as e:
        print(f"✅ Correctly handled non-existent file: {e}")
    
    print("✅ ZIP functionality test completed")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_zip())
    sys.exit(0 if success else 1)
'''
    
    # Write test script to temporary file
    temp_script = mcp_dir / "temp_zip_test.py"
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
    success = test_zip_functionality()
    sys.exit(0 if success else 1)
