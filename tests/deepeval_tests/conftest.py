"""
DeepEval Test Configuration

Pytest fixtures and configuration for DeepEval tests.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.supervisor.agent import SupervisorAgent
from backend.agents.sales.agent import SalesAgent
from backend.agents.inventory.agent import InventoryAgent
from backend.agents.marketing.agent import MarketingAgent
from backend.agents.support.agent import SupportAgent
from backend.agents.general.agent import GeneralAgent


@pytest.fixture(scope="module")
def supervisor_agent():
    """Initialize Supervisor Agent for testing."""
    return SupervisorAgent()


@pytest.fixture(scope="module")
def sales_agent():
    """Initialize Sales Agent for testing."""
    return SalesAgent(use_tools=False)


@pytest.fixture(scope="module")
def inventory_agent():
    """Initialize Inventory Agent for testing."""
    return InventoryAgent(use_tools=False)


@pytest.fixture(scope="module")
def marketing_agent():
    """Initialize Marketing Agent for testing."""
    return MarketingAgent(use_tools=False)


@pytest.fixture(scope="module")
def support_agent():
    """Initialize Support Agent for testing."""
    return SupportAgent(use_tools=False)


@pytest.fixture(scope="module")
def general_agent():
    """Initialize General Agent for testing."""
    return GeneralAgent()
