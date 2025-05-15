from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")  # Note: keeping the original variable name with typo for compatibility

# Initialize MongoDB client
client = MongoClient(MONGODB_URL)
db = client["policy_tracker"]
pending_collection = db["pending_submissions"]
approved_collection = db["approved_policies"]

pending_collection.create_index("country", unique=True)
approved_collection.create_index("country", unique=True)