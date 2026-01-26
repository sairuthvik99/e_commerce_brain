"""
MCP Server Implementation

Exposes database queries as MCP tools.
Runs as a standalone service that agents connect to.
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import logging
from typing import Any, Dict
from backend.database.queries import (
    get_most_recent_date,
    get_daily_sales_metrics,
    get_stockout_events,
    get_inventory_baseline,
    get_campaign_performance,
    get_ticket_volume
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP Server for database access.
    
    Exposes database queries as MCP tools that agents can call.
    """
    
    def __init__(self):
        self.server = Server("ecommerce_db")
        self._register_tools()
        logger.info("[MCPServer] Initialized")
    
    def _register_tools(self):
        """Register all available MCP tools."""
        
        # Tool 1: Get most recent date
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="get_most_recent_date",
                    description="Get the most recent date in the database (represents 'yesterday')",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_daily_sales_metrics",
                    description="Get sales metrics for the last N days including revenue, orders, and AOV",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back (default: 7)",
                                "default": 7
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_stockout_events",
                    description="Get inventory stockout events for a specific date",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format (optional, defaults to most recent)",
                                "default": None
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_inventory_baseline",
                    description="Get baseline inventory metrics for comparison",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days for baseline (default: 7)",
                                "default": 7
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_campaign_performance",
                    description="Get marketing campaign performance metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days to analyze (default: 7)",
                                "default": 7
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_ticket_volume",
                    description="Get support ticket volume and sentiment analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days to analyze (default: 7)",
                                "default": 7
                            }
                        },
                        "required": []
                    }
                )
            ]
        
        # Tool execution handler
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
            """Execute MCP tool and return results."""
            try:
                logger.info(f"[MCPServer] Executing tool: {name} with args: {arguments}")
                
                if name == "get_most_recent_date":
                    result = get_most_recent_date()
                    return [TextContent(
                        type="text",
                        text=json.dumps({"date": str(result)})
                    )]
                
                elif name == "get_daily_sales_metrics":
                    days = arguments.get("days", 7)
                    result = get_daily_sales_metrics(days=days)
                    # Convert date objects to strings for JSON serialization
                    result['yesterday_date'] = str(result['yesterday_date'])
                    for item in result['daily_breakdown']:
                        item['date'] = str(item['date'])
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, default=str)
                    )]
                
                elif name == "get_stockout_events":
                    target_date = arguments.get("target_date")
                    if target_date:
                        from datetime import datetime
                        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
                    result = get_stockout_events(target_date=target_date)
                    result['date'] = str(result['date'])
                    for item in result['stockout_details']:
                        if item['out_of_stock_since']:
                            item['out_of_stock_since'] = str(item['out_of_stock_since'])
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, default=str)
                    )]
                
                elif name == "get_inventory_baseline":
                    days = arguments.get("days", 7)
                    result = get_inventory_baseline(days=days)
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, default=str)
                    )]
                
                elif name == "get_campaign_performance":
                    days = arguments.get("days", 7)
                    result = get_campaign_performance(days=days)
                    result['yesterday_date'] = str(result['yesterday_date'])
                    for item in result['daily_breakdown']:
                        item['date'] = str(item['date'])
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, default=str)
                    )]
                
                elif name == "get_ticket_volume":
                    days = arguments.get("days", 7)
                    result = get_ticket_volume(days=days)
                    result['yesterday_date'] = str(result['yesterday_date'])
                    for item in result['daily_breakdown']:
                        item['date'] = str(item['date'])
                    return [TextContent(
                        type="text",
                        text=json.dumps(result, default=str)
                    )]
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
            except Exception as e:
                logger.error(f"[MCPServer] Tool execution failed: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)})
                )]
    
    async def run(self):
        """Run the MCP server."""
        logger.info("[MCPServer] Starting server...")
        print("[MCPServer] Starting server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def start_mcp_server():
    """
    Start the MCP server (blocking).
    
    Usage:
        python -m backend.mcp.server
    """
    import asyncio
    
    server = MCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    start_mcp_server()