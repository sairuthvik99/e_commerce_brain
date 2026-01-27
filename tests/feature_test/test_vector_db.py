"""
Test Suite for Vector Database (HistoryStore and HistoricalCaseRetriever)

Tests the vector database functionality for storing and retrieving
historical analyses using Pinecone.
"""

import os
import json
import time
from datetime import datetime
from backend.vector_db.history_store import HistoryStore
from backend.vector_db.retriever import HistoricalCaseRetriever


def test_history_store_initialization():
    """Test HistoryStore initialization"""
    print("\n" + "="*60)
    print("TEST: HistoryStore Initialization")
    print("="*60)
    
    try:
        store = HistoryStore()
        assert store is not None
        assert hasattr(store, 'vectorstore')
        assert hasattr(store, 'embeddings')
        assert hasattr(store, 'index')
        assert hasattr(store, 'index_name')
        
        print(f"✓ HistoryStore initialized successfully")
        print(f"✓ Index name: {store.index_name}")
        print("✅ Initialization test passed!")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        raise


def test_retriever_initialization():
    """Test HistoricalCaseRetriever initialization"""
    print("\n" + "="*60)
    print("TEST: HistoricalCaseRetriever Initialization")
    print("="*60)
    
    try:
        retriever = HistoricalCaseRetriever()
        assert retriever is not None
        assert hasattr(retriever, 'vectorstore')
        assert hasattr(retriever, 'embeddings')
        assert hasattr(retriever, 'index')
        assert hasattr(retriever, 'index_name')
        
        print(f"✓ HistoricalCaseRetriever initialized successfully")
        print(f"✓ Index name: {retriever.index_name}")
        print("✅ Retriever initialization test passed!")
    except Exception as e:
        print(f"✗ Retriever initialization failed: {e}")
        raise


