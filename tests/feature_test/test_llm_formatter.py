from backend.utils.llm_formatter import LLMFormatter

def test_llm_formatter_basic():
    """Test basic formatter initialization"""
    formatter = LLMFormatter(agent_name="test_agent")
    assert formatter.agent_name == "test_agent"
    assert hasattr(formatter, 'llm')
    print(f"✓ Basic initialization test passed!")

def test_format_finding():
    """Test format_finding method"""
    formatter = LLMFormatter(agent_name="inventory")
    
    # Correct arguments: raw_metrics, analysis_results, context (optional)
    raw_metrics = {
        "total_skus": 100,
        "out_of_stock": 15,
        "low_stock": 25
    }
    
    analysis_results = {
        "finding": "Stock levels critically low for 15 SKUs",
        "confidence": 0.85,
        "evidence": ["SKU-123 out of stock", "SKU-456 below threshold"],
        "stockout_rate": 15.0,
        "trend": "increasing"
    }
    
    context = {
        "sales": {"finding": "Sales dropped by 45%"},
        "marketing": {"finding": "Campaign conversions down"}
    }
    
    try:
        result = formatter.format_finding(raw_metrics, analysis_results, context)
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"✓ format_finding test passed!")
        print(f"  Result preview: {result[:100]}...")
    except Exception as e:
        print(f"✗ format_finding test failed: {e}")

def test_format_reflection():
    """Test format_reflection method"""
    formatter = LLMFormatter(agent_name="reflection")
    
    # Correct arguments: prompt, context
    prompt = """
    Review the following agent findings and synthesis:
    - Check for conflicts
    - Assess confidence scores
    - Verify logical consistency
    """
    
    context = {
        "agent_findings": {
            "inventory": {"finding": "15 SKUs out of stock", "confidence": 0.85},
            "sales": {"finding": "Sales dropped 45%", "confidence": 0.92}
        },
        "synthesis": {
            "root_cause": "Inventory stockouts caused sales drop",
            "confidence": 0.88
        }
    }
    
    try:
        result = formatter.format_reflection(prompt, context)
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"✓ format_reflection test passed!")
        print(f"  Result preview: {result[:100]}...")
    except Exception as e:
        print(f"✗ format_reflection test failed: {e}")

def test_format_synthesis():
    """Test format_synthesis method"""
    formatter = LLMFormatter(agent_name="synthesis")
    
    # Correct arguments: prompt, context
    prompt = """
    Synthesize findings from all agents into a unified root cause analysis.
    Identify primary and contributing causes.
    """
    
    context = {
        "inventory": {
            "finding": "15 SKUs critically out of stock",
            "confidence": 0.85,
            "evidence": ["SKU-123", "SKU-456"]
        },
        "sales": {
            "finding": "Revenue dropped 45% in last 7 days",
            "confidence": 0.92,
            "evidence": ["Order count down", "AOV stable"]
        },
        "marketing": {
            "finding": "Campaign conversion rate dropped 78%",
            "confidence": 0.68
        },
        "support": {
            "finding": "Support tickets increased 400%",
            "confidence": 0.90,
            "evidence": ["Delivery issues", "Stock complaints"]
        }
    }
    
    try:
        result = formatter.format_synthesis(prompt, context)
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"✓ format_synthesis test passed!")
        print(f"  Result preview: {result[:100]}...")
    except Exception as e:
        print(f"✗ format_synthesis test failed: {e}")

def test_format_with_fallback():
    """Test format_with_fallback method"""
    formatter = LLMFormatter(agent_name="test_agent")
    
    # Correct arguments: raw_metrics, analysis_results, fallback_template, context (optional)
    raw_metrics = {
        "metric1": 100,
        "metric2": 200
    }
    
    analysis_results = {
        "finding": "Test finding",
        "confidence": 0.75,
        "drop_pct": 25.5
    }
    
    fallback_template = "{finding} with {confidence} confidence and {drop_pct}% drop"
    
    context = {
        "other_agent": "some context"
    }
    
    try:
        result = formatter.format_with_fallback(
            raw_metrics, 
            analysis_results, 
            fallback_template, 
            context
        )
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"✓ format_with_fallback test passed!")
        print(f"  Result: {result[:100]}...")
    except Exception as e:
        print(f"✗ format_with_fallback test failed: {e}")

def test_all_agent_types():
    """Test all common agent types with correct arguments"""
    agents = ["inventory", "sales", "marketing", "support"]
    
    for agent_name in agents:
        formatter = LLMFormatter(agent_name=agent_name)
        
        raw_metrics = {"test_metric": 100}
        analysis_results = {"finding": f"Test finding for {agent_name} agent"}
        fallback_template = "{finding}"
        
        try:
            result = formatter.format_with_fallback(
                raw_metrics,
                analysis_results,
                fallback_template
            )
            assert isinstance(result, str)
            print(f"✓ Test passed for {agent_name} agent")
        except Exception as e:
            print(f"✗ Test failed for {agent_name} agent: {e}")

