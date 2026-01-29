"""
Test script for LLM-driven Sales and Supervisor agents.

Run this script to verify the new tools-based implementation works correctly.
"""

import logging
from backend.agents.sales import SalesAgent, SalesAgentContext, get_sales_tools
from backend.agents.supervisor import SupervisorAgent, get_supervisor_tools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_sales_tools():
    """Test that sales tools are properly defined."""
    print("\n" + "="*60)
    print("Testing Sales Tools")
    print("="*60)
    
    tools = get_sales_tools()
    print(f"\n[OK] Found {len(tools)} sales tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")


def test_supervisor_tools():
    """Test that supervisor tools are properly defined."""
    print("\n" + "="*60)
    print("Testing Supervisor Tools")
    print("="*60)
    
    tools = get_supervisor_tools()
    print(f"\n[OK] Found {len(tools)} supervisor tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")


def test_sales_agent_direct_mode():
    """Test sales agent in direct mode (no tools, just LLM)."""
    print("\n" + "="*60)
    print("Testing Sales Agent (Direct Mode)")
    print("="*60)
    
    # Initialize agent without tools
    agent = SalesAgent(use_tools=False, use_direct_loader=True)
    
    # Create context
    context = SalesAgentContext(
        question="Why did sales drop yesterday?",
        intent="sales"
    )
    
    print(f"\nQuestion: {context.question}")
    print("Processing...")
    
    # Execute
    result = agent.execute(context)
    
    print(f"\n✓ Finding: {result.finding}")
    print(f"✓ Evidence: {result.evidence}")
    print(f"✓ Confidence: {result.confidence}")


def test_supervisor_intent_detection():
    """Test supervisor intent detection."""
    print("\n" + "="*60)
    print("Testing Supervisor Intent Detection")
    print("="*60)
    
    # Initialize supervisor without tools for simple test
    supervisor = SupervisorAgent(use_tools=False)
    
    test_questions = [
        "Why did sales drop yesterday?",
        "Were any products out of stock?",
        "How are campaigns performing?",
        "Are customer complaints up?",
        "What caused the issue?",
        "Has this happened before?",
        "Fix the problem.",
    ]
    
    print("\nTesting intent detection for various questions:")
    for question in test_questions:
        intent = supervisor.detect_intent(question)
        print(f"  '{question[:40]}...' -> {intent}")


def test_sales_agent_with_tools():
    """Test sales agent with tools enabled."""
    print("\n" + "="*60)
    print("Testing Sales Agent (Tools Mode)")
    print("="*60)
    
    # Initialize agent with tools
    agent = SalesAgent(use_tools=True, use_direct_loader=True)
    
    print(f"\nAvailable tools: {agent.get_available_tools()}")
    
    # Create context
    context = SalesAgentContext(
        question="Why did sales drop yesterday? Was it due to fewer orders or lower order value?",
        intent="sales"
    )
    
    print(f"\nQuestion: {context.question}")
    print("Processing with tools...")
    
    # Execute
    result = agent.execute(context)
    
    print(f"\n[OK] Finding: {result.finding}")
    print(f"[OK] Evidence: {result.evidence}")
    print(f"[OK] Confidence: {result.confidence}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LLM-Driven Agent Tests")
    print("="*60)
    
    # Test tool definitions
    test_sales_tools()
    test_supervisor_tools()
    
    # Test agent functionality
    print("\n\n>>> Running agent tests (requires database connection)...")
    
    try:
        test_sales_agent_direct_mode()
    except Exception as e:
        print(f"\n[FAIL] Direct mode test failed: {e}")
    
    try:
        test_supervisor_intent_detection()
    except Exception as e:
        print(f"\n[FAIL] Intent detection test failed: {e}")
    
    try:
        test_sales_agent_with_tools()
    except Exception as e:
        print(f"\n[FAIL] Tools mode test failed: {e}")
    
    print("\n" + "="*60)
    print("Tests Complete")
    print("="*60)


if __name__ == "__main__":
    main()
