"""
MCP Client for Agents

Provides a simple interface for agents to query the MCP server.
"""

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import logging
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class MCPClient:
    """
    MCP Client for querying database through MCP server.
    
    Usage:
        client = MCPClient()
        async with client.connect():
            result = await client.call_tool("get_daily_sales_metrics", days=7)
    """
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        logger.info("[MCPClient] Initialized")
    
    @asynccontextmanager
    async def connect(self):
        """
        Connect to MCP server.
        
        Usage:
            async with client.connect():
                # Make queries
        """
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "backend.mcp.server"],
            env=None
        )
        
        try:
            logger.info("[MCPClient] Connecting to MCP server...")
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.session = session
                    logger.info("[MCPClient] Connected successfully")
                    yield self
        except Exception as e:
            logger.error(f"[MCPClient] Connection failed: {e}")
            raise
        finally:
            self.session = None
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments
        
        Returns:
            Tool result as dictionary
        
        Raises:
            RuntimeError: If not connected
            ValueError: If tool call fails
        """
        if self.session is None:
            raise RuntimeError("Not connected to MCP server. Use 'async with client.connect()'")
        
        try:
            logger.info(f"[MCPClient] Calling tool: {tool_name} with args: {kwargs}")
            
            result = await self.session.call_tool(tool_name, arguments=kwargs)
            
            # Parse response
            if result.content:
                text_content = result.content[0].text
                data = json.loads(text_content)
                
                # Check for errors
                if "error" in data:
                    raise ValueError(f"Tool returned error: {data['error']}")
                
                logger.info(f"[MCPClient] Tool {tool_name} succeeded")
                return data
            else:
                raise ValueError("Empty response from tool")
        
        except Exception as e:
            logger.error(f"[MCPClient] Tool call failed: {e}")
            raise
    
    async def get_most_recent_date(self) -> str:
        """Get the most recent date in database."""
        result = await self.call_tool("get_most_recent_date")
        return result["date"]
    
    async def get_daily_sales_metrics(self, days: int = 7) -> Dict:
        """Get sales metrics."""
        return await self.call_tool("get_daily_sales_metrics", days=days)
    
    async def get_stockout_events(self, target_date: Optional[str] = None) -> Dict:
        """Get stockout events."""
        kwargs = {}
        if target_date:
            kwargs["target_date"] = target_date
        return await self.call_tool("get_stockout_events", **kwargs)
    
    async def get_inventory_baseline(self, days: int = 7) -> Dict:
        """Get inventory baseline."""
        return await self.call_tool("get_inventory_baseline", days=days)
    
    async def get_campaign_performance(self, days: int = 7) -> Dict:
        """Get campaign performance."""
        return await self.call_tool("get_campaign_performance", days=days)
    
    async def get_ticket_volume(self, days: int = 7) -> Dict:
        """Get ticket volume."""
        return await self.call_tool("get_ticket_volume", days=days)


# Singleton instance for convenience
_client = MCPClient()


async def get_mcp_client() -> MCPClient:
    """
    Get the singleton MCP client instance.
    
    Usage:
        client = await get_mcp_client()
        async with client.connect():
            data = await client.get_daily_sales_metrics()
    """
    return _client