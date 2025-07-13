"""
File Handling Utilities with AWS S3 Integration
Upload, storage, and retrieval of files using AWS S3 with caching
"""
from fastapi import UploadFile, HTTPException
from config.database import get_files_collection
from services.aws_service import aws_service
from bson import ObjectId
from datetime import datetime
from typing import Dict, Optional, List, Any
import logging
import json

logger = logging.getLogger(__name__)

async def save_file_to_s3(file: UploadFile, metadata: Dict = None) -> Dict[str, Any]:
    """Save uploaded file to AWS S3 with database metadata, fallback to local storage"""
    try:
        # Try AWS S3 first
        try:
            s3_result = await aws_service.upload_file(file, metadata)
            
            # Save metadata to database for tracking
            file_doc = {
                "filename": file.filename,
                "content_type": file.content_type,
                "s3_key": s3_result['s3_key'],
                "file_url": s3_result['file_url'],
                "cdn_url": s3_result['cdn_url'],
                "size": s3_result['size'],
                "etag": s3_result['etag'],
                "upload_date": datetime.utcnow(),
                "storage_type": "s3",
                "metadata": metadata or {}
            }
            
            # Store in database for tracking
            files_collection = get_files_collection()
            result = await files_collection.insert_one(file_doc)
            
            logger.info(f"File uploaded to S3 successfully: {file.filename}")
            
            # Return comprehensive result
            return {
                "file_id": str(result.inserted_id),
                "s3_key": s3_result['s3_key'],
                "file_url": s3_result['file_url'],
                "cdn_url": s3_result['cdn_url'],
                "filename": file.filename,
                "size": s3_result['size'],
                "content_type": file.content_type,
                "upload_date": file_doc['upload_date'].isoformat(),
                "metadata": s3_result['metadata'],
                "storage_type": "s3"
            }
            
        except Exception as s3_error:
            logger.warning(f"S3 upload failed, falling back to local storage: {str(s3_error)}")
            
            # Fallback to local storage
            return await save_file_locally(file, metadata)
            
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

