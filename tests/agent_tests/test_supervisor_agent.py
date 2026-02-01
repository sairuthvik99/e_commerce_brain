"""
Test Supervisor Agent

Tests the Supervisor Agent with various intent classification queries.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.supervisor.agent import SupervisorAgent


def test_supervisor_agent():
    """Test the Supervisor Agent with intent classification."""
    print("=" * 60)
    print("Testing Supervisor Agent")
    print("=" * 60)
    
    # Initialize the agent
    print("\n[1] Initializing Supervisor Agent...")
    agent = SupervisorAgent()
    print("    ✅ Agent initialized successfully")
    
    # Test intent detection with various queries
    test_queries = [
        ("Why did sales drop last week?", "sales"),
        ("What products are out of stock?", "inventory"),
        ("How are our marketing campaigns performing?", "marketing"),
        ("What are the top customer complaints?", "support"),
        ("Give me an overview of the business", "general"),
    ]
    
    print("\n[2] Testing Intent Detection:")
    print("-" * 40)
    
    results = []
    for query, expected_intent in test_queries:
        intent = agent.detect_intent(query)
        match = "✅" if intent == expected_intent else "⚠️"
        print(f"    {match} Query: '{query[:50]}...'")
        print(f"       Expected: {expected_intent}, Got: {intent}")
        results.append((query, expected_intent, intent))
    
    print("-" * 40)
    
    # Test full __call__ method
    print("\n[3] Testing Full Supervisor Flow:")
    test_state = {
        "question": "Why are our sales declining while inventory is low?"
    }
    
    print(f"    Input Question: '{test_state['question']}'")
    
    result_state = agent(test_state)
    
    print(f"\n[4] Result State:")
    print("-" * 40)
    print(f"    Intent: {result_state.get('intent')}")
    print(f"    Agents to Call: {result_state.get('agents_to_call')}")
    print("-" * 40)
    
    # Basic assertions
    assert result_state.get("intent") is not None, "Intent should not be None"
    assert result_state.get("agents_to_call") is not None, "Agents to call should not be None"
    
    print("\n✅ Supervisor Agent test passed!")
    print("=" * 60)
    
    return result_state


if __name__ == "__main__":
    test_supervisor_agent()
