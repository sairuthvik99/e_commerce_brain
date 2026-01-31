"""
Test script for General Agent functionality.
Tests routing, agent initialization, and basic execution.
"""

import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.supervisor.router import route_agents, VALID_AGENTS
from backend.agents.general import GeneralAgent
from backend.graph import run_graph


def test_router():
    """Test that router correctly routes general and unknown intents."""
    print("\n" + "=" * 60)
    print("Testing Router")
    print("=" * 60)
    
    # Test general intent
    result = route_agents("general")
    print(f"general -> {result}")
    assert result == ["general"], f"Expected ['general'], got {result}"
    print("✓ general intent routes correctly")
    
    # Test unknown intent
    result = route_agents("unknown")
    print(f"unknown -> {result}")
    assert result == ["general"], f"Expected ['general'], got {result}"
    print("✓ unknown intent routes correctly")
    
    # Test sales intent (should still work)
    result = route_agents("sales")
    print(f"sales -> {result}")
    assert result == ["sales"], f"Expected ['sales'], got {result}"
    print("✓ sales intent routes correctly")
    
    # Verify general is in valid agents
    print(f"\nValid agents: {VALID_AGENTS}")
    assert "general" in VALID_AGENTS, "general should be in VALID_AGENTS"
    print("✓ general is in VALID_AGENTS")
    
    print("\n✓ All router tests passed!")


def test_general_agent_init():
    """Test that GeneralAgent initializes correctly."""
    print("\n" + "=" * 60)
    print("Testing GeneralAgent Initialization")
    print("=" * 60)
    
    # Test with tools
    agent = GeneralAgent(use_tools=True, use_direct_loader=True)
    print(f"Agent name: {agent.agent_name}")
    assert agent.agent_name == "general"
    print("✓ GeneralAgent initialized with tools")
    
    # Get available tools
    tools = agent.get_available_tools()
    print(f"Available tools: {tools}")
    assert len(tools) > 0, "Should have at least one tool"
    print(f"✓ GeneralAgent has {len(tools)} tools")
    
    # Test description
    desc = agent.get_tool_description()
    print(f"Description: {desc[:100]}...")
    print("✓ GeneralAgent has tool description")
    
    print("\n✓ All initialization tests passed!")


def test_graph_integration():
    """Test that the graph includes the general agent."""
    print("\n" + "=" * 60)
    print("Testing Graph Integration")
    print("=" * 60)
    
    from backend.graph import AGENT_PRIORITY
    
    print(f"Agent priority: {AGENT_PRIORITY}")
    assert "general" in AGENT_PRIORITY, "general should be in AGENT_PRIORITY"
    print("✓ general is in AGENT_PRIORITY")
    
    print("\n✓ Graph integration test passed!")


def test_full_flow():
    """Test a complete flow with a general question."""
    print("\n" + "=" * 60)
    print("Testing Full Flow with General Question")
    print("=" * 60)
    
    # Test with a general business health question
    question = "How is the business doing overall?"
    print(f"Question: {question}")
    
    try:
        result = run_graph(question)
        
        print(f"\nIntent detected: {result.get('intent', 'N/A')}")
        print(f"Agents to call: {result.get('agents_to_call', [])}")
        print(f"Agents completed: {result.get('agents_completed', [])}")
        
        # Check if general agent was called
        agent_outputs = result.get("agent_outputs", {})
        if "general" in agent_outputs:
            print(f"\n✓ General agent output received")
            finding = agent_outputs["general"].get("finding", "No finding")
            print(f"Finding: {finding[:200]}..." if len(finding) > 200 else f"Finding: {finding}")
        else:
            print("\nAgent outputs:", list(agent_outputs.keys()))
        
        print("\n✓ Full flow test completed!")
        
    except Exception as e:
        print(f"\n✗ Full flow test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GENERAL AGENT TEST SUITE")
    print("=" * 60)
    
    # Run tests
    test_router()
    test_general_agent_init()
    test_graph_integration()
    
    # Ask if user wants to run full flow test (requires DB connection)
    print("\n" + "=" * 60)
    run_full = input("Run full flow test? (requires database connection) [y/N]: ").lower()
    if run_full == 'y':
        test_full_flow()
    else:
        print("Skipping full flow test.")
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
