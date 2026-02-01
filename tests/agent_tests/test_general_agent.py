"""
Test General Agent

Tests the General Agent with a simple greeting input.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.general.agent import GeneralAgent, GeneralAgentContext


def test_general_agent():
    """Test the General Agent with a simple 'Hi' input."""
    print("=" * 60)
    print("Testing General Agent")
    print("=" * 60)
    
    # Initialize the agent
    print("\n[1] Initializing General Agent...")
    agent = GeneralAgent(use_tools=True, use_direct_loader=True)
    print("    ✅ Agent initialized successfully")
    
    # Create context with simple greeting
    test_input = "Hi"
    print(f"\n[2] Test Input: '{test_input}'")
    
    context = GeneralAgentContext(
        question=test_input,
        intent="general",
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
    assert result.agent == "general", "Agent name should be 'general'"
    assert result.finding is not None, "Finding should not be None"
    
    print("\n✅ General Agent test passed!")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    test_general_agent()
