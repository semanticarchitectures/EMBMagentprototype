#!/usr/bin/env python3
"""
Start the EMBM-J DS MCP Server

This script starts the FastAPI server that implements the MCP protocol.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import uvicorn


def main():
    """Start the MCP server."""
    # Get configuration from environment
    host = os.getenv("EMBM_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("EMBM_SERVER_PORT", "8000"))
    reload = os.getenv("DEBUG", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    print("=" * 50)
    print("EMBM-J DS MCP Server")
    print("=" * 50)
    print(f"Starting server at http://{host}:{port}")
    print(f"Reload enabled: {reload}")
    print(f"Log level: {log_level}")
    print()
    print("Endpoints:")
    print(f"  - MCP Endpoint: http://{host}:{port}/mcp")
    print(f"  - Tools List: http://{host}:{port}/mcp/tools")
    print(f"  - Health Check: http://{host}:{port}/health")
    print(f"  - API Docs: http://{host}:{port}/docs")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    print()

    # Start server
    uvicorn.run(
        "mcp_server.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )


if __name__ == "__main__":
    main()
