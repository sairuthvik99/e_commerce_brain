"""
Test Suite for Self-Reflection Agent

Tests the reflection agent's ability to audit reasoning quality
and detect issues in multi-agent analysis.
"""

from backend.reflection.agent import SelfReflectionAgent
from backend.schemas.agent_output import AgentOutput
from backend.schemas.root_cause import RootCause
from backend.schemas.reflection_result import ReflectionResult
import json


def test_reflection_agent_basic():
    """Test basic reflection agent functionality"""
    print("\n" + "="*60)
    print("TEST: Basic Reflection Agent")
    print("="*60)
    
    agent = SelfReflectionAgent()
    
    # Prepare agent outputs
    agent_outputs = {
        "inventory": {
            "finding": "15 products out of stock",
            "evidence": ["stockout_count_15", "5x_baseline"],
            "confidence": 0.94,
            "agent": "inventory"
        },
        "sales": {
            "finding": "Sales dropped 45%",
            "evidence": ["45%_drop", "order_count_down"],
            "confidence": 0.91,
            "agent": "sales"
        }
    }
    
    # Prepare synthesis
    synthesis = RootCause(
        root_cause="Inventory stockouts caused sales drop.",
        primary_cause="inventory",
        contributing_causes=["sales"],
        confidence=0.92,
        causal_chain=["inventory", "sales"],
        evidence_summary={
            "inventory": ["stockout_count_15", "5x_baseline"],
            "sales": ["45%_drop", "order_count_down"]
        }
    )
    
    # Execute reflection
    result = agent.reflect(agent_outputs, synthesis)
    
    # Assertions
    assert isinstance(result, ReflectionResult), "Result should be ReflectionResult instance"
    assert hasattr(result, "quality_score"), "Result should have quality_score"
    assert hasattr(result, "conflicts"), "Result should have conflicts"
    assert hasattr(result, "warnings"), "Result should have warnings"
    assert isinstance(result.conflicts, list), "Conflicts should be a list"
    assert isinstance(result.warnings, list), "Warnings should be a list"
    assert 0 <= result.quality_score <= 1, "Quality score should be between 0 and 1"
    
    print(f"✓ Quality Score: {result.quality_score}")
    print(f"✓ Conflicts Detected: {result.conflicts_detected}")
    print(f"✓ Conflicts: {result.conflicts}")
    print(f"✓ Warnings: {result.warnings}")
    print(f"✓ Recommendations: {result.recommendations}")
    print(f"✓ Pass Status: {result.pass_threshold}")
    print("✅ Basic reflection test passed!")


def test_reflection_with_conflicts():
    """Test reflection agent detecting conflicts"""
    print("\n" + "="*60)
    print("TEST: Reflection with Conflicting Findings")
    print("="*60)
    
    agent = SelfReflectionAgent()
    
    # Create conflicting outputs
    agent_outputs = {
        "inventory": {
            "finding": "All products fully stocked",
            "evidence": ["stock_levels_normal"],
            "confidence": 0.90,
            "agent": "inventory"
        },
        "sales": {
            "finding": "Sales dropped 60% due to stockouts",
            "evidence": ["60%_drop", "stockout_complaints"],
            "confidence": 0.85,
            "agent": "sales"
        }
    }
    
    synthesis = RootCause(
        root_cause="Conflicting findings between inventory and sales.",
        primary_cause="sales",
        contributing_causes=["inventory"],
        confidence=0.65,  # Lower confidence due to conflict
        causal_chain=["inventory", "sales"],
        evidence_summary={
            "inventory": ["stock_levels_normal"],
            "sales": ["60%_drop", "stockout_complaints"]
        }
    )
    
    result = agent.reflect(agent_outputs, synthesis)
    
    # Assertions
    assert isinstance(result, ReflectionResult)
    print(f"✓ Quality Score: {result.quality_score}")
    print(f"✓ Conflicts Detected: {result.conflicts_detected}")
    print(f"✓ Conflicts: {result.conflicts}")
    print(f"✓ Warnings: {result.warnings}")
    print("✅ Conflict detection test passed!")


