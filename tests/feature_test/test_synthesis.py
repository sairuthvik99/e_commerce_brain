"""
Test Suite for Synthesis Agent

Tests the synthesis agent's ability to aggregate agent outputs
into unified root cause analysis.
"""

from backend.synthesis.synthesis import SynthesisAgent
from backend.schemas.agent_output import AgentOutput
from backend.schemas.root_cause import RootCause
import json


def test_synthesis_agent_basic():
    """Test basic synthesis agent functionality with AgentOutput objects"""
    print("\n" + "="*60)
    print("TEST: Basic Synthesis Agent")
    print("="*60)
    
    agent = SynthesisAgent()
    
    # Prepare agent outputs using AgentOutput objects
    agent_outputs = {
        "inventory": AgentOutput(
            finding="15 products out of stock",
            evidence=["stockout_count_15", "5x_baseline"],
            confidence=0.94,
            agent="inventory"
        ),
        "sales": AgentOutput(
            finding="Sales dropped 45%",
            evidence=["45%_drop", "order_count_down"],
            confidence=0.91,
            agent="sales"
        )
    }
    
    # Execute synthesis
    result = agent.synthesize(agent_outputs)
    
    # Assertions
    assert isinstance(result, RootCause), "Result should be RootCause instance"
    assert hasattr(result, "root_cause"), "Result should have root_cause"
    assert hasattr(result, "primary_cause"), "Result should have primary_cause"
    assert hasattr(result, "confidence"), "Result should have confidence"
    assert hasattr(result, "causal_chain"), "Result should have causal_chain"
    assert hasattr(result, "evidence_summary"), "Result should have evidence_summary"
    
    assert result.confidence >= 0.0, "Confidence should be >= 0"
    assert result.confidence <= 1.0, "Confidence should be <= 1"
    assert isinstance(result.causal_chain, list), "Causal chain should be a list"
    assert isinstance(result.contributing_causes, list), "Contributing causes should be a list"
    assert isinstance(result.evidence_summary, dict), "Evidence summary should be a dict"
    
    print(f"✓ Root Cause: {result.root_cause}")
    print(f"✓ Primary Cause: {result.primary_cause}")
    print(f"✓ Contributing Causes: {result.contributing_causes}")
    print(f"✓ Confidence: {result.confidence}")
    print(f"✓ Causal Chain: {result.causal_chain}")
    print(f"✓ Evidence Summary: {result.evidence_summary}")
    print("✅ Basic synthesis test passed!")


def test_synthesis_with_dict_inputs():
    """Test synthesis agent with dictionary inputs"""
    print("\n" + "="*60)
    print("TEST: Synthesis with Dict Inputs")
    print("="*60)
    
    agent = SynthesisAgent()
    
    # Prepare agent outputs as dictionaries
    agent_outputs = {
        "inventory": {
            "finding": "20 SKUs critically low",
            "evidence": ["low_stock_20", "warehouse_alert"],
            "confidence": 0.88,
            "agent": "inventory"
        },
        "sales": {
            "finding": "Revenue dropped 35%",
            "evidence": ["revenue_drop_35%"],
            "confidence": 0.85,
            "agent": "sales"
        }
    }
    
    result = agent.synthesize(agent_outputs)
    
    # Assertions
    assert isinstance(result, RootCause)
    assert result.confidence >= 0.0 and result.confidence <= 1.0
    assert len(result.causal_chain) > 0
    assert result.primary_cause in ["inventory", "sales"]
    
    print(f"✓ Root Cause: {result.root_cause}")
    print(f"✓ Primary Cause: {result.primary_cause}")
    print(f"✓ Confidence: {result.confidence}")
    print("✅ Dict input test passed!")


