#!/usr/bin/env python3
"""
Test MCP Server Connection

Verifies that MCP server and client work correctly.
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.mcp.client import MCPClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mcp():
    """Test MCP server connection and tools."""
    print("\n" + "=" * 60)
    print("🧪 Testing MCP Server Connection")
    print("=" * 60 + "\n")
    
    client = MCPClient()
    
    try:
        async with client.connect():
            print("✅ Connected to MCP server\n")
            
            # Test 1: Get most recent date
            print("Test 1: Get most recent date")
            date = await client.get_most_recent_date()
            print(f"  → Yesterday: {date}\n")
            
            # Test 2: Get sales metrics
            print("Test 2: Get sales metrics")
            sales = await client.get_daily_sales_metrics(days=7)
            print(f"  → Yesterday revenue: ${sales['yesterday_revenue']:.2f}")
            print(f"  → Avg revenue: ${sales['avg_revenue']:.2f}\n")
            
            # Test 3: Get stockouts
            print("Test 3: Get stockout events")
            stockouts = await client.get_stockout_events()
            print(f"  → Total stockouts: {stockouts['total_stockouts']}\n")
            
            # Test 4: Get marketing data
            print("Test 4: Get campaign performance")
            marketing = await client.get_campaign_performance(days=7)
            print(f"  → Yesterday conversions: {marketing['yesterday_conversions']}")
            print(f"  → Avg conversions: {marketing['avg_conversions']:.1f}\n")
            
            # Test 5: Get support data
            print("Test 5: Get ticket volume")
            support = await client.get_ticket_volume(days=7)
            print(f"  → Yesterday tickets: {support['yesterday_tickets']}")
            print(f"  → Avg tickets: {support['avg_tickets']:.1f}\n")
            
            print("=" * 60)
            print("✅ All MCP tests passed!")
            print("=" * 60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        raise


if __name__ == "__main__":
    asyncio.run(test_mcp())