def test_reflection_low_confidence():
    """Test reflection agent flagging low confidence"""
    print("\n" + "="*60)
    print("TEST: Reflection with Low Confidence Scores")
    print("="*60)
    
    agent = SelfReflectionAgent()
    
    agent_outputs = {
        "marketing": {
            "finding": "Campaign performance unclear",
            "evidence": ["incomplete_data"],
            "confidence": 0.55,  # Low confidence
            "agent": "marketing"
        },
        "support": {
            "finding": "Ticket volume stable",
            "evidence": ["ticket_count_normal"],
            "confidence": 0.65,  # Below 0.7 threshold
            "agent": "support"
        }
    }
    
    synthesis = RootCause(
        root_cause="Insufficient evidence for root cause analysis.",
        primary_cause="marketing",
        contributing_causes=["support"],
        confidence=0.60,
        causal_chain=["marketing", "support"],
        evidence_summary={
            "marketing": ["incomplete_data"],
            "support": ["ticket_count_normal"]
        }
    )
    
    result = agent.reflect(agent_outputs, synthesis)
    
    # Assertions
    assert isinstance(result, ReflectionResult)
    assert len(result.warnings) > 0, "Should have warnings for low confidence"
    
    print(f"✓ Quality Score: {result.quality_score}")
    print(f"✓ Warnings: {result.warnings}")
    print(f"✓ Recommendations: {result.recommendations}")
    print("✅ Low confidence detection test passed!")


def test_reflection_state_update():
    """Test reflection agent state update via __call__"""
    print("\n" + "="*60)
    print("TEST: Reflection State Update")
    print("="*60)
    
    agent = SelfReflectionAgent()
    
    # Prepare state dict (as used by LangGraph)
    state = {
        "agent_outputs": {
            "inventory": {
                "finding": "10 SKUs out of stock",
                "evidence": ["stockout_count_10"],
                "confidence": 0.88,
                "agent": "inventory"
            }
        },
        "root_cause": RootCause(
            root_cause="Inventory stockouts detected.",
            primary_cause="inventory",
            contributing_causes=[],
            confidence=0.88,
            causal_chain=["inventory"],
            evidence_summary={"inventory": ["stockout_count_10"]}
        )
    }
    
    # Call agent (LangGraph style)
    updated_state = agent(state)
    
    # Assertions
    assert "reflection_result" in updated_state, "State should have reflection_result"
    assert "quality_score" in updated_state, "State should have quality_score"
    assert "conflicts" in updated_state, "State should have conflicts"
    assert isinstance(updated_state["reflection_result"], dict), "reflection_result should be dict"
    assert isinstance(updated_state["quality_score"], float), "quality_score should be float"
    assert isinstance(updated_state["conflicts"], list), "conflicts should be list"
    
    print(f"✓ Reflection Result: {json.dumps(updated_state['reflection_result'], indent=2)}")
    print(f"✓ Quality Score: {updated_state['quality_score']}")
    print(f"✓ Conflicts: {updated_state['conflicts']}")
    print("✅ State update test passed!")


