from bson import ObjectId
from datetime import datetime
from typing import Any, Dict, List

def convert_objectid(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    return obj

def pydantic_to_dict(obj: Any) -> Dict:
    """Convert Pydantic models and other objects to MongoDB-compatible dict"""
    if hasattr(obj, 'dict'):  # Pydantic model
        return obj.dict()
    elif isinstance(obj, dict):
        return {key: pydantic_to_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [pydantic_to_dict(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj
    else:
        return obj