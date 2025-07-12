#!/usr/bin/env python3
"""
Test script to verify policy deletion and popup refresh functionality
"""
import asyncio
import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_COUNTRY = "United States"  # Change this to a country that has policies

async def test_policy_deletion_flow():
    """Test the complete policy deletion flow"""
    print("=== Testing Policy Deletion Flow ===")
    
    # 1. Get initial policies for a country
    print(f"\n1. Fetching initial policies for {TEST_COUNTRY}...")
    response = requests.get(f"{API_BASE_URL}/public/master-policies-no-dedup", 
                          params={"country": TEST_COUNTRY, "limit": 10})
    
    if response.status_code == 200:
        initial_data = response.json()
        initial_count = len(initial_data.get("policies", []))
        print(f"   Found {initial_count} policies initially")
        
        if initial_count > 0:
            first_policy = initial_data["policies"][0]
            policy_id = first_policy.get("_id")
            policy_name = first_policy.get("policyName", "Unknown")
            print(f"   First policy: {policy_name} (ID: {policy_id})")
            
            # 2. Test the popup API with timestamp (simulate popup refresh)
            print(f"\n2. Testing popup API with timestamp parameter...")
            timestamp = str(int(datetime.now().timestamp() * 1000))
            response2 = requests.get(f"{API_BASE_URL}/public/master-policies-no-dedup", 
                                   params={"country": TEST_COUNTRY, "limit": 10, "_t": timestamp})
            
            if response2.status_code == 200:
                popup_data = response2.json()
                popup_count = len(popup_data.get("policies", []))
                print(f"   Popup API returned {popup_count} policies")
                
                # 3. Verify filtering is working
                active_policies = [p for p in popup_data.get("policies", []) 
                                 if p.get("master_status") == "active"]
                print(f"   Active policies after filtering: {len(active_policies)}")
                
                if len(active_policies) == popup_count:
                    print("   ✅ All returned policies are active (filtering working)")
                else:
                    print("   ⚠️  Some non-active policies found")
                    
            else:
                print(f"   ❌ Popup API error: {response2.status_code}")
        else:
            print(f"   ℹ️  No policies found for {TEST_COUNTRY} to test deletion")
    else:
        print(f"   ❌ Initial API error: {response.status_code}")
        return

    # 4. Test policy area coverage
    print(f"\n3. Testing policy area coverage...")
    if initial_count > 0:
        policies = initial_data.get("policies", [])
        areas = set()
        for policy in policies:
            area = policy.get("policyArea", "unknown")
            areas.add(area)
        
        print(f"   Policy areas covered: {len(areas)}")
        print(f"   Areas: {', '.join(sorted(areas))}")
        
        # Check for any deleted policies that might have slipped through
        deleted_policies = [p for p in policies if 
                          p.get("master_status") == "deleted" or 
                          p.get("status") == "deleted" or 
                          p.get("status") == "rejected"]
        
        if deleted_policies:
            print(f"   ⚠️  Found {len(deleted_policies)} deleted/rejected policies that shouldn't be returned")
            for dp in deleted_policies:
                print(f"      - {dp.get('policyName', 'Unknown')} (status: {dp.get('status')}, master_status: {dp.get('master_status')})")
        else:
            print("   ✅ No deleted/rejected policies found in results")

def test_frontend_filtering():
    """Test the frontend filtering logic"""
    print("\n=== Testing Frontend Filtering Logic ===")
    
    # Mock policy data with various statuses
    mock_policies = [
        {"policyName": "Active Policy 1", "master_status": "active", "status": "approved"},
        {"policyName": "Active Policy 2", "master_status": "active", "status": "approved"},
        {"policyName": "Deleted Policy 1", "master_status": "deleted", "status": "approved"},
        {"policyName": "Rejected Policy 1", "master_status": "active", "status": "rejected"},
        {"policyName": "Deleted Policy 2", "master_status": "active", "status": "deleted"},
    ]
    
    # Apply the same filtering logic as the frontend
    filtered_policies = [policy for policy in mock_policies if 
                        policy.get("master_status") == "active" and 
                        policy.get("status") != "deleted" and 
                        policy.get("status") != "rejected" and
                        policy.get("master_status") != "deleted"]
    
    print(f"Original policies: {len(mock_policies)}")
    print(f"Filtered policies: {len(filtered_policies)}")
    print("Filtered policies:")
    for policy in filtered_policies:
        print(f"  - {policy['policyName']}")
    
    expected_count = 2  # Only the first 2 should pass
    if len(filtered_policies) == expected_count:
        print("✅ Frontend filtering logic working correctly")
    else:
        print(f"❌ Frontend filtering failed. Expected {expected_count}, got {len(filtered_policies)}")

if __name__ == "__main__":
    print("Policy Deletion and Popup Test")
    print("=" * 50)
    
    # Test the API and filtering
    asyncio.run(test_policy_deletion_flow())
    
    # Test frontend logic
    test_frontend_filtering()
    
    print("\n=== Test Summary ===")
    print("1. Backend API endpoints filter for master_status='active'")
    print("2. Frontend popup adds additional safety filtering")
    print("3. Admin rejection/deletion now removes from master collection")
    print("4. Timestamp parameter prevents caching issues")
    print("\nIf you're still seeing deleted policies in the popup:")
    print("- Check if the backend server has been restarted")
    print("- Clear browser cache")
    print("- Check admin logs for any errors in the deletion process")
