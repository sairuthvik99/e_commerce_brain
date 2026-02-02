"""
DeepEval End-to-End Tests

Tests the complete flow from user query to final response.
Uses simple assertions to verify the agent pipeline.
"""

import pytest

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.supervisor.agent import SupervisorAgent


class TestEndToEndFlow:
    """End-to-end tests for the complete agent flow."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize agents."""
        self.supervisor = SupervisorAgent()

    def test_supervisor_full_flow(self):
        """Test the complete supervisor flow."""
        test_state = {
            "question": "Why are our sales declining while inventory is low?"
        }
        
        # Run supervisor
        result = self.supervisor(test_state)
        
        # Verify required fields
        assert result.get("intent") is not None, "Intent should be detected"
        assert result.get("agents_to_call") is not None, "Agents to call should be set"
        assert isinstance(result.get("agents_to_call"), list), "Agents to call should be a list"
        assert len(result.get("agents_to_call", [])) > 0, "At least one agent should be called"

    def test_supervisor_preserves_question(self):
        """Test that supervisor preserves the original question."""
        test_state = {
            "question": "What is our inventory status?"
        }
        
        result = self.supervisor(test_state)
        
        assert result.get("question") == test_state["question"], "Question should be preserved"

    @pytest.mark.parametrize("query,expected_agents", [
        ("Why did sales drop?", ["sales"]),
        ("Stock levels are low", ["inventory"]),
        ("Marketing ROI analysis", ["marketing"]),
        ("Customer complaints summary", ["support"]),
    ])
    def test_agent_routing(self, query, expected_agents):
        """Test that queries are routed to correct agents."""
        state = {"question": query}
        result = self.supervisor(state)
        
        agents_to_call = result.get("agents_to_call", [])
        
        # Check if at least one expected agent is in the routing
        matched = any(agent in agents_to_call for agent in expected_agents)
        
        assert matched, (
            f"Query '{query}' should route to {expected_agents}, "
            f"but got {agents_to_call}"
        )

    def test_valid_agents_in_routing(self):
        """Test that only valid agents are returned."""
        valid_agents = {"sales", "inventory", "marketing", "support", "general"}
        
        queries = [
            "Sales analysis needed",
            "Check inventory",
            "Marketing performance",
            "Customer issues",
            "Business overview",
        ]
        
        for query in queries:
            state = {"question": query}
            result = self.supervisor(state)
            agents_to_call = result.get("agents_to_call", [])
            
            for agent in agents_to_call:
                assert agent in valid_agents, f"Invalid agent '{agent}' for query '{query}'"


class TestMultiAgentCoordination:
    """Tests for multi-agent coordination scenarios."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize supervisor."""
        self.supervisor = SupervisorAgent()

    def test_complex_query_returns_agents(self):
        """Test that complex queries return valid agent routing."""
        complex_queries = [
            "Sales are down and inventory is low, what's happening?",
            "Customer complaints are increasing and marketing isn't working",
            "Give me a full business analysis",
        ]
        
        for query in complex_queries:
            state = {"question": query}
            result = self.supervisor(state)
            
            agents = result.get("agents_to_call", [])
            
            # Complex queries should return at least one agent
            assert len(agents) >= 1, f"Query '{query}' should return at least one agent"
            assert result.get("intent") is not None, f"Intent should be detected for '{query}'"

    def test_general_query_routing(self):
        """Test that general/overview queries work correctly."""
        general_queries = [
            "Give me an overview",
            "How is the business doing?",
            "Summary of everything",
        ]
        
        for query in general_queries:
            state = {"question": query}
            result = self.supervisor(state)
            
            intent = result.get("intent")
            agents = result.get("agents_to_call", [])
            
            # General queries should have valid routing
            assert intent is not None, f"Intent should be detected for '{query}'"
            assert len(agents) >= 1, f"At least one agent should be routed for '{query}'"

    def test_supervisor_state_structure(self):
        """Test that supervisor returns proper state structure."""
        state = {"question": "Test query for sales analysis"}
        result = self.supervisor(state)
        
        # Check all expected keys are present
        expected_keys = ["question", "intent", "agents_to_call"]
        for key in expected_keys:
            assert key in result, f"Result should contain '{key}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
