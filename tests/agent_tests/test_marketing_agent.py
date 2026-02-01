"""
Test Marketing Agent

Tests the Marketing Agent with a marketing-related query.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.marketing.agent import MarketingAgent, MarketingAgentContext


def test_marketing_agent():
    """Test the Marketing Agent with a marketing-related query."""
    print("=" * 60)
    print("Testing Marketing Agent")
    print("=" * 60)
    
    # Initialize the agent
    print("\n[1] Initializing Marketing Agent...")
    agent = MarketingAgent(use_tools=True, use_direct_loader=True)
    print("    ✅ Agent initialized successfully")
    
    # Create context with marketing query
    test_input = "How are our marketing campaigns performing? What is the current conversion rate and ROI?"
    print(f"\n[2] Test Input: '{test_input}'")
    
    context = MarketingAgentContext(
        question=test_input,
        intent="marketing",
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
    assert result.agent == "marketing", "Agent name should be 'marketing'"
    assert result.finding is not None, "Finding should not be None"
    
    print("\n✅ Marketing Agent test passed!")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    test_marketing_agent()
