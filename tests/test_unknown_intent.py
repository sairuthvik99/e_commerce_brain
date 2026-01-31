"""
Quick test for unknown intent routing to General Agent.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.graph import run_graph

# Test with a question that should be classified as "unknown" or "general"
test_questions = [
    "What is the weather like today?",  # Should be unknown
    "Tell me about the company",  # Should be unknown  
    "Summarize yesterday's business health",  # Should be general
]

for question in test_questions:
    print("\n" + "=" * 60)
    print(f"Question: {question}")
    print("=" * 60)
    
    try:
        result = run_graph(question)
        print(f"Intent: {result.get('intent', 'N/A')}")
        print(f"Agents called: {result.get('agents_to_call', [])}")
        print(f"Agents completed: {result.get('agents_completed', [])}")
        
        agent_outputs = result.get("agent_outputs", {})
        if "general" in agent_outputs:
            finding = agent_outputs["general"].get("finding", "No finding")
            print(f"Finding (first 300 chars): {finding[:300]}...")
    except Exception as e:
        print(f"Error: {e}")
