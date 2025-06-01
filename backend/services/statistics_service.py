from typing import Dict
from motor.motor_asyncio import AsyncIOMotorCollection

async def get_policy_statistics(master_collection: AsyncIOMotorCollection) -> Dict:
    """Get statistics about policy distribution across countries"""
    try:
        policy_types = [
            "AI Safety", "CyberSafety", "Digital Education", "Digital Inclusion",
            "Digital Leisure", "(Dis)Information", "Digital Work", "Mental Health",
            "Physical Health", "Social Media/Gaming Regulation"
        ]
        
        cursor = master_collection.find({"master_status": {"$ne": "deleted"}})
        
        # Initialize counts
        policy_type_counts = {pt: 0 for pt in policy_types}
        color_counts = {
            "green": 0,
            "yellow": 0,
            "red": 0,
            "gray": 0
        }
        total_countries = set()
        countries_with_policies = set()
        
        async for policy in cursor:
            country = policy.get("country")
            if country:
                total_countries.add(country)
                
                # Count policy types
                policy_area = policy.get("policyArea")
                if policy_area and policy_area in policy_types:
                    policy_type_counts[policy_area] += 1
                    countries_with_policies.add(country)
        
        # Determine most/least common policies
        most_common = max(policy_type_counts.items(), key=lambda x: x[1]) if any(policy_type_counts.values()) else None
        least_common = min(policy_type_counts.items(), key=lambda x: x[1]) if any(policy_type_counts.values()) else None
        
        return {
            "total_countries": len(total_countries),
            "countries_with_policies": len(countries_with_policies),
            "color_distribution": color_counts,
            "policy_type_counts": policy_type_counts,
            "most_common_policy": most_common[0] if most_common else None,
            "least_common_policy": least_common[0] if least_common else None
        }
    except Exception as e:
        raise Exception(f"Error generating policy statistics: {str(e)}")