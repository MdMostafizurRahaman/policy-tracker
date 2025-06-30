"""
Data Conversion Utilities
Handles conversion between different data formats
"""
from bson import ObjectId
from datetime import datetime

def convert_objectid(obj):
    """Convert ObjectId to string recursively"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    return obj

def pydantic_to_dict(obj):
    """Convert Pydantic model to dict recursively"""
    if hasattr(obj, 'dict'):
        return obj.dict()
    elif isinstance(obj, dict):
        return {key: pydantic_to_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [pydantic_to_dict(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj
    else:
        return obj