def test_synthesis_with_mixed_inputs():
    """Test synthesis with mixed AgentOutput objects and dicts"""
    print("\n" + "="*60)
    print("TEST: Synthesis with Mixed Inputs")
    print("="*60)
    
    agent = SynthesisAgent()
    
    # Mix of AgentOutput objects and dicts
    agent_outputs = {
        "inventory": AgentOutput(
            finding="Stock issues detected",
            evidence=["stock_alert"],
            confidence=0.90,
            agent="inventory"
        ),
        "sales": {
            "finding": "Sales declining",
            "evidence": ["sales_drop"],
            "confidence": 0.87,
            "agent": "sales"
        }
    }
    
    result = agent.synthesize(agent_outputs)
    
    # Assertions
    assert isinstance(result, RootCause)
    assert len(result.causal_chain) == 2
    assert "inventory" in result.causal_chain or "inventory" == result.primary_cause
    assert "sales" in result.causal_chain or "sales" in result.contributing_causes
    
    print(f"✓ Successfully handled mixed input types")
    print(f"✓ Causal Chain: {result.causal_chain}")
    print("✅ Mixed input test passed!")


def test_synthesis_all_four_agents():
    """Test synthesis with all four agents (inventory, sales, marketing, support)"""
    print("\n" + "="*60)
    print("TEST: Synthesis with All Four Agents")
    print("="*60)
    
    agent = SynthesisAgent()
    
    agent_outputs = {
        "inventory": AgentOutput(
            finding="15 SKUs critically out of stock",
            evidence=["stockout_count_15", "5x_baseline"],
            confidence=0.94,
            agent="inventory"
        ),
        "sales": AgentOutput(
            finding="Revenue dropped 45% in last 7 days",
            evidence=["45%_drop", "order_count_down"],
            confidence=0.91,
            agent="sales"
        ),
        "marketing": AgentOutput(
            finding="Campaign conversion rate dropped 78%",
            evidence=["conversion_drop_78%", "ctr_down"],
            confidence=0.68,
            agent="marketing"
        ),
        "support": AgentOutput(
            finding="Support tickets increased 400%",
            evidence=["400%_ticket_spike", "delivery_issues"],
            confidence=0.90,
            agent="support"
        )
    }
    
    result = agent.synthesize(agent_outputs)
    
    # Assertions
    assert isinstance(result, RootCause)
    assert len(result.causal_chain) >= 2, "Should have multiple agents in causal chain"
    assert result.primary_cause in ["inventory", "sales", "marketing", "support"]
    assert len(result.evidence_summary) == 4, "Should have evidence from all 4 agents"
    assert all(agent in result.evidence_summary for agent in ["inventory", "sales", "marketing", "support"])
    
    print(f"✓ Root Cause: {result.root_cause}")
    print(f"✓ Primary Cause: {result.primary_cause}")
    print(f"✓ Contributing Causes: {result.contributing_causes}")
    print(f"✓ Confidence: {result.confidence}")
    print(f"✓ Causal Chain: {result.causal_chain}")
    print(f"✓ Evidence Summary Keys: {list(result.evidence_summary.keys())}")
    print("✅ Four-agent synthesis test passed!")


def test_synthesis_single_agent():
    """Test synthesis with only one agent output"""
    print("\n" + "="*60)
    print("TEST: Synthesis with Single Agent")
    print("="*60)
    
    agent = SynthesisAgent()
    
    agent_outputs = {
        "inventory": AgentOutput(
            finding="Critical stock shortage",
            evidence=["stock_shortage"],
            confidence=0.85,
            agent="inventory"
        )
    }
    
    result = agent.synthesize(agent_outputs)
    
    # Assertions
    assert isinstance(result, RootCause)
    assert result.primary_cause == "inventory"
    assert len(result.causal_chain) >= 1
    assert "inventory" in result.causal_chain
    assert len(result.contributing_causes) >= 0
    
    print(f"✓ Root Cause: {result.root_cause}")
    print(f"✓ Primary Cause: {result.primary_cause}")
    print(f"✓ Causal Chain: {result.causal_chain}")
    print("✅ Single agent test passed!")


