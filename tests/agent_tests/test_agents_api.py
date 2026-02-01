"""
Test Agents via FastAPI Endpoints

Tests all agents by calling the FastAPI backend API endpoints.
Assumes the FastAPI server is already running on localhost:8000.
"""

import sys
import os
import time
import requests

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"


def submit_analysis(question: str) -> dict:
    """Submit an analysis request to the API."""
    payload = {"question": question}
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    return response


def wait_for_job_completion(job_id: str, max_wait: int = 120, poll_interval: int = 3) -> dict:
    """
    Poll the job status until completion.
    
    Args:
        job_id: The job ID to monitor
        max_wait: Maximum wait time in seconds
        poll_interval: Polling interval in seconds
        
    Returns:
        Final job status response
    """
    elapsed = 0
    while elapsed < max_wait:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}")
        if response.status_code == 200:
            job_data = response.json()
            status = job_data.get("status")
            print(f"    Status: {status} (elapsed: {elapsed}s)")
            
            if status in ["completed", "failed", "error"]:
                return job_data
        else:
            print(f"    Error getting status: {response.status_code}")
        
        time.sleep(poll_interval)
        elapsed += poll_interval
    
    return {"status": "timeout", "error": f"Job did not complete within {max_wait} seconds"}


def test_general_agent_api():
    """Test General Agent via API with 'Hi' input."""
    print("=" * 60)
    print("Testing General Agent via API")
    print("=" * 60)
    
    payload = {
        "question": "Hi, how are you doing today?"
    }
    
    print(f"\n[1] Submitting analysis request: '{payload['question']}'")
    
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    
    print(f"    Response Status: {response.status_code}")
    
    if response.status_code == 202:
        data = response.json()
        job_id = data.get("job_id")
        print(f"    Job ID: {job_id}")
        
        print("\n[2] Waiting for job completion...")
        result = wait_for_job_completion(job_id)
        
        print("\n[3] Final Result:")
        print("-" * 40)
        print(f"    Status: {result.get('status')}")
        if result.get('result'):
            print(f"    Intent: {result.get('result', {}).get('intent')}")
            agent_outputs = result.get('result', {}).get('agent_outputs', {})
            if 'general' in agent_outputs:
                print(f"    General Agent Finding: {agent_outputs['general'].get('finding', 'N/A')[:200]}...")
        print("-" * 40)
        print("\n✅ General Agent API test completed!")
    else:
        print(f"    Error: {response.text}")
        print("\n❌ General Agent API test failed!")
    
    print("=" * 60)
    return response


def test_inventory_agent_api():
    """Test Inventory Agent via API."""
    print("=" * 60)
    print("Testing Inventory Agent via API")
    print("=" * 60)
    
    payload = {
        "question": "What products are currently out of stock or have low inventory levels?"
    }
    
    print(f"\n[1] Submitting analysis request: '{payload['question']}'")
    
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    
    print(f"    Response Status: {response.status_code}")
    
    if response.status_code == 202:
        data = response.json()
        job_id = data.get("job_id")
        print(f"    Job ID: {job_id}")
        
        print("\n[2] Waiting for job completion...")
        result = wait_for_job_completion(job_id)
        
        print("\n[3] Final Result:")
        print("-" * 40)
        print(f"    Status: {result.get('status')}")
        if result.get('result'):
            print(f"    Intent: {result.get('result', {}).get('intent')}")
            agent_outputs = result.get('result', {}).get('agent_outputs', {})
            if 'inventory' in agent_outputs:
                print(f"    Inventory Agent Finding: {agent_outputs['inventory'].get('finding', 'N/A')[:200]}...")
        print("-" * 40)
        print("\n✅ Inventory Agent API test completed!")
    else:
        print(f"    Error: {response.text}")
        print("\n❌ Inventory Agent API test failed!")
    
    print("=" * 60)
    return response


def test_sales_agent_api():
    """Test Sales Agent via API."""
    print("=" * 60)
    print("Testing Sales Agent via API")
    print("=" * 60)
    
    payload = {
        "question": "What is our sales performance for the last 7 days? Are there any concerning trends?"
    }
    
    print(f"\n[1] Submitting analysis request: '{payload['question']}'")
    
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    
    print(f"    Response Status: {response.status_code}")
    
    if response.status_code == 202:
        data = response.json()
        job_id = data.get("job_id")
        print(f"    Job ID: {job_id}")
        
        print("\n[2] Waiting for job completion...")
        result = wait_for_job_completion(job_id)
        
        print("\n[3] Final Result:")
        print("-" * 40)
        print(f"    Status: {result.get('status')}")
        if result.get('result'):
            print(f"    Intent: {result.get('result', {}).get('intent')}")
            agent_outputs = result.get('result', {}).get('agent_outputs', {})
            if 'sales' in agent_outputs:
                print(f"    Sales Agent Finding: {agent_outputs['sales'].get('finding', 'N/A')[:200]}...")
        print("-" * 40)
        print("\n✅ Sales Agent API test completed!")
    else:
        print(f"    Error: {response.text}")
        print("\n❌ Sales Agent API test failed!")
    
    print("=" * 60)
    return response


