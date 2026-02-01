"""
Test Inventory Agent

Tests the Inventory Agent with an inventory-related query.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.inventory.agent import InventoryAgent, InventoryAgentContext


def test_inventory_agent():
    """Test the Inventory Agent with an inventory-related query."""
    print("=" * 60)
    print("Testing Inventory Agent")
    print("=" * 60)
    
    # Initialize the agent
    print("\n[1] Initializing Inventory Agent...")
    agent = InventoryAgent(use_tools=True, use_direct_loader=True)
    print("    ✅ Agent initialized successfully")
    
    # Create context with inventory query
    test_input = "What products are currently out of stock or have low inventory levels?"
    print(f"\n[2] Test Input: '{test_input}'")
    
    context = InventoryAgentContext(
        question=test_input,
        intent="inventory",
        other_agent_outputs={}
    )
    
    # Execute the agent
    print("\n[3] Executing agent...")
    result = agent.execute(context)
    
    # Display results
    print("\n[4] Results:")
    print("-" * 40)
    print(f"    Agent: {result.agent}")
    print(f"    Finding: {result.finding}")
    print(f"    Evidence: {result.evidence}")
    print(f"    Confidence: {result.confidence}")
    print("-" * 40)
    
    # Basic assertions
    assert result is not None, "Result should not be None"
    assert result.agent == "inventory", "Agent name should be 'inventory'"
    assert result.finding is not None, "Finding should not be None"
    
    print("\n✅ Inventory Agent test passed!")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    test_inventory_agent()