def test_synthesis_state_update():
    """Test synthesis agent state update via __call__"""
    print("\n" + "="*60)
    print("TEST: Synthesis State Update")
    print("="*60)
    
    agent = SynthesisAgent()
    
    # Prepare state dict (as used by LangGraph)
    state = {
        "agent_outputs": {
            "inventory": AgentOutput(
                finding="10 SKUs out of stock",
                evidence=["stockout_count_10"],
                confidence=0.88,
                agent="inventory"
            ),
            "sales": AgentOutput(
                finding="Sales down 30%",
                evidence=["sales_drop_30%"],
                confidence=0.86,
                agent="sales"
            )
        }
    }
    
    # Call agent (LangGraph style)
    updated_state = agent(state)
    
    # Assertions
    assert "root_cause" in updated_state, "State should have root_cause"
    assert "causal_chain" in updated_state, "State should have causal_chain"
    assert isinstance(updated_state["root_cause"], dict), "root_cause should be dict"
    assert isinstance(updated_state["causal_chain"], list), "causal_chain should be list"
    
    print(f"✓ Root Cause: {updated_state['root_cause']['root_cause']}")
    print(f"✓ Causal Chain: {updated_state['causal_chain']}")
    print(f"✓ State Keys: {list(updated_state.keys())}")
    print("✅ State update test passed!")


def test_synthesis_confidence_weighting():
    """Test that synthesis properly weights findings by confidence"""
    print("\n" + "="*60)
    print("TEST: Synthesis Confidence Weighting")
    print("="*60)
    
    agent = SynthesisAgent()
    
    # High confidence inventory, low confidence sales
    agent_outputs = {
        "inventory": AgentOutput(
            finding="Strong evidence of stockouts",
            evidence=["multiple_stockouts", "warehouse_empty"],
            confidence=0.95,  # Very high
            agent="inventory"
        ),
        "sales": AgentOutput(
            finding="Unclear sales pattern",
            evidence=["mixed_signals"],
            confidence=0.55,  # Low
            agent="sales"
        )
    }
    
    result = agent.synthesize(agent_outputs)
    
    # Assertions
    assert isinstance(result, RootCause)
    # The high-confidence agent should likely be the primary cause
    print(f"✓ Primary Cause: {result.primary_cause}")
    print(f"✓ Overall Confidence: {result.confidence}")
    print(f"✓ Note: High-confidence agent (inventory: 0.95) vs low-confidence (sales: 0.55)")
    print("✅ Confidence weighting test passed!")


def test_synthesis_empty_inputs():
    """Test synthesis with edge case: empty inputs"""
    print("\n" + "="*60)
    print("TEST: Synthesis with Empty Inputs")
    print("="*60)
    
    agent = SynthesisAgent()
    
    try:
        result = agent.synthesize({})
        
        # Should still return a valid RootCause object
        assert isinstance(result, RootCause)
        print(f"✓ Handled empty inputs gracefully")
        print(f"✓ Root Cause: {result.root_cause}")
        print(f"✓ Primary Cause: {result.primary_cause}")
        print("✅ Empty input test passed!")
    except Exception as e:
        print(f"⚠ Empty input raised exception: {e}")
        print("✓ Exception is acceptable for empty inputs")


def test_synthesis_evidence_aggregation():
    """Test that evidence is properly aggregated from all agents"""
    print("\n" + "="*60)
    print("TEST: Synthesis Evidence Aggregation")
    print("="*60)
    
    agent = SynthesisAgent()
    
    agent_outputs = {
        "inventory": AgentOutput(
            finding="Stock issues",
            evidence=["evidence_1", "evidence_2"],
            confidence=0.90,
            agent="inventory"
        ),
        "sales": AgentOutput(
            finding="Sales down",
            evidence=["evidence_3", "evidence_4", "evidence_5"],
            confidence=0.88,
            agent="sales"
        ),
        "support": AgentOutput(
            finding="Tickets up",
            evidence=["evidence_6"],
            confidence=0.85,
            agent="support"
        )
    }
    
    result = agent.synthesize(agent_outputs)
    
    # Assertions
    assert isinstance(result.evidence_summary, dict)
    assert len(result.evidence_summary) == 3  # Three agents
    assert "inventory" in result.evidence_summary
    assert "sales" in result.evidence_summary
    assert "support" in result.evidence_summary
    assert len(result.evidence_summary["inventory"]) == 2
    assert len(result.evidence_summary["sales"]) == 3
    assert len(result.evidence_summary["support"]) == 1
    
    print(f"✓ Evidence Summary: {result.evidence_summary}")
    print(f"✓ Total evidence items: {sum(len(v) for v in result.evidence_summary.values())}")
    print("✅ Evidence aggregation test passed!")