def test_marketing_agent_api():
    """Test Marketing Agent via API."""
    print("=" * 60)
    print("Testing Marketing Agent via API")
    print("=" * 60)
    
    payload = {
        "question": "How are our marketing campaigns performing? What is the current conversion rate and ROI?"
    }
    
    print(f"\n[1] Submitting analysis request: '{payload['question']}'")
    
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    
    print(f"    Response Status: {response.status_code}")
    
    if response.status_code == 202:
        data = response.json()
        job_id = data.get("job_id")
        print(f"    Job ID: {job_id}")
        
        print("\n[2] Waiting for job completion...")
        result = wait_for_job_completion(job_id)
        
        print("\n[3] Final Result:")
        print("-" * 40)
        print(f"    Status: {result.get('status')}")
        if result.get('result'):
            print(f"    Intent: {result.get('result', {}).get('intent')}")
            agent_outputs = result.get('result', {}).get('agent_outputs', {})
            if 'marketing' in agent_outputs:
                print(f"    Marketing Agent Finding: {agent_outputs['marketing'].get('finding', 'N/A')[:200]}...")
        print("-" * 40)
        print("\n✅ Marketing Agent API test completed!")
    else:
        print(f"    Error: {response.text}")
        print("\n❌ Marketing Agent API test failed!")
    
    print("=" * 60)
    return response


def test_support_agent_api():
    """Test Support Agent via API."""
    print("=" * 60)
    print("Testing Support Agent via API")
    print("=" * 60)
    
    payload = {
        "question": "What are the most common customer complaints? Are there any spikes in support tickets?"
    }
    
    print(f"\n[1] Submitting analysis request: '{payload['question']}'")
    
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    
    print(f"    Response Status: {response.status_code}")
    
    if response.status_code == 202:
        data = response.json()
        job_id = data.get("job_id")
        print(f"    Job ID: {job_id}")
        
        print("\n[2] Waiting for job completion...")
        result = wait_for_job_completion(job_id)
        
        print("\n[3] Final Result:")
        print("-" * 40)
        print(f"    Status: {result.get('status')}")
        if result.get('result'):
            print(f"    Intent: {result.get('result', {}).get('intent')}")
            agent_outputs = result.get('result', {}).get('agent_outputs', {})
            if 'support' in agent_outputs:
                print(f"    Support Agent Finding: {agent_outputs['support'].get('finding', 'N/A')[:200]}...")
        print("-" * 40)
        print("\n✅ Support Agent API test completed!")
    else:
        print(f"    Error: {response.text}")
        print("\n❌ Support Agent API test failed!")
    
    print("=" * 60)
    return response


def test_supervisor_agent_api():
    """Test Supervisor Agent intent detection via API by checking the intent in response."""
    print("=" * 60)
    print("Testing Supervisor Agent via API (Intent Detection)")
    print("=" * 60)
    
    # Test with different queries to verify intent classification (minimum 10 chars)
    test_cases = [
        ("Why did sales drop last week in our store?", "sales"),
        ("What products are currently out of stock?", "inventory"),
        ("How are our marketing campaigns performing?", "marketing"),
        ("What are the customer complaints about?", "support"),
        ("Give me a business overview of operations", "general"),
    ]
    
    results = []
    
    for question, expected_intent in test_cases:
        print(f"\n[Test] Question: '{question}'")
        print(f"       Expected Intent: {expected_intent}")
        
        payload = {"question": question}
        response = requests.post(f"{BASE_URL}/analyze", json=payload)
        
        if response.status_code == 202:
            data = response.json()
            job_id = data.get("job_id")
            
            # Wait a bit for supervisor to process
            time.sleep(2)
            
            job_response = requests.get(f"{BASE_URL}/jobs/{job_id}")
            if job_response.status_code == 200:
                job_data = job_response.json()
                result_data = job_data.get("result") or {}
                detected_intent = result_data.get("intent", "unknown") if result_data else "unknown"
                match = "✅" if detected_intent == expected_intent else "⚠️"
                print(f"       {match} Detected Intent: {detected_intent}")
                results.append((question, expected_intent, detected_intent))
            else:
                print(f"       ❌ Job status check failed: {job_response.status_code}")
                results.append((question, expected_intent, "error"))
        else:
            print(f"       ❌ Request failed: {response.status_code}")
            results.append((question, expected_intent, "error"))
    
    print("\n" + "=" * 60)
    print("Supervisor Test Summary:")
    print("-" * 40)
    for q, expected, got in results:
        match = "✅" if expected == got else "❌"
        print(f"  {match} '{q[:40]}...' → Expected: {expected}, Got: {got}")
    print("-" * 40)
    print("\n✅ Supervisor Agent API test completed!")
    print("=" * 60)
    
    return results


def run_all_api_tests():
    """Run all API tests sequentially."""
    print("\n" + "🚀" * 30)
    print(" RUNNING ALL AGENT API TESTS")
    print("🚀" * 30 + "\n")
    
    # Check if API is accessible
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ API is not accessible. Make sure the FastAPI server is running.")
            return
        print("✅ API is accessible\n")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the FastAPI server is running on http://localhost:8000")
        return
    
    # Run tests sequentially
    test_general_agent_api()
    print("\n")
    
    test_inventory_agent_api()
    print("\n")
    
    test_sales_agent_api()
    print("\n")
    
    test_marketing_agent_api()
    print("\n")
    
    test_support_agent_api()
    print("\n")
    
    test_supervisor_agent_api()
    
    print("\n" + "🎉" * 30)
    print(" ALL API TESTS COMPLETED!")
    print("🎉" * 30 + "\n")


if __name__ == "__main__":
    run_all_api_tests()
