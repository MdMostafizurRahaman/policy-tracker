import os
import csv
from datetime import datetime
from database import approved_collection
from models import POLICY_TYPES

def generate_policy_data_csv():
    """Generate a CSV file with all approved policies data"""
    try:
        # Get all approved policies
        approved_policies = list(approved_collection.find({}, {"_id": 0}))
        
        # Create CSV file with timestamp to avoid caching issues
        csv_path = f"policy_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Define CSV headers based on policy types
            fieldnames = ['country'] + POLICY_TYPES
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # Write data for each country
            for country_data in approved_policies:
                country = country_data.get('country', 'Unknown')
                row = {'country': country}
                
                # Map each policy to its corresponding type
                for i, policy in enumerate(country_data.get('policies', [])):
                    if i < len(POLICY_TYPES):
                        policy_type = POLICY_TYPES[i]
                        # Mark as 1 if approved policy exists, 0 otherwise
                        has_policy = 1 if (policy.get('file') or policy.get('text')) and policy.get('status') == 'approved' else 0
                        row[policy_type] = has_policy
                
                writer.writerow(row)
        
        return csv_path
    except Exception as e:
        print(f"Error generating CSV: {str(e)}")
        return None

def ensure_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs("temp_policies", exist_ok=True)
    os.makedirs("approved_policies", exist_ok=True)