"""
Test Sales Agent

Tests the Sales Agent with a sales-related query.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.sales.agent import SalesAgent, SalesAgentContext


def test_sales_agent():
    """Test the Sales Agent with a sales-related query."""
    print("=" * 60)
    print("Testing Sales Agent")
    print("=" * 60)
    
    # Initialize the agent
    print("\n[1] Initializing Sales Agent...")
    agent = SalesAgent(use_tools=True, use_direct_loader=True)
    print("    ✅ Agent initialized successfully")
    
    # Create context with sales query
    test_input = "What is our sales performance for the last 7 days? Are there any concerning trends?"
    print(f"\n[2] Test Input: '{test_input}'")
    
    context = SalesAgentContext(
        question=test_input,
        intent="sales",
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
    assert result.agent == "sales", "Agent name should be 'sales'"
    assert result.finding is not None, "Finding should not be None"
    
    print("\n✅ Sales Agent test passed!")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    test_sales_agent()
