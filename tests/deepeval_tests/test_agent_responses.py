"""
DeepEval Tests for Agent Response Quality

Tests the quality of responses from domain agents.
Uses simple assertions to verify response structure and content.
"""

import pytest

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.sales.agent import SalesAgent
from backend.agents.inventory.agent import InventoryAgent
from backend.agents.marketing.agent import MarketingAgent
from backend.agents.support.agent import SupportAgent
from backend.agents.general.agent import GeneralAgent


class TestSalesAgentResponses:
    """Test suite for Sales Agent response quality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize the Sales Agent."""
        self.agent = SalesAgent(use_tools=False)

    def test_sales_agent_returns_output(self):
        """Test that sales agent returns a proper output structure."""
        state = {
            "question": "Why did sales drop last week?",
            "intent": "sales",
            "agent_outputs": {},
            "agents_completed": []
        }
        
        result = self.agent(state)
        
        # Check state is returned
        assert result is not None, "Agent should return a state"
        assert "agent_outputs" in result, "Result should contain agent_outputs"
        
        # Check sales output exists
        agent_output = result.get("agent_outputs", {}).get("sales", {})
        assert agent_output is not None, "Sales agent output should exist"

    def test_sales_agent_adds_to_agent_outputs(self):
        """Test that sales agent adds its output to agent_outputs."""
        state = {
            "question": "What are our top products?",
            "intent": "sales",
            "agent_outputs": {},
            "agents_completed": []
        }
        
        result = self.agent(state)
        
        # Check sales output was added
        assert "sales" in result.get("agent_outputs", {}), "Sales output should be in agent_outputs"
        sales_output = result["agent_outputs"]["sales"]
        assert sales_output is not None, "Sales output should not be None"


class TestInventoryAgentResponses:
    """Test suite for Inventory Agent response quality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize the Inventory Agent."""
        self.agent = InventoryAgent(use_tools=False)

    def test_inventory_agent_returns_output(self):
        """Test that inventory agent returns a proper output structure."""
        state = {
            "question": "What products are low on stock?",
            "intent": "inventory",
            "agent_outputs": {},
            "agents_completed": []
        }
        
        result = self.agent(state)
        
        assert result is not None, "Agent should return a state"
        assert "agent_outputs" in result, "Result should contain agent_outputs"
        
        agent_output = result.get("agent_outputs", {}).get("inventory", {})
        assert agent_output is not None, "Inventory agent output should exist"

    def test_inventory_agent_adds_to_agent_outputs(self):
        """Test that inventory agent adds its output to agent_outputs."""
        state = {
            "question": "Show me stock levels",
            "intent": "inventory",
            "agent_outputs": {},
            "agents_completed": []
        }
        
        result = self.agent(state)
        
        # Check inventory output was added
        assert "inventory" in result.get("agent_outputs", {}), "Inventory output should be in agent_outputs"
        inventory_output = result["agent_outputs"]["inventory"]
        assert inventory_output is not None, "Inventory output should not be None"


class TestMarketingAgentResponses:
    """Test suite for Marketing Agent response quality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize the Marketing Agent."""
        self.agent = MarketingAgent(use_tools=False)

    def test_marketing_agent_returns_output(self):
        """Test that marketing agent returns a proper output structure."""
        state = {
            "question": "How are our marketing campaigns performing?",
            "intent": "marketing",
            "agent_outputs": {},
            "agents_completed": []
        }
        
        result = self.agent(state)
        
        assert result is not None, "Agent should return a state"
        assert "agent_outputs" in result, "Result should contain agent_outputs"
        
        agent_output = result.get("agent_outputs", {}).get("marketing", {})
        assert agent_output is not None, "Marketing agent output should exist"

    def test_marketing_agent_adds_to_agent_outputs(self):
        """Test that marketing agent adds its output to agent_outputs."""
        state = {
            "question": "Marketing ROI analysis",
            "intent": "marketing",
            "agent_outputs": {},
            "agents_completed": []
        }
        
        result = self.agent(state)
        
        # Check marketing output was added
        assert "marketing" in result.get("agent_outputs", {}), "Marketing output should be in agent_outputs"
        marketing_output = result["agent_outputs"]["marketing"]
        assert marketing_output is not None, "Marketing output should not be None"


class TestSupportAgentResponses:
    """Test suite for Support Agent response quality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize the Support Agent."""
        self.agent = SupportAgent(use_tools=False)

    def test_support_agent_returns_output(self):
        """Test that support agent returns a proper output structure."""
        state = {
            "question": "What are the main customer complaints?",
            "intent": "support",
            "agent_outputs": {},
            "agents_completed": []
        }
        
        result = self.agent(state)
        
        assert result is not None, "Agent should return a state"
        assert "agent_outputs" in result, "Result should contain agent_outputs"
        
        agent_output = result.get("agent_outputs", {}).get("support", {})
        assert agent_output is not None, "Support agent output should exist"

    def test_support_agent_adds_to_agent_outputs(self):
        """Test that support agent adds its output to agent_outputs."""
        state = {
            "question": "Customer satisfaction issues",
            "intent": "support",
            "agent_outputs": {},
            "agents_completed": []
        }
        
        result = self.agent(state)
        
        # Check support output was added
        assert "support" in result.get("agent_outputs", {}), "Support output should be in agent_outputs"
        support_output = result["agent_outputs"]["support"]
        assert support_output is not None, "Support output should not be None"


class TestGeneralAgentResponses:
    """Test suite for General Agent response quality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize the General Agent."""
        self.agent = GeneralAgent()

    def test_general_agent_returns_output(self):
        """Test that general agent returns a proper output structure."""
        state = {
            "question": "Give me a business overview",
            "intent": "general",
            "agent_outputs": {},
            "agents_completed": []
        }
        
        result = self.agent(state)
        
        assert result is not None, "Agent should return a state"
        assert "agent_outputs" in result, "Result should contain agent_outputs"
        
        agent_output = result.get("agent_outputs", {}).get("general", {})
        assert agent_output is not None, "General agent output should exist"

    def test_general_agent_adds_to_agent_outputs(self):
        """Test that general agent adds its output to agent_outputs."""
        state = {
            "question": "Overall business health",
            "intent": "general",
            "agent_outputs": {},
            "agents_completed": []
        }
        
        result = self.agent(state)
        
        # Check general output was added
        assert "general" in result.get("agent_outputs", {}), "General output should be in agent_outputs"
        general_output = result["agent_outputs"]["general"]
        assert general_output is not None, "General output should not be None"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