async def save_file_locally(file: UploadFile, metadata: Dict = None) -> Dict[str, Any]:
    """Fallback: Save file to local storage with database metadata"""
    import os
    import shutil
    import uuid
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        local_path = os.path.join(upload_dir, unique_filename)
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Save file locally
        with open(local_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Reset file pointer for any further processing
        await file.seek(0)
        
        # Save metadata to database
        file_doc = {
            "filename": file.filename,
            "content_type": file.content_type,
            "local_path": local_path,
            "file_url": f"/files/{unique_filename}",  # Relative URL for local files
            "size": file_size,
            "upload_date": datetime.utcnow(),
            "storage_type": "local",
            "metadata": metadata or {}
        }
        
        files_collection = get_files_collection()
        result = await files_collection.insert_one(file_doc)
        
        logger.info(f"File uploaded to local storage: {file.filename}")
        
        return {
            "file_id": str(result.inserted_id),
            "local_path": local_path,
            "file_url": file_doc['file_url'],
            "filename": file.filename,
            "size": file_size,
            "content_type": file.content_type,
            "upload_date": file_doc['upload_date'].isoformat(),
            "metadata": metadata or {},
            "storage_type": "local",
            "message": "File uploaded to local storage (S3 unavailable)"
        }
        
    except Exception as e:
        logger.error(f"Error saving file locally: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Local file storage failed: {str(e)}")

async def get_file_from_s3(file_id: str = None, s3_key: str = None) -> Dict[str, Any]:
    """Get file from S3 by file_id or s3_key"""
    try:
        if file_id:
            # Get metadata from database first
            files_collection = get_files_collection()
            file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
            if not file_doc:
                raise HTTPException(status_code=404, detail="File not found in database")
            s3_key = file_doc.get('s3_key')
        
        if not s3_key:
            raise HTTPException(status_code=400, detail="Either file_id or s3_key must be provided")
        
        # Get file from S3
        s3_result = await aws_service.get_file(s3_key)
        
        return {
            "content": s3_result['content'],
            "content_type": s3_result['content_type'],
            "size": s3_result['size'],
            "last_modified": s3_result['last_modified'],
            "metadata": s3_result['metadata']
        }
        
    except Exception as e:
        logger.error(f"Error retrieving file from S3: {str(e)}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

async def get_file_url(file_id: str = None, s3_key: str = None, use_cdn: bool = True) -> str:
    """Get public URL for file (CDN or direct S3)"""
    try:
        if file_id:
            files_collection = get_files_collection()
            file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
            if not file_doc:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Return cached URL if available
            if use_cdn and file_doc.get('cdn_url'):
                return file_doc['cdn_url']
            elif file_doc.get('file_url'):
                return file_doc['file_url']
            
            s3_key = file_doc.get('s3_key')
        
        if not s3_key:
            raise HTTPException(status_code=400, detail="Either file_id or s3_key must be provided")
        
        # Generate URL
        if use_cdn and aws_service.cloudfront_domain:
            return aws_service._generate_cdn_url(s3_key)
        else:
            return aws_service._generate_file_url(s3_key)
            
    except Exception as e:
        logger.error(f"Error generating file URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating URL: {str(e)}")

async def get_presigned_url(file_id: str = None, s3_key: str = None, expiration: int = 3600) -> str:
    """Get presigned URL for secure file access"""
    try:
        if file_id:
            files_collection = get_files_collection()
            file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
            if not file_doc:
                raise HTTPException(status_code=404, detail="File not found")
            s3_key = file_doc.get('s3_key')
        
        if not s3_key:
            raise HTTPException(status_code=400, detail="Either file_id or s3_key must be provided")
        
        return await aws_service.get_presigned_url(s3_key, expiration)
        
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")

async def delete_file(file_id: str = None, s3_key: str = None) -> bool:
    """Delete file from S3 and database"""
    try:
        if file_id:
            files_collection = get_files_collection()
            file_doc = await files_collection.find_one({"_id": ObjectId(file_id)})
            if file_doc:
                s3_key = file_doc.get('s3_key')
                # Delete from database
                await files_collection.delete_one({"_id": ObjectId(file_id)})
        
        if s3_key:
            # Delete from S3
            await aws_service.delete_file(s3_key)
        
        return True
        
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return False

async def list_files(prefix: str = "", limit: int = 100, metadata_filter: Dict = None) -> List[Dict[str, Any]]:
    """List files with optional metadata filtering"""
    try:
        # Get files from database with metadata
        files_collection = get_files_collection()
        query = {"storage_type": "s3"}
        
        if metadata_filter:
            for key, value in metadata_filter.items():
                query[f"metadata.{key}"] = value
        
        cursor = files_collection.find(query).limit(limit)
        files = []
        
        async for file_doc in cursor:
            if not prefix or file_doc.get('s3_key', '').startswith(prefix):
                files.append({
                    "file_id": str(file_doc['_id']),
                    "filename": file_doc['filename'],
                    "s3_key": file_doc['s3_key'],
                    "file_url": file_doc['file_url'],
                    "cdn_url": file_doc.get('cdn_url'),
                    "size": file_doc['size'],
                    "content_type": file_doc['content_type'],
                    "upload_date": file_doc['upload_date'].isoformat(),
                    "metadata": file_doc.get('metadata', {})
                })
        
        return files
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

async def get_storage_stats() -> Dict[str, Any]:
    """Get storage statistics"""
    try:
        # Get S3 bucket stats
        s3_stats = await aws_service.get_bucket_stats()
        
        # Get database stats
        files_collection = get_files_collection()
        db_count = await files_collection.count_documents({"storage_type": "s3"})
        
        return {
            "s3_stats": s3_stats,
            "database_tracked_files": db_count,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

# Legacy functions for backward compatibility
async def save_file_to_db(file: UploadFile, metadata: Dict = None) -> str:
    """Legacy function - redirects to S3"""
    result = await save_file_to_s3(file, metadata)
    return result['file_id']

async def get_file_from_db(file_id: str):
    """Legacy function - redirects to S3"""
    return await get_file_from_s3(file_id=file_id)
