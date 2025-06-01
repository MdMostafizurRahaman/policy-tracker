from fastapi import UploadFile, HTTPException
from bson import ObjectId
from datetime import datetime
from typing import Dict, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
import mimetypes

async def save_file_to_db(collection: AsyncIOMotorCollection, file: UploadFile, metadata: Dict = None) -> str:
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
        
        result = await collection.insert_one(file_doc)
        return str(result.inserted_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

async def get_file_from_db(collection: AsyncIOMotorCollection, file_id: str) -> Dict:
    try:
        file_doc = await collection.find_one({"_id": ObjectId(file_id)})
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        return file_doc
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

def validate_file(file: UploadFile) -> None:
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds 10MB limit")
    
    allowed_types = [
        'application/pdf', 
        'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="File type not supported. Please upload PDF, DOC, DOCX, or TXT files.")