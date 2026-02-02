"""
Test script for agent table access permissions.

Run this script to verify that each agent only has access to their designated tables.
"""

import sys
sys.path.insert(0, "c:\\Users\\DevavarapuSaiRuthvik\\Desktop\\E-Commerce_Brain\\e_commerce_brain")

from backend.database.permissions import (
    get_allowed_tables,
    has_table_access,
    get_allowed_data_methods,
    can_use_data_method
)


def test_permissions():
    """Test that each agent has correct table access."""
    
    print("=" * 60)
    print("Agent Table Access Permissions Test")
    print("=" * 60)
    
    # Expected permissions
    expected = {
        "sales": {"daily_metrics", "orders"},
        "marketing": {"daily_metrics", "marketing_campaigns_daily"},
        "inventory": {"daily_metrics", "inventory_snapshots"},
        "support": {"daily_metrics", "support_tickets"},
        "general": {"orders", "daily_metrics", "inventory_snapshots", 
                   "marketing_campaigns_daily", "support_tickets"},
    }
    
    all_passed = True
    
    for agent, expected_tables in expected.items():
        actual_tables = get_allowed_tables(agent)
        
        if actual_tables == expected_tables:
            print(f"✓ {agent.upper()} agent: {actual_tables}")
        else:
            print(f"✗ {agent.upper()} agent FAILED!")
            print(f"  Expected: {expected_tables}")
            print(f"  Actual:   {actual_tables}")
            all_passed = False
    
    print("\n" + "=" * 60)
    print("Data Loader Method Access Test")
    print("=" * 60)
    
    # Test method access
    method_tests = [
        # (agent, method, should_have_access)
        ("sales", "load_sales_data", True),
        ("sales", "load_marketing_data", False),
        ("sales", "load_support_data", False),
        ("sales", "load_inventory_data", False),
        
        ("marketing", "load_marketing_data", True),
        ("marketing", "load_sales_data", False),
        ("marketing", "load_support_data", False),
        
        ("inventory", "load_inventory_data", True),
        ("inventory", "load_inventory_baseline", True),
        ("inventory", "load_sales_data", False),
        
        ("support", "load_support_data", True),
        ("support", "load_sales_data", False),
        ("support", "load_marketing_data", False),
        
        ("general", "load_sales_data", True),
        ("general", "load_marketing_data", True),
        ("general", "load_inventory_data", True),
        ("general", "load_support_data", True),
    ]
    
    for agent, method, expected_access in method_tests:
        actual_access = can_use_data_method(agent, method)
        
        if actual_access == expected_access:
            status = "✓" if expected_access else "✓ (blocked)"
            print(f"{status} {agent}.{method}")
        else:
            print(f"✗ FAILED: {agent}.{method}")
            print(f"  Expected access: {expected_access}, Got: {actual_access}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    test_permissions()