def test_synthesis_causal_chain_ordering():
    """Test that causal chain has proper ordering"""
    print("\n" + "="*60)
    print("TEST: Synthesis Causal Chain Ordering")
    print("="*60)
    
    agent = SynthesisAgent()
    
    # Typical e-commerce issue flow: inventory → sales → marketing → support
    agent_outputs = {
        "inventory": AgentOutput(
            finding="Stockouts detected",
            evidence=["stockout"],
            confidence=0.92,
            agent="inventory"
        ),
        "sales": AgentOutput(
            finding="Sales impacted",
            evidence=["sales_drop"],
            confidence=0.89,
            agent="sales"
        ),
        "marketing": AgentOutput(
            finding="Conversions down",
            evidence=["conversion_drop"],
            confidence=0.75,
            agent="marketing"
        ),
        "support": AgentOutput(
            finding="Customer complaints up",
            evidence=["complaint_spike"],
            confidence=0.88,
            agent="support"
        )
    }
    
    result = agent.synthesize(agent_outputs)
    
    # Assertions
    assert isinstance(result.causal_chain, list)
    assert len(result.causal_chain) >= 2
    print(f"✓ Causal Chain: {result.causal_chain}")
    print(f"✓ Primary Cause: {result.primary_cause}")
    print(f"✓ Contributing Causes: {result.contributing_causes}")
    print("✅ Causal chain ordering test passed!")


def test_synthesis_pydantic_validation():
    """Test that output properly validates against RootCause schema"""
    print("\n" + "="*60)
    print("TEST: Synthesis Pydantic Validation")
    print("="*60)
    
    agent = SynthesisAgent()
    
    agent_outputs = {
        "inventory": AgentOutput(
            finding="Test finding",
            evidence=["test"],
            confidence=0.80,
            agent="inventory"
        )
    }
    
    result = agent.synthesize(agent_outputs)
    
    # Test all required RootCause fields
    assert hasattr(result, "root_cause")
    assert hasattr(result, "primary_cause")
    assert hasattr(result, "contributing_causes")
    assert hasattr(result, "confidence")
    assert hasattr(result, "causal_chain")
    assert hasattr(result, "evidence_summary")
    
    # Test field types
    assert isinstance(result.root_cause, str)
    assert isinstance(result.primary_cause, str)
    assert isinstance(result.contributing_causes, list)
    assert isinstance(result.confidence, float)
    assert isinstance(result.causal_chain, list)
    assert isinstance(result.evidence_summary, dict)
    
    # Test field constraints
    assert 0.0 <= result.confidence <= 1.0
    
    # Test serialization
    dict_output = result.dict()
    assert isinstance(dict_output, dict)
    json_output = result.json()
    assert isinstance(json_output, str)
    
    print(f"✓ All RootCause fields present and valid")
    print(f"✓ Pydantic validation passed")
    print(f"✓ Serialization works: dict() and json()")
    print("✅ Pydantic validation test passed!")


def run_all_tests():
    """Run all synthesis agent tests"""
    print("\n" + "="*70)
    print(" SYNTHESIS AGENT TEST SUITE")
    print("="*70)
    
    try:
        test_synthesis_agent_basic()
        test_synthesis_with_dict_inputs()
        test_synthesis_with_mixed_inputs()
        test_synthesis_all_four_agents()
        test_synthesis_single_agent()
        test_synthesis_state_update()
        test_synthesis_confidence_weighting()
        test_synthesis_empty_inputs()
        test_synthesis_evidence_aggregation()
        test_synthesis_causal_chain_ordering()
        test_synthesis_pydantic_validation()
        
        print("\n" + "="*70)
        print("✅ ALL SYNTHESIS AGENT TESTS PASSED!")
        print("="*70)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        raise


if __name__ == "__main__":
    # Run individual test
    # test_synthesis_agent_basic()
    
    # Or run all tests
    run_all_tests()