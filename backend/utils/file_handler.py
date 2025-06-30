"""
File Handling Utilities
Upload, storage, and retrieval of files
"""
from fastapi import UploadFile, HTTPException
from config.database import get_files_collection
from bson import ObjectId
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

async def save_file_to_db(file: UploadFile, metadata: Dict = None) -> str:
    """Save uploaded file to database"""
    try:
        file_content = await file.read()
        await file.seek(0)
        
        file_doc = {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_data": file_content,
            "size": len(file_content),
            "upload_date": datetime.utcnow(),
            **(metadata or {})
        }
        
        files_collection = get_files_collection()
        result = await files_collection.insert_one(file_doc)
        logger.info(f"File saved to database: {file.filename} (ID: {result.inserted_id})")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error saving file to database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

async def get_file_from_db(file_id: str):
    """Get file from database"""
    try:
        files_collection = get_files_collection()
        file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        return file_doc
    except Exception as e:
        logger.error(f"Error retrieving file: {str(e)}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
