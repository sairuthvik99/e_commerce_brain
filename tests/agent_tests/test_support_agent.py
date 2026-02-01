"""
Test Support Agent

Tests the Support Agent with a support-related query.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.support.agent import SupportAgent, SupportAgentContext


def test_support_agent():
    """Test the Support Agent with a support-related query."""
    print("=" * 60)
    print("Testing Support Agent")
    print("=" * 60)
    
    # Initialize the agent
    print("\n[1] Initializing Support Agent...")
    agent = SupportAgent(use_tools=True, use_direct_loader=True)
    print("    ✅ Agent initialized successfully")
    
    # Create context with support query
    test_input = "What are the most common customer complaints? Are there any spikes in support tickets?"
    print(f"\n[2] Test Input: '{test_input}'")
    
    context = SupportAgentContext(
        question=test_input,
        intent="support",
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
    assert result.agent == "support", "Agent name should be 'support'"
    assert result.finding is not None, "Finding should not be None"
    
    print("\n✅ Support Agent test passed!")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    test_support_agent()