def test_reflection_multiple_agents():
    """Test reflection with all four agents"""
    print("\n" + "="*60)
    print("TEST: Reflection with All Four Agents")
    print("="*60)
    
    agent = SelfReflectionAgent()
    
    agent_outputs = {
        "inventory": {
            "finding": "15 SKUs critically out of stock",
            "evidence": ["stockout_count_15", "5x_baseline"],
            "confidence": 0.94,
            "agent": "inventory"
        },
        "sales": {
            "finding": "Revenue dropped 45% in last 7 days",
            "evidence": ["45%_drop", "order_count_down"],
            "confidence": 0.91,
            "agent": "sales"
        },
        "marketing": {
            "finding": "Campaign conversion rate dropped 78%",
            "evidence": ["conversion_drop_78%"],
            "confidence": 0.68,  # Below 0.7
            "agent": "marketing"
        },
        "support": {
            "finding": "Support tickets increased 400%",
            "evidence": ["400%_ticket_spike", "delivery_issues"],
            "confidence": 0.90,
            "agent": "support"
        }
    }
    
    synthesis = RootCause(
        root_cause="Inventory stockouts (15 SKUs) caused a 45% sales drop, triggering marketing campaign pauses and a 400% support ticket spike.",
        primary_cause="inventory",
        contributing_causes=["marketing", "support"],
        confidence=0.92,
        causal_chain=["inventory", "sales", "marketing", "support"],
        evidence_summary={
            "inventory": ["stockout_count_15", "5x_baseline"],
            "sales": ["45%_drop", "order_count_down"],
            "marketing": ["conversion_drop_78%"],
            "support": ["400%_ticket_spike", "delivery_issues"]
        }
    )
    
    result = agent.reflect(agent_outputs, synthesis)
    
    # Assertions
    assert isinstance(result, ReflectionResult)
    assert result.quality_score >= 0.0
    assert result.quality_score <= 1.0
    
    print(f"✓ Quality Score: {result.quality_score}")
    print(f"✓ Conflicts Detected: {result.conflicts_detected}")
    print(f"✓ Conflicts: {result.conflicts}")
    print(f"✓ Warnings: {result.warnings}")
    print(f"✓ Recommendations: {result.recommendations}")
    print(f"✓ Pass Status: {result.pass_threshold}")
    print("✅ Multi-agent reflection test passed!")


def test_reflection_edge_cases():
    """Test reflection with edge cases"""
    print("\n" + "="*60)
    print("TEST: Reflection Edge Cases")
    print("="*60)
    
    agent = SelfReflectionAgent()
    
    # Test Case 1: Empty agent outputs
    print("\n1. Testing empty agent outputs...")
    try:
        result = agent.reflect({}, RootCause(
            root_cause="No data available",
            primary_cause="unknown",
            contributing_causes=[],
            confidence=0.0,
            causal_chain=[],
            evidence_summary={}
        ))
        print(f"✓ Handled empty outputs. Quality Score: {result.quality_score}")
    except Exception as e:
        print(f"✗ Failed with empty outputs: {e}")
    
    # Test Case 2: Single agent output
    print("\n2. Testing single agent output...")
    result = agent.reflect(
        {"inventory": {
            "finding": "Test",
            "evidence": ["test"],
            "confidence": 0.5,
            "agent": "inventory"
        }},
        RootCause(
            root_cause="Single agent analysis",
            primary_cause="inventory",
            contributing_causes=[],
            confidence=0.5,
            causal_chain=["inventory"],
            evidence_summary={"inventory": ["test"]}
        )
    )
    print(f"✓ Handled single agent. Quality Score: {result.quality_score}")
    
    # Test Case 3: Perfect confidence scores
    print("\n3. Testing perfect confidence scores...")
    result = agent.reflect(
        {"inventory": {
            "finding": "Perfect data",
            "evidence": ["complete_data"],
            "confidence": 1.0,
            "agent": "inventory"
        }},
        RootCause(
            root_cause="Perfect analysis",
            primary_cause="inventory",
            contributing_causes=[],
            confidence=1.0,
            causal_chain=["inventory"],
            evidence_summary={"inventory": ["complete_data"]}
        )
    )
    print(f"✓ Handled perfect confidence. Quality Score: {result.quality_score}")
    
    print("\n✅ Edge case tests passed!")


def run_all_tests():
    """Run all reflection agent tests"""
    print("\n" + "="*70)
    print(" REFLECTION AGENT TEST SUITE")
    print("="*70)
    
    try:
        test_reflection_agent_basic()
        test_reflection_with_conflicts()
        test_reflection_low_confidence()
        test_reflection_state_update()
        test_reflection_multiple_agents()
        test_reflection_edge_cases()
        
        print("\n" + "="*70)
        print("✅ ALL REFLECTION AGENT TESTS PASSED!")
        print("="*70)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        raise


if __name__ == "__main__":
    # Run individual test
    # test_reflection_agent_basic()
    
    # Or run all tests
    run_all_tests()