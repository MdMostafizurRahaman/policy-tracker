from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware #Cross-Origin Resource Sharing.
import pandas as pd

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load and preprocess data
df = pd.read_csv("policy_data.csv")
policy_data = {}
for _, row in df.iterrows():
    country = row['Country']
    policies = row.drop('Country').to_dict()
    total = sum(policies.values())
    
    # Determine color category
    if total <= 3:
        color = "#FF0000"  # Red
    elif total <= 7:
        color = "#FFD700"  # Yellow
    else:
        color = "#00AA00"  # Green
    
    policy_data[country] = {
        **policies,
        "total_policies": total,
        "color": color
    }

@app.get("/api/countries")
def get_all_countries():
    return policy_data

@app.get("/api/country/{country_name}")
def get_country(country_name: str):
    return policy_data.get(country_name, {"error": "Country not found"})