"""
Main entry point for the document_image_extractor_mcp package.
"""
import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
