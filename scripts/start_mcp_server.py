#!/usr/bin/env python3
"""
MCP Server Startup Script

Starts the MCP server for database access.
Run this before starting the main application.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.mcp.server import start_mcp_server
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Start MCP server."""
    print("=" * 60)
    print("🌐 AI Operations Brain - MCP Server")
    print("=" * 60)
    print()
    print("Starting MCP server for database access...")
    print("  → Database: PostgreSQL")
    print("  → Protocol: Model Context Protocol (MCP)")
    print("  → Mode: stdio (standard input/output)")
    print()
    print("Server ready. Waiting for client connections...")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    try:
        start_mcp_server()
    except KeyboardInterrupt:
        print("\n\n⚠️  Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()