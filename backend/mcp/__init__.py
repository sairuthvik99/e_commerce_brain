"""
Model Context Protocol (MCP) Server Package

Exposes database functionality through MCP protocol.
Agents use this to query data instead of direct SQL.
"""

from backend.mcp.server import MCPServer
from backend.mcp.client import MCPClient

__all__ = ["MCPServer", "MCPClient"]