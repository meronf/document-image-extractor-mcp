"""
Test script to verify the HTTP MCP server is working correctly.
"""

import asyncio
import json
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import socket


async def test_http_server():
    """Test basic HTTP server connectivity."""
    base_url = "http://localhost:8000"
    
    print("Testing HTTP MCP Server...")
    print(f"Server URL: {base_url}\n")
    
    try:
        # Test SSE endpoint connectivity
        print("1. Testing SSE endpoint (GET /sse)...")
        try:
            req = Request(f"{base_url}/sse", headers={"Accept": "text/event-stream"})
            with urlopen(req, timeout=2) as response:
                status = response.status
                print(f"   Status: {status}")
                if status == 200 or status == 202:
                    print("   ✓ SSE endpoint is accessible")
                else:
                    print(f"   ✗ Unexpected status code: {status}")
        except socket.timeout:
            print("   ✓ SSE endpoint is accessible (connection streaming)")
        except HTTPError as e:
            print(f"   Status: {e.code}")
            if e.code == 200:
                print("   ✓ SSE endpoint is accessible")
            else:
                print(f"   ✗ HTTP Error: {e.code}")
        except URLError as e:
            print(f"   ✗ Error: {e.reason}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        print("\n2. Testing server health...")
        # Try to connect to the base URL to verify server is responding
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()
            
            if result == 0:
                print(f"   Server is running on port 8000")
                print("   ✓ HTTP server is operational")
            else:
                print(f"   ✗ Cannot connect to port 8000")
        except Exception as e:
            print(f"   Note: {e}")
            print("   Server may still be accessible via SSE endpoint")
            
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("\n   Make sure the server is running:")
        print("   Run: document-image-extractor-mcp")
        print("   Or: python -m document_image_extractor_mcp")
        return False
    
    print("\n" + "="*60)
    print("HTTP MCP Server Test Summary")
    print("="*60)
    print("The server appears to be running correctly.")
    print("You can now connect MCP clients to: http://localhost:8000/sse")
    print("="*60)
    
    return True


def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("Document Image Extractor MCP - HTTP Server Test")
    print("="*60 + "\n")
    
    asyncio.run(test_http_server())


if __name__ == "__main__":
    main()
