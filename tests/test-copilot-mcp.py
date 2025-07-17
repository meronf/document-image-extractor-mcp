#!/usr/bin/env python3
"""
Test GitHub Copilot MCP Server Configuration
"""

import json
import os
from pathlib import Path

def test_copilot_mcp_config():
    """Test the GitHub Copilot MCP configuration."""
    print("🤖 Testing GitHub Copilot MCP Configuration")
    print("=" * 55)
    
    # Check if settings.json exists in the repository root
    settings_path = Path(__file__).parent.parent.parent / ".vscode" / "settings.json"
    if not settings_path.exists():
        print("❌ .vscode/settings.json not found!")
        return False
    
    # Read and validate the configuration
    try:
        with open(settings_path, 'r') as f:
            settings = json.load(f)
        
        print(f"✅ Found settings.json at: {settings_path.absolute()}")
        
        # Check for MCP server configuration
        if "github.copilot.mcp.servers" in settings:
            mcp_servers = settings["github.copilot.mcp.servers"]
            print(f"✅ Found MCP servers configuration with {len(mcp_servers)} server(s)")
            
            if "document-image-extractor" in mcp_servers:
                server_config = mcp_servers["document-image-extractor"]
                print("✅ Found document-image-extractor server configuration")
                print(f"   Command: {server_config.get('command', 'Not set')}")
                print(f"   Args: {server_config.get('args', [])}")
                print(f"   Working Directory: {server_config.get('cwd', 'Not set')}")
                
                # Verify the MCP server path exists
                mcp_path = "/mnt/b/Users/cjdua/Github/Leet_Vibe/document-image-extractor-mcp"
                if os.path.exists(mcp_path):
                    print(f"✅ MCP server path exists: {mcp_path}")
                else:
                    print(f"❌ MCP server path not found: {mcp_path}")
                    return False
                
            else:
                print("❌ document-image-extractor server not found in configuration")
                return False
        else:
            print("❌ No MCP servers configuration found")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in settings.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading settings.json: {e}")
        return False
    
    print("\n📋 Configuration Summary:")
    print("✅ GitHub Copilot MCP server configured successfully!")
    print("\n🔧 Next Steps:")
    print("1. Restart VS Code to reload the settings")
    print("2. Open GitHub Copilot Chat")
    print("3. Your MCP server tools should now be available:")
    print("   - extract_document_images")
    print("   - get_document_info") 
    print("   - validate_document")
    print("   - list_supported_formats")
    
    print("\n💡 Usage Example:")
    print("In Copilot Chat, you can now ask:")
    print("'Extract images from my PDF document at /path/to/document.pdf'")
    print("'What information can you get about this Word document?'")
    
    return True

if __name__ == "__main__":
    test_copilot_mcp_config()