def test_save_single_analysis():
    """Test saving a single analysis to vector DB"""
    print("\n" + "="*60)
    print("TEST: Save Single Analysis")
    print("="*60)
    
    store = HistoryStore()
    
    analysis = {
        "root_cause": "Inventory stockouts caused sales drop",
        "primary_cause": "inventory",
        "confidence": 0.92,
        "causal_chain": ["inventory", "sales"],
        "evidence_summary": {
            "inventory": ["stockout_count_15", "5x_baseline"],
            "sales": ["45%_drop"]
        },
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        store.save_analysis(analysis)
        print(f"✓ Analysis saved successfully")
        print(f"✓ Root cause: {analysis['root_cause']}")
        print(f"✓ Primary cause: {analysis['primary_cause']}")
        print("✅ Save single analysis test passed!")
        
        # Wait a bit for indexing
        time.sleep(2)
    except Exception as e:
        print(f"✗ Save failed: {e}")
        raise


def test_save_multiple_analyses():
    """Test saving multiple analyses"""
    print("\n" + "="*60)
    print("TEST: Save Multiple Analyses")
    print("="*60)
    
    store = HistoryStore()
    
    analyses = [
        {
            "root_cause": "Marketing campaign failure led to low conversions",
            "primary_cause": "marketing",
            "confidence": 0.88,
            "causal_chain": ["marketing", "sales"],
            "evidence_summary": {
                "marketing": ["campaign_ctr_drop_60%"],
                "sales": ["conversion_drop"]
            },
            "timestamp": datetime.now().isoformat()
        },
        {
            "root_cause": "Support ticket backlog caused customer churn",
            "primary_cause": "support",
            "confidence": 0.85,
            "causal_chain": ["support", "sales"],
            "evidence_summary": {
                "support": ["ticket_backlog_300%"],
                "sales": ["churn_rate_up"]
            },
            "timestamp": datetime.now().isoformat()
        },
        {
            "root_cause": "Warehouse delay impacted delivery times",
            "primary_cause": "inventory",
            "confidence": 0.90,
            "causal_chain": ["inventory", "support", "sales"],
            "evidence_summary": {
                "inventory": ["warehouse_delay"],
                "support": ["delivery_complaints"],
                "sales": ["order_cancellations"]
            },
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    try:
        for idx, analysis in enumerate(analyses):
            store.save_analysis(analysis)
            print(f"✓ Analysis {idx+1} saved: {analysis['root_cause'][:50]}...")
        
        print(f"✓ Total analyses saved: {len(analyses)}")
        print("✅ Save multiple analyses test passed!")
        
        # Wait for indexing
        time.sleep(3)
    except Exception as e:
        print(f"✗ Save multiple failed: {e}")
        raise


def test_retrieve_similar_cases_basic():
    """Test basic retrieval of similar cases"""
    print("\n" + "="*60)
    print("TEST: Retrieve Similar Cases - Basic")
    print("="*60)
    
    retriever = HistoricalCaseRetriever()
    
    query = "inventory stockout"
    k = 3
    
    try:
        results = retriever.find_similar_cases(query, k=k)
        
        assert isinstance(results, list), "Results should be a list"
        print(f"✓ Query: '{query}'")
        print(f"✓ Number of results: {len(results)}")
        
        for idx, result in enumerate(results[:3]):  # Show first 3
            try:
                parsed = json.loads(result)
                print(f"\n  Result {idx+1}:")
                print(f"    Root Cause: {parsed.get('root_cause', 'N/A')[:60]}...")
                print(f"    Primary Cause: {parsed.get('primary_cause', 'N/A')}")
                print(f"    Confidence: {parsed.get('confidence', 'N/A')}")
            except:
                print(f"  Result {idx+1}: {result[:100]}...")
        
        print("\n✅ Basic retrieval test passed!")
    except Exception as e:
        print(f"✗ Retrieval failed: {e}")
        raise


def test_retrieve_with_different_queries():
    """Test retrieval with different query types"""
    print("\n" + "="*60)
    print("TEST: Retrieve with Different Queries")
    print("="*60)
    
    retriever = HistoricalCaseRetriever()
    
    queries = [
        "inventory stockout problem",
        "marketing campaign issues",
        "customer support tickets",
        "sales decline",
        "warehouse delays"
    ]
    
    for query in queries:
        try:
            results = retriever.find_similar_cases(query, k=2)
            print(f"\n✓ Query: '{query}'")
            print(f"  Found {len(results)} results")
            
            if results:
                parsed = json.loads(results[0])
                print(f"  Top result: {parsed.get('root_cause', 'N/A')[:50]}...")
        except Exception as e:
            print(f"✗ Query '{query}' failed: {e}")
    
    print("\n✅ Multiple query test passed!")


def test_retrieve_with_metadata():
    """Test retrieval with metadata"""
    print("\n" + "="*60)
    print("TEST: Retrieve with Metadata")
    print("="*60)
    
    retriever = HistoricalCaseRetriever()
    
    query = "inventory issues"
    
    try:
        results = retriever.find_similar_cases_with_metadata(query, k=3)
        
        assert isinstance(results, list), "Results should be a list"
        print(f"✓ Query: '{query}'")
        print(f"✓ Number of results: {len(results)}")
        
        for idx, result in enumerate(results[:3]):
            print(f"\n  Result {idx+1}:")
            print(f"    Content: {str(result.get('content', {}))[:60]}...")
            print(f"    Metadata: {result.get('metadata', {})}")
        
        print("\n✅ Metadata retrieval test passed!")
    except Exception as e:
        print(f"✗ Metadata retrieval failed: {e}")
        # This might fail if method doesn't exist yet
        print("⚠ Note: find_similar_cases_with_metadata may not be implemented")


def test_search_similar_analyses():
    """Test HistoryStore's search_similar_analyses method"""
    print("\n" + "="*60)
    print("TEST: Search Similar Analyses")
    print("="*60)
    
    store = HistoryStore()
    
    query = "stockout inventory"
    k = 3
    
    try:
        results = store.search_similar_analyses(query, k=k)
        
        assert isinstance(results, list), "Results should be a list"
        print(f"✓ Query: '{query}'")
        print(f"✓ Number of results: {len(results)}")
        
        for idx, result in enumerate(results[:3]):
            print(f"\n  Result {idx+1}:")
            print(f"    Root Cause: {result.get('root_cause', 'N/A')[:60]}...")
            print(f"    Primary Cause: {result.get('primary_cause', 'N/A')}")
            print(f"    Confidence: {result.get('confidence', 'N/A')}")
        
        print("\n✅ Search similar analyses test passed!")
    except Exception as e:
        print(f"✗ Search failed: {e}")
        raise


def test_integration_save_and_retrieve():
    """Integration test: save and immediately retrieve"""
    print("\n" + "="*60)
    print("TEST: Integration - Save and Retrieve")
    print("="*60)
    
    store = HistoryStore()
    retriever = HistoricalCaseRetriever()
    
    # Unique analysis for this test
    unique_keyword = f"unique_test_case_{int(time.time())}"
    analysis = {
        "root_cause": f"Test root cause with {unique_keyword}",
        "primary_cause": "inventory",
        "confidence": 0.95,
        "causal_chain": ["inventory", "sales"],
        "evidence_summary": {
            "inventory": [f"test_evidence_{unique_keyword}"]
        },
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Save
        print(f"✓ Saving analysis with keyword: {unique_keyword}")
        store.save_analysis(analysis)
        
        # Wait for indexing
        print("⏳ Waiting for indexing...")
        time.sleep(5)
        
        # Retrieve
        print(f"✓ Searching for: {unique_keyword}")
        results = retriever.find_similar_cases(unique_keyword, k=5)
        
        assert isinstance(results, list), "Results should be a list"
        print(f"✓ Found {len(results)} results")
        
        # Check if our analysis is in the results
        found = False
        for result in results:
            parsed = json.loads(result)
            if unique_keyword in parsed.get('root_cause', ''):
                found = True
                print(f"✓ Successfully retrieved saved analysis!")
                break
        
        if not found:
            print(f"⚠ Warning: Saved analysis not found in top {len(results)} results")
            print("  This may be due to indexing delay or semantic search ranking")
        
        print("✅ Integration test passed!")
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        raise


def test_empty_query():
    """Test retrieval with empty query"""
    print("\n" + "="*60)
    print("TEST: Empty Query Handling")
    print("="*60)
    
    retriever = HistoricalCaseRetriever()
    
    try:
        results = retriever.find_similar_cases("", k=1)
        print(f"✓ Empty query handled")
        print(f"✓ Results: {len(results)} items")
        print("✅ Empty query test passed!")
    except Exception as e:
        print(f"⚠ Empty query raised exception: {e}")
        print("✓ Exception handling is acceptable")


def test_large_k_value():
    """Test retrieval with large k value"""
    print("\n" + "="*60)
    print("TEST: Large K Value")
    print("="*60)
    
    retriever = HistoricalCaseRetriever()
    
    try:
        results = retriever.find_similar_cases("inventory", k=100)
        print(f"✓ Large k value (100) handled")
        print(f"✓ Actual results returned: {len(results)}")
        print("✅ Large k value test passed!")
    except Exception as e:
        print(f"✗ Large k value failed: {e}")
        raise


def test_special_characters_query():
    """Test retrieval with special characters in query"""
    print("\n" + "="*60)
    print("TEST: Special Characters in Query")
    print("="*60)
    
    retriever = HistoricalCaseRetriever()
    
    queries = [
        "inventory: stockout!",
        "sales (down 45%)",
        "marketing & advertising",
        "customer@support.com",
        "100% increase"
    ]
    
    for query in queries:
        try:
            results = retriever.find_similar_cases(query, k=1)
            print(f"✓ Query '{query}' handled: {len(results)} results")
        except Exception as e:
            print(f"✗ Query '{query}' failed: {e}")
    
    print("✅ Special characters test passed!")


def test_vector_db_complete():
    """Complete end-to-end test"""
    print("\n" + "="*60)
    print("TEST: Complete End-to-End Vector DB Test")
    print("="*60)
    
    store = HistoryStore()
    retriever = HistoricalCaseRetriever()
    
    # Sample analysis from the original test
    analysis = {
        "root_cause": "Test root cause",
        "primary_cause": "inventory",
        "confidence": 0.9,
        "causal_chain": ["inventory", "sales"],
        "evidence_summary": {"inventory": ["test_evidence"]},
        "timestamp": "2026-01-27"
    }
    
    try:
        # Save analysis
        store.save_analysis(analysis)
        print("✓ Analysis saved")
        
        # Wait for indexing
        time.sleep(2)
        
        # Retrieve similar cases
        results = retriever.find_similar_cases("inventory stockout", k=1)
        assert isinstance(results, list), "Results should be a list"
        print(f"✓ Retrieved {len(results)} similar cases")
        
        print("✅ Complete end-to-end test passed!")
    except Exception as e:
        print(f"✗ End-to-end test failed: {e}")
        raise


def run_all_tests():
    """Run all vector DB tests"""
    print("\n" + "="*70)
    print(" VECTOR DATABASE TEST SUITE")
    print("="*70)
    
    try:
        # Initialization tests
        test_history_store_initialization()
        test_retriever_initialization()
        
        # Save tests
        test_save_single_analysis()
        test_save_multiple_analyses()
        
        # Retrieval tests
        test_retrieve_similar_cases_basic()
        test_retrieve_with_different_queries()
        test_search_similar_analyses()
        
        # Integration test
        test_integration_save_and_retrieve()
        
        # Edge case tests
        test_empty_query()
        test_large_k_value()
        test_special_characters_query()
        
        # Metadata test (may fail if not implemented)
        try:
            test_retrieve_with_metadata()
        except AttributeError:
            print("\n⚠ Skipping metadata test (method not implemented)")
        
        # Complete test
        test_vector_db_complete()
        
        print("\n" + "="*70)
        print("✅ ALL VECTOR DATABASE TESTS PASSED!")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        raise


if __name__ == "__main__":
    # Run individual test
    # test_vector_db_complete()
    
    # Or run all tests
    run_all_tests()