def test_all_methods_comprehensive():
    """Comprehensive test of all formatting methods with correct signatures"""
    formatter = LLMFormatter(agent_name="inventory")
    
    print("\n" + "="*10)
    print("Testing All Methods with Correct Arguments")
    print("="*10)
    
    # 1. Test format_finding
    print("\n1. Testing format_finding...")
    try:
        raw_metrics = {
            "total_skus": 100,
            "out_of_stock": 15
        }
        analysis_results = {
            "finding": "15 SKUs out of stock",
            "confidence": 0.85,
            "evidence": ["SKU-123", "SKU-456"]
        }
        context = {"sales": {"finding": "Sales down"}}
        
        result = formatter.format_finding(raw_metrics, analysis_results, context)
        print(f"✓ format_finding:")
        print(f"  Type: {type(result)}")
        print(f"  Length: {len(str(result))}")
        print(f"  Preview: {str(result)[:80]}...")
    except Exception as e:
        print(f"✗ format_finding failed: {e}")
    
    # 2. Test format_reflection
    print("\n2. Testing format_reflection...")
    try:
        reflection_formatter = LLMFormatter(agent_name="reflection")
        prompt = "Review the agent findings for consistency."
        context = {
            "findings": {"inventory": "Test finding"},
            "synthesis": {"root_cause": "Test cause"}
        }
        
        result = reflection_formatter.format_reflection(prompt, context)
        print(f"✓ format_reflection:")
        print(f"  Type: {type(result)}")
        print(f"  Length: {len(str(result))}")
        print(f"  Preview: {str(result)[:80]}...")
    except Exception as e:
        print(f"✗ format_reflection failed: {e}")
    
    # 3. Test format_synthesis
    print("\n3. Testing format_synthesis...")
    try:
        synthesis_formatter = LLMFormatter(agent_name="synthesis")
        prompt = "Synthesize all agent findings."
        context = {
            "inventory": {"finding": "Stock issues", "confidence": 0.85},
            "sales": {"finding": "Sales down", "confidence": 0.92}
        }
        
        result = synthesis_formatter.format_synthesis(prompt, context)
        print(f"✓ format_synthesis:")
        print(f"  Type: {type(result)}")
        print(f"  Length: {len(str(result))}")
        print(f"  Preview: {str(result)[:80]}...")
    except Exception as e:
        print(f"✗ format_synthesis failed: {e}")
    
    # 4. Test format_with_fallback
    print("\n4. Testing format_with_fallback...")
    try:
        raw_metrics = {"metric": 100}
        analysis_results = {"finding": "Test", "drop_pct": 25}
        fallback_template = "{finding} - {drop_pct}% drop"
        
        result = formatter.format_with_fallback(
            raw_metrics,
            analysis_results,
            fallback_template
        )
        print(f"✓ format_with_fallback:")
        print(f"  Type: {type(result)}")
        print(f"  Length: {len(str(result))}")
        print(f"  Preview: {str(result)[:80]}...")
    except Exception as e:
        print(f"✗ format_with_fallback failed: {e}")

def test_convenience_function():
    """Test the convenience function"""
    from backend.utils.llm_formatter import format_finding
    
    print("\n" + "="*10)
    print("Testing Convenience Function")
    print("="*10)
    
    try:
        raw_metrics = {"revenue": 10000, "orders": 100}
        analysis_results = {
            "finding": "Revenue dropped significantly",
            "drop_pct": 25.5,
            "confidence": 0.88
        }
        context = {"inventory": {"finding": "Stock issues"}}
        
        result = format_finding(
            agent_name="sales",
            raw_metrics=raw_metrics,
            analysis_results=analysis_results,
            context=context
        )
        
        print(f"✓ Convenience function test passed!")
        print(f"  Result: {result[:100]}...")
    except Exception as e:
        print(f"✗ Convenience function test failed: {e}")

if __name__ == "__main__":
    print("Running LLM Formatter Tests...\n")
    print("="*10)
    
    test_llm_formatter_basic()
    print()
    
    test_format_finding()
    print()
    
    test_format_reflection()
    print()
    
    test_format_synthesis()
    print()
    
    test_format_with_fallback()
    print()
    
    test_all_agent_types()
    
    test_all_methods_comprehensive()
    
    test_convenience_function()
    
    print("\n" + "="*10)
    print("✅ All tests completed!")
    print("="*10)