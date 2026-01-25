"""
Application Entry Point

For Day 2: CLI-based testing
For Day 6: Will become API server
"""

import logging
from .graph import run_graph
from .settings import Settings
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for testing the graph.
    """
    print("\n" + "="*10)
    print("🧠 AI Operations Brain - Day 2 MVP Test")
    print("="*10 + "\n")
    
    # Test question
    question = "Why did sales drop yesterday?"
    
    print(f"Question: {question}\n")
    print("-"*10)
    
    # Run the graph
    try:
        final_state = run_graph(question)
        
        # Display results
        print("\n" + "="*10)
        print("📊 RESULTS")
        print("="*10 + "\n")
        
        print(f"🎯 Detected Intent: {final_state.get('intent', 'N/A')}")
        print(f"🤖 Agents Called: {', '.join(final_state.get('agents_to_call', []))}")
        
        print("\n" + "-"*10)
        print("Agent Outputs:")
        print("-"*10 + "\n")
        
        agent_outputs = final_state.get('agent_outputs', {})
        for agent_name, output in agent_outputs.items():
            print(f"🔹 {agent_name.upper()} Agent:")
            print(f"   Finding: {output.get('finding', 'N/A')}")
            print(f"   Evidence: {', '.join(output.get('evidence', []))}")
            print(f"   Confidence: {output.get('confidence', 0):.2%}")
            print()
        
        if final_state.get('error'):
            print(f"⚠️  Error: {final_state['error']}")
        
        print("="*10)
        print("✅ Day 2 MVP Flow Complete!")
        print("="*10 + "\n")
        
        # Save full state to file for inspection
        with open("day2_output.json", "w") as f:
            json.dump(final_state, f, indent=2)
        print("💾 Full state saved to: day2_output.json\n")
        
    except Exception as e:
        logger.error(f"Failed to run graph: {e}")
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()