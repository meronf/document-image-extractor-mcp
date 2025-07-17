# Test Suite for Document Image Extractor MCP Server

This directory contains all test scripts for the Document Image Extractor MCP Server.

## Test Files

### Core Tests
- **`test_server.py`** - Tests core MCP server functionality and tool handlers
- **`run_all_tests.py`** - Main test runner that executes all tests

### Configuration Tests
- **`test-mcp-config.py`** - Tests MCP server configuration and accessibility
- **`test-copilot-mcp.py`** - Tests GitHub Copilot MCP integration

### Feature Tests
- **`test_zip_mcp.py`** - Tests ZIP file creation functionality

## Running Tests

### Run All Tests
```bash
cd /mnt/b/Users/cjdua/Github/Leet_Vibe/document-image-extractor-mcp/tests
python3 run_all_tests.py
```

### Run Individual Tests
```bash
# Test core server functionality
python3 test_server.py

# Test configuration
python3 test-mcp-config.py

# Test GitHub Copilot integration
python3 test-copilot-mcp.py

# Test ZIP functionality
python3 test_zip_mcp.py
```

## Test Environment

All tests should be run from the MCP server directory context:
```bash
cd /mnt/b/Users/cjdua/Github/Leet_Vibe/document-image-extractor-mcp
```

## Expected Test Results

When all tests pass, you should see:
- ✅ MCP server tools properly registered
- ✅ Configuration files correctly set up
- ✅ GitHub Copilot integration working
- ✅ ZIP file creation functional
- ✅ Error handling working correctly

## Troubleshooting

If tests fail:
1. Ensure you're in the correct directory
2. Check that `uv` is installed and accessible
3. Verify the MCP server dependencies are installed
4. Make sure the virtual environment is activated

## Adding New Tests

To add a new test:
1. Create a new `.py` file in this directory
2. Follow the existing test patterns
3. Add the test to the `tests` list in `run_all_tests.py`
4. Update this README with the new test description
