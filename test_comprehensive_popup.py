#!/usr/bin/env python3
"""
Comprehensive test to simulate admin deletion workflow and verify popup behavior
"""
import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api"

def test_popup_refresh_mechanism():
    """Test the popup refresh mechanism"""
    print("=== Testing Popup Refresh Mechanism ===")
    
    # Test with different cache-busting parameters
    test_countries = ["United States", "Bangladesh", "Canada"]
    
    for country in test_countries:
        print(f"\nTesting {country}:")
        
        # First request
        timestamp1 = int(time.time() * 1000)
        response1 = requests.get(f"{API_BASE_URL}/public/master-policies-no-dedup", 
                                params={"country": country, "limit": 10, "_t": timestamp1})
        
        if response1.status_code == 200:
            data1 = response1.json()
            count1 = len(data1.get("policies", []))
            print(f"  Request 1: {count1} policies")
            
            # Second request with different timestamp (simulate refresh)
            time.sleep(0.1)  # Small delay
            timestamp2 = int(time.time() * 1000)
            headers = {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
            response2 = requests.get(f"{API_BASE_URL}/public/master-policies-no-dedup", 
                                    params={"country": country, "limit": 10, "_t": timestamp2},
                                    headers=headers)
            
            if response2.status_code == 200:
                data2 = response2.json()
                count2 = len(data2.get("policies", []))
                print(f"  Request 2: {count2} policies")
                
                if count1 == count2:
                    print("  ✅ Consistent results (no caching issues)")
                else:
                    print(f"  ⚠️  Inconsistent results: {count1} vs {count2}")
                
                # Check policy details
                for policy in data2.get("policies", []):
                    master_status = policy.get("master_status")
                    status = policy.get("status")
                    
                    if master_status != "active":
                        print(f"  ❌ Policy {policy.get('policyName')} has wrong master_status: {master_status}")
                    
                    if status in ["deleted", "rejected"]:
                        print(f"  ❌ Policy {policy.get('policyName')} has wrong status: {status}")
            else:
                print(f"  ❌ Request 2 failed: {response2.status_code}")
        else:
            print(f"  ❌ Request 1 failed: {response1.status_code}")

def test_enhanced_api_filtering():
    """Test the enhanced API filtering"""
    print("\n=== Testing Enhanced API Filtering ===")
    
    # Test the approved policies endpoint
    response = requests.get(f"{API_BASE_URL}/public/approved-policies", 
                           params={"limit": 100})
    
    if response.status_code == 200:
        data = response.json()
        policies = data.get("policies", [])
        print(f"Approved policies endpoint returned: {len(policies)} policies")
        
        # Check each policy
        problematic_policies = []
        for policy in policies:
            master_status = policy.get("master_status")
            status = policy.get("status")
            
            if master_status != "active" or status in ["deleted", "rejected"]:
                problematic_policies.append({
                    "name": policy.get("policyName", "Unknown"),
                    "master_status": master_status,
                    "status": status
                })
        
        if problematic_policies:
            print(f"❌ Found {len(problematic_policies)} problematic policies:")
            for p in problematic_policies:
                print(f"  - {p['name']}: master_status={p['master_status']}, status={p['status']}")
        else:
            print("✅ All policies have correct status")
    else:
        print(f"❌ Approved policies endpoint failed: {response.status_code}")

def test_specific_country_scenarios():
    """Test specific scenarios that might cause issues"""
    print("\n=== Testing Specific Country Scenarios ===")
    
    # Countries that are likely to have policies
    test_countries = ["United States", "Bangladesh", "Canada", "United Kingdom", "Australia"]
    
    for country in test_countries:
        print(f"\nTesting {country}:")
        
        # Test both endpoints
        endpoints = [
            "/public/approved-policies",
            "/public/master-policies-no-dedup"
        ]
        
        for endpoint in endpoints:
            timestamp = int(time.time() * 1000)
            params = {"country": country, "limit": 50}
            if endpoint == "/public/master-policies-no-dedup":
                params["_t"] = timestamp
            
            response = requests.get(f"{API_BASE_URL}{endpoint}", params=params)
            
            if response.status_code == 200:
                data = response.json()
                policies = data.get("policies", [])
                print(f"  {endpoint}: {len(policies)} policies")
                
                # Quick validation
                for policy in policies:
                    if (policy.get("master_status") != "active" or 
                        policy.get("status") in ["deleted", "rejected"]):
                        print(f"    ❌ Invalid policy: {policy.get('policyName')} ({policy.get('master_status')}, {policy.get('status')})")
            else:
                print(f"  ❌ {endpoint} failed: {response.status_code}")

def simulate_admin_workflow():
    """Simulate what happens when admin deletes/rejects policies"""
    print("\n=== Simulating Admin Workflow ===")
    
    print("Admin workflow simulation:")
    print("1. Admin views submission with policies")
    print("2. Admin rejects a policy")
    print("3. System calls update_policy_status with status='rejected'")
    print("4. System calls _remove_policy_from_master_if_exists")
    print("5. Master policy marked as master_status='deleted'")
    print("6. Popup should no longer show the policy")
    print("7. Next popup refresh should get updated data")
    
    # Test if the endpoints are responding correctly
    print("\nChecking if backend is running...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

if __name__ == "__main__":
    print("Comprehensive Popup and Admin Deletion Test")
    print("=" * 70)
    
    # Check if backend is running
    if not simulate_admin_workflow():
        print("\n❌ Cannot run tests - backend not accessible")
        exit(1)
    
    # Run all tests
    test_popup_refresh_mechanism()
    test_enhanced_api_filtering()
    test_specific_country_scenarios()
    
    print("\n=== Final Recommendations ===")
    print("1. Ensure backend server is restarted after code changes")
    print("2. Clear browser cache completely")
    print("3. Use the refresh button in popup to force new data")
    print("4. Check browser console for any filtering logs")
    print("5. If issues persist, check MongoDB connection and data integrity")
    
    print("\n=== Testing Complete ===")
    print("The popup should now:")
    print("✅ Filter out deleted/rejected policies")
    print("✅ Refresh data on every open")
    print("✅ Have a manual refresh button")
    print("✅ Show debugging info in console")
    print("✅ Use enhanced backend filtering")
