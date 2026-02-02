"""
DeepEval Tests for Supervisor Agent Intent Classification

Tests the Supervisor Agent's ability to correctly classify user intents.
Uses simple assertions for intent detection accuracy.
"""

import pytest

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.agents.supervisor.agent import SupervisorAgent


# Define test cases for intent classification
INTENT_TEST_CASES = [
    {
        "input": "Why did sales drop last week?",
        "expected_intent": "sales",
    },
    {
        "input": "What products are out of stock?",
        "expected_intent": "inventory",
    },
    {
        "input": "How are our marketing campaigns performing?",
        "expected_intent": "marketing",
    },
    {
        "input": "What are the top customer complaints?",
        "expected_intent": "support",
    },
    {
        "input": "Give me an overview of the business",
        "expected_intent": "general",
    },
]


class TestSupervisorIntentClassification:
    """Test suite for Supervisor Agent intent classification."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize the Supervisor Agent."""
        self.agent = SupervisorAgent()

    @pytest.mark.parametrize("test_case", INTENT_TEST_CASES)
    def test_intent_detection_correctness(self, test_case):
        """
        Test that detected intent matches expected intent.
        Uses direct assertion for intent matching.
        """
        # Get the detected intent
        detected_intent = self.agent.detect_intent(test_case["input"])
        expected_intent = test_case["expected_intent"]
        
        # Direct assertion - intent should match
        assert detected_intent == expected_intent, (
            f"Intent mismatch for query '{test_case['input']}': "
            f"expected '{expected_intent}', got '{detected_intent}'"
        )

    def test_sales_intent_accuracy(self):
        """Test sales intent detection accuracy."""
        sales_queries = [
            "Why are sales declining?",
            "Show me revenue trends",
            "What's our sales performance?",
            "Which products sell the most?",
        ]
        
        correct = 0
        for query in sales_queries:
            intent = self.agent.detect_intent(query)
            if intent == "sales":
                correct += 1
        
        accuracy = correct / len(sales_queries)
        assert accuracy >= 0.75, f"Sales intent accuracy too low: {accuracy:.2%}"

    def test_inventory_intent_accuracy(self):
        """Test inventory intent detection accuracy."""
        inventory_queries = [
            "What's our stock level?",
            "Which products are running low?",
            "Show me inventory status",
            "Are there any stockouts?",
        ]
        
        correct = 0
        for query in inventory_queries:
            intent = self.agent.detect_intent(query)
            if intent == "inventory":
                correct += 1
        
        accuracy = correct / len(inventory_queries)
        assert accuracy >= 0.75, f"Inventory intent accuracy too low: {accuracy:.2%}"

    def test_marketing_intent_accuracy(self):
        """Test marketing intent detection accuracy."""
        marketing_queries = [
            "How are our ads performing?",
            "What's the ROI on marketing?",
            "Show me campaign metrics",
            "Marketing spend analysis",
        ]
        
        correct = 0
        for query in marketing_queries:
            intent = self.agent.detect_intent(query)
            if intent == "marketing":
                correct += 1
        
        accuracy = correct / len(marketing_queries)
        assert accuracy >= 0.75, f"Marketing intent accuracy too low: {accuracy:.2%}"

    def test_support_intent_accuracy(self):
        """Test support intent detection accuracy."""
        support_queries = [
            "What are customers complaining about?",
            "Show me support tickets",
            "Customer satisfaction issues",
            "Top customer problems",
        ]
        
        correct = 0
        for query in support_queries:
            intent = self.agent.detect_intent(query)
            if intent == "support":
                correct += 1
        
        accuracy = correct / len(support_queries)
        assert accuracy >= 0.75, f"Support intent accuracy too low: {accuracy:.2%}"

    def test_general_intent_accuracy(self):
        """Test general intent detection accuracy."""
        general_queries = [
            "Give me a business overview",
            "How is the company doing?",
            "General performance summary",
            "Overall business health",
        ]
        
        correct = 0
        for query in general_queries:
            intent = self.agent.detect_intent(query)
            if intent == "general":
                correct += 1
        
        accuracy = correct / len(general_queries)
        assert accuracy >= 0.75, f"General intent accuracy too low: {accuracy:.2%}"

    def test_valid_intent_returned(self):
        """Test that all detected intents are valid."""
        valid_intents = {"sales", "inventory", "marketing", "support", "general", "unknown"}
        
        test_queries = [
            "Random question about sales",
            "Inventory check needed",
            "Marketing update please",
            "Support ticket info",
            "General overview",
        ]
        
        for query in test_queries:
            intent = self.agent.detect_intent(query)
            assert intent in valid_intents, f"Invalid intent '{intent}' for query '{query}'"

    def test_empty_question_handling(self):
        """Test handling of empty questions."""
        intent = self.agent.detect_intent("")
        assert intent == "unknown", f"Empty question should return 'unknown', got '{intent}'"

    def test_whitespace_question_handling(self):
        """Test handling of whitespace-only questions."""
        intent = self.agent.detect_intent("   ")
        assert intent == "unknown", f"Whitespace question should return 'unknown', got '{intent}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
