"""
Application Entry Point

For Day 3: CLI-based testing with real agents
For Day 6: Will become API server
"""

import logging
from .graph import run_graph, get_agent_findings, get_highest_confidence_agent
from .settings import Settings
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_header(text: str, width: int = 70):
    """Print a formatted header."""
    print("\n" + "=" * width)
    print(text.center(width))
    print("=" * width + "\n")


def print_section(text: str, width: int = 70):
    """Print a formatted section divider."""
    print("\n" + "-" * width)
    print(text)
    print("-" * width + "\n")


def format_confidence_bar(confidence: float, width: int = 20) -> str:
    """Create a visual confidence bar."""
    filled = int(confidence * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {confidence:.1%}"


def main():
    """
    Main entry point for testing the graph.
    """
    print_header("🧠 AI Operations Brain - Day 3 MVP Test", 70)
    
    print("Configuration:")
    print(f"  → Database: {Settings.DB_NAME}")
    print(f"  → Azure OpenAI Endpoint: {Settings.AZURE_ENDPOINT}")
    print(f"  → Agent Models: {Settings.AGENT_MODELS}")
    print()
    
    # Test question
    question = "Why did sales drop yesterday?"
    
    print(f"Question: \"{question}\"\n")
    print_section("🚀 Executing Agent Pipeline")
    
    # Run the graph
    try:
        start_time = datetime.now()
        final_state = run_graph(question)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Check for errors
        if final_state.get('error'):
            print(f"\n❌ Error: {final_state['error']}\n")
            return
        
        # Display results
        print_header("📊 ANALYSIS RESULTS", 70)
        
        # Metadata
        print(f"🎯 Detected Intent: {final_state.get('intent', 'N/A')}")
        print(f"🤖 Agents Called: {', '.join(final_state.get('agents_to_call', []))}")
        print(f"✅ Agents Completed: {', '.join(final_state.get('agents_completed', []))}")
        print(f"⏱️  Execution Time: {execution_time:.2f}s")
        
        print_section("🔍 Agent Findings")
        
        agent_outputs = final_state.get('agent_outputs', {})
        
        if not agent_outputs:
            print("⚠️  No agent outputs found\n")
            return
        
        # Display each agent's output
        agent_icons = {
            "inventory": "📦",
            "sales": "💰",
            "marketing": "📢",
            "support": "🎧"
        }
        
        for agent_name, output in agent_outputs.items():
            icon = agent_icons.get(agent_name, "🔹")
            
            print(f"{icon} {agent_name.upper()} Agent")
            print(f"   Finding:")
            
            # Word wrap the finding
            finding = output.get('finding', 'N/A')
            words = finding.split()
            lines = []
            current_line = "     "
            
            for word in words:
                if len(current_line) + len(word) + 1 <= 70:
                    current_line += word + " "
                else:
                    lines.append(current_line)
                    current_line = "     " + word + " "
            lines.append(current_line)
            
            for line in lines:
                print(line)
            
            print(f"   Evidence: {', '.join(output.get('evidence', []))}")
            print(f"   Confidence: {format_confidence_bar(output.get('confidence', 0))}")
            print()
        
        # Highlight highest confidence
        highest_agent, highest_conf = get_highest_confidence_agent(final_state)
        if highest_agent:
            print(f"⭐ Highest Confidence: {highest_agent.upper()} ({highest_conf:.1%})")
            print()
        
        # Synthesis summary
        print_section("🔗 Synthesis (Day 3 Stub)")
        root_cause = final_state.get('root_cause', {})
        print(f"Summary: {root_cause.get('summary', 'N/A')}")
        print(f"Agents Contributing: {root_cause.get('agent_count', 0)}")
        print()
        
        # HITL status
        print_section("✋ Human Approval (Day 3 Stub)")
        hitl = final_state.get('hitl_decision', {})
        print(f"Status: {'✅ Approved' if hitl.get('approved') else '❌ Pending'}")
        print(f"Note: {hitl.get('note', 'N/A')}")
        print()
        
        print_header("✅ Day 3 MVP Flow Complete!", 70)
        
        # Save full state to file for inspection
        output_file = "day3_output.json"
        with open(output_file, "w") as f:
            # Convert to JSON-serializable format
            json_state = json.loads(json.dumps(final_state, default=str))
            json.dump(json_state, f, indent=2)
        
        print(f"💾 Full state saved to: {output_file}")
        print()
        print("Next Steps:")
        print("  1. Review agent findings above")
        print("  2. Check day3_output.json for detailed state")
        print("  3. Verify data is coming from PostgreSQL via MCP")
        print("  4. Ready to move to Day 4 (Synthesis & Reflection)")
        print()
        
    except Exception as e:
        logger.error(f"Failed to run graph: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()