#!/usr/bin/env python3
"""
Advanced database test to check for deleted policies still appearing
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def check_database_directly():
    """Check the database directly for any inconsistencies"""
    try:
        # Connect to MongoDB
        MONGODB_URL = os.getenv("MONGODB_URL")
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.policy_tracker
        master_policies = db.master_policies
        
        print("=== Direct Database Analysis ===")
        
        # Check all policies and their statuses
        print("\n1. Checking all master policies...")
        all_policies = []
        async for policy in master_policies.find({}):
            all_policies.append(policy)
        
        print(f"Total policies in master collection: {len(all_policies)}")
        
        # Group by status
        status_counts = {}
        for policy in all_policies:
            status = policy.get("master_status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("Status breakdown:")
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")
        
        # Check for policies that should be hidden but might appear
        print("\n2. Checking for potentially problematic policies...")
        
        problematic = []
        for policy in all_policies:
            master_status = policy.get("master_status")
            regular_status = policy.get("status")
            country = policy.get("country", "Unknown")
            
            # These should NOT appear in popup
            if (master_status == "deleted" or 
                regular_status == "deleted" or 
                regular_status == "rejected"):
                problematic.append({
                    "id": str(policy["_id"]),
                    "name": policy.get("policyName", "Unknown"),
                    "country": country,
                    "master_status": master_status,
                    "status": regular_status
                })
        
        if problematic:
            print(f"Found {len(problematic)} policies that should be hidden:")
            for p in problematic:
                print(f"  - {p['name']} ({p['country']}) - master_status: {p['master_status']}, status: {p['status']}")
        else:
            print("✅ No problematic policies found")
        
        # Test the exact API filter
        print("\n3. Testing API filter logic...")
        active_filter = {"master_status": "active"}
        active_policies = []
        async for policy in master_policies.find(active_filter):
            active_policies.append(policy)
        
        print(f"Policies matching API filter (master_status='active'): {len(active_policies)}")
        
        # Test by country
        test_countries = ["United States", "Bangladesh", "Canada", "United Kingdom"]
        for country in test_countries:
            country_filter = {"master_status": "active", "country": country}
            country_policies = []
            async for policy in master_policies.find(country_filter):
                country_policies.append(policy)
            
            if len(country_policies) > 0:
                print(f"  - {country}: {len(country_policies)} policies")
                # Check if any have wrong status
                for policy in country_policies:
                    if (policy.get("status") in ["deleted", "rejected"] or 
                        policy.get("master_status") == "deleted"):
                        print(f"    ⚠️  Policy {policy.get('policyName')} has wrong status but passed filter!")
        
        client.close()
        
    except Exception as e:
        print(f"Database check error: {e}")

async def test_admin_deletion_process():
    """Test the admin deletion process end-to-end"""
    print("\n=== Testing Admin Deletion Process ===")
    
    # This would require admin authentication, so we'll simulate the logic
    print("Simulating admin deletion workflow:")
    print("1. Admin marks policy as 'rejected' in submission")
    print("2. System should call _remove_policy_from_master_if_exists")
    print("3. Master policy should be marked as master_status='deleted'")
    print("4. API should filter it out")
    print("5. Popup should not show it")
    
    # Check if our new method exists in the service
    try:
        from backend.services.admin_service import AdminService
        admin_service = AdminService()
        
        # Check if the method exists
        if hasattr(admin_service, '_remove_policy_from_master_if_exists'):
            print("✅ _remove_policy_from_master_if_exists method exists")
        else:
            print("❌ _remove_policy_from_master_if_exists method NOT found")
            
    except Exception as e:
        print(f"Could not verify admin service: {e}")

if __name__ == "__main__":
    print("Advanced Policy Deletion Database Test")
    print("=" * 60)
    
    asyncio.run(check_database_directly())
    asyncio.run(test_admin_deletion_process())
