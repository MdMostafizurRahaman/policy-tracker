from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
MONGODB_URL = os.getenv("MONODB_URL")  # Note: keeping the original variable name with typo for compatibility

# Initialize MongoDB client
client = MongoClient(MONGODB_URL)
db = client["policy_tracker"]
pending_collection = db["pending_submissions"]
approved_collection = db["approved_policies"]