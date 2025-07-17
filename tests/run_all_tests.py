#!/usr/bin/env python3
"""
Test Suite for Document Image Extractor MCP Server

This script runs all tests to verify the MCP server functionality.
"""

import sys
import os
import subprocess
from pathlib import Path

def run_test(test_file, description):
    """Run a single test file and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"File: {test_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ PASSED")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ FAILED")
            if result.stderr:
                print("STDERR:", result.stderr)
            if result.stdout:
                print("STDOUT:", result.stdout)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all tests in the test suite."""
    print("🧪 Document Image Extractor MCP Server Test Suite")
    print("=" * 60)
    
    # Get the tests directory
    tests_dir = Path(__file__).parent
    
    # Define test files and their descriptions
    tests = [
        ("test_server.py", "MCP Server Core Functionality"),
        ("test-mcp-config.py", "MCP Server Configuration and Accessibility"),
        ("test-copilot-mcp.py", "GitHub Copilot MCP Integration"),
        ("test_zip_mcp.py", "ZIP File Creation Functionality"),
    ]
    
    # Track results
    passed = 0
    failed = 0
    
    # Run each test
    for test_file, description in tests:
        test_path = tests_dir / test_file
        
        if test_path.exists():
            if run_test(str(test_path), description):
                passed += 1
            else:
                failed += 1
        else:
            print(f"❌ Test file not found: {test_file}")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! MCP server is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
