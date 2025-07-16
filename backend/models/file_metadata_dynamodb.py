"""
DynamoDB File Metadata Model
Handles file metadata storage in DynamoDB with S3 integration
"""
from typing import Optional, Dict, List, Any
import uuid
from datetime import datetime
from config.dynamodb import get_dynamodb
from boto3.dynamodb.conditions import Key, Attr
import logging

logger = logging.getLogger(__name__)

class FileMetadata:
    """File metadata model for DynamoDB operations"""
    
    def __init__(self, **kwargs):
        self.file_id = kwargs.get('file_id', str(uuid.uuid4()))
        self.user_id = kwargs.get('user_id')
        self.policy_id = kwargs.get('policy_id')
        self.filename = kwargs.get('filename')
        self.original_filename = kwargs.get('original_filename')
        self.file_size = kwargs.get('file_size')
        self.file_type = kwargs.get('file_type')
        self.mime_type = kwargs.get('mime_type')
        self.s3_bucket = kwargs.get('s3_bucket')
        self.s3_key = kwargs.get('s3_key')
        self.s3_url = kwargs.get('s3_url')
        self.file_hash = kwargs.get('file_hash')
        self.upload_status = kwargs.get('upload_status', 'pending')  # pending, uploading, completed, failed
        self.processing_status = kwargs.get('processing_status', 'pending')  # pending, processing, completed, failed
        self.extracted_text = kwargs.get('extracted_text')
        self.ai_analysis = kwargs.get('ai_analysis', {})
        self.tags = kwargs.get('tags', [])
        self.metadata = kwargs.get('metadata', {})
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        self.expires_at = kwargs.get('expires_at')
        self.is_deleted = kwargs.get('is_deleted', False)
        self.download_count = kwargs.get('download_count', 0)
        self.last_accessed = kwargs.get('last_accessed')
    
    def to_dict(self) -> Dict:
        """Convert file metadata object to dictionary"""
        return {
            'file_id': self.file_id,
            'user_id': self.user_id,
            'policy_id': self.policy_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            's3_bucket': self.s3_bucket,
            's3_key': self.s3_key,
            's3_url': self.s3_url,
            'file_hash': self.file_hash,
            'upload_status': self.upload_status,
            'processing_status': self.processing_status,
            'extracted_text': self.extracted_text,
            'ai_analysis': self.ai_analysis,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'expires_at': self.expires_at,
            'is_deleted': self.is_deleted,
            'download_count': self.download_count,
            'last_accessed': self.last_accessed
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileMetadata':
        """Create file metadata object from dictionary"""
        return cls(**data)
    
    async def save(self) -> bool:
        """Save file metadata to DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            self.updated_at = datetime.utcnow().isoformat()
            
            return await dynamodb.insert_item('file_metadata', self.to_dict())
        except Exception as e:
            logger.error(f"Error saving file metadata: {str(e)}")
            return False
    
    async def update(self, update_data: Dict) -> bool:
        """Update file metadata in DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            
            # Update local object
            for key, value in update_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            self.updated_at = datetime.utcnow().isoformat()
            update_data['updated_at'] = self.updated_at
            
            return await dynamodb.update_item(
                'file_metadata', 
                {'file_id': self.file_id}, 
                update_data
            )
        except Exception as e:
            logger.error(f"Error updating file metadata: {str(e)}")
            return False
    
    async def delete(self) -> bool:
        """Soft delete file metadata"""
        try:
            return await self.update({'is_deleted': True})
        except Exception as e:
            logger.error(f"Error deleting file metadata: {str(e)}")
            return False
    
    async def hard_delete(self) -> bool:
        """Hard delete file metadata from DynamoDB"""
        try:
            dynamodb = await get_dynamodb()
            return await dynamodb.delete_item('file_metadata', {'file_id': self.file_id})
        except Exception as e:
            logger.error(f"Error hard deleting file metadata: {str(e)}")
            return False
    
    async def mark_accessed(self) -> bool:
        """Mark file as accessed and increment download count"""
        try:
            update_data = {
                'download_count': self.download_count + 1,
                'last_accessed': datetime.utcnow().isoformat()
            }
            return await self.update(update_data)
        except Exception as e:
            logger.error(f"Error marking file as accessed: {str(e)}")
            return False
    
    @staticmethod
    async def find_by_id(file_id: str) -> Optional['FileMetadata']:
        """Find file metadata by ID"""
        try:
            dynamodb = await get_dynamodb()
            file_data = await dynamodb.get_item('file_metadata', {'file_id': file_id})
            
            if file_data and not file_data.get('is_deleted', False):
                return FileMetadata.from_dict(file_data)
            return None
        except Exception as e:
            logger.error(f"Error finding file metadata by ID: {str(e)}")
            return None
    
    @staticmethod
    async def find_by_user_id(user_id: str, limit: Optional[int] = None) -> List['FileMetadata']:
        """Find file metadata by user ID"""
        try:
            dynamodb = await get_dynamodb()
            files_data = await dynamodb.query_items(
                'file_metadata',
                Key('user_id').eq(user_id),
                index_name='user-created-index',
                limit=limit
            )
            
            # Filter out deleted files
            active_files = [
                file_data for file_data in files_data 
                if not file_data.get('is_deleted', False)
            ]
            
            return [FileMetadata.from_dict(file_data) for file_data in active_files]
        except Exception as e:
            logger.error(f"Error finding file metadata by user ID: {str(e)}")
            return []
    
    @staticmethod
    async def find_by_policy_id(policy_id: str, limit: Optional[int] = None) -> List['FileMetadata']:
        """Find file metadata by policy ID"""
        try:
            dynamodb = await get_dynamodb()
            files_data = await dynamodb.scan_items(
                'file_metadata',
                filter_expression=Attr('policy_id').eq(policy_id) & Attr('is_deleted').eq(False),
                limit=limit
            )
            
            return [FileMetadata.from_dict(file_data) for file_data in files_data]
        except Exception as e:
            logger.error(f"Error finding file metadata by policy ID: {str(e)}")
            return []
    
    @staticmethod
    async def find_by_hash(file_hash: str) -> Optional['FileMetadata']:
        """Find file metadata by hash (for duplicate detection)"""
        try:
            dynamodb = await get_dynamodb()
            files_data = await dynamodb.scan_items(
                'file_metadata',
                filter_expression=Attr('file_hash').eq(file_hash) & Attr('is_deleted').eq(False)
            )
            
            if files_data:
                return FileMetadata.from_dict(files_data[0])
            return None
        except Exception as e:
            logger.error(f"Error finding file metadata by hash: {str(e)}")
            return None
    
    @staticmethod
    async def find_by_status(upload_status: str = None, processing_status: str = None,
                           limit: Optional[int] = None) -> List['FileMetadata']:
        """Find file metadata by status"""
        try:
            dynamodb = await get_dynamodb()
            
            filter_expr = Attr('is_deleted').eq(False)
            
            if upload_status:
                filter_expr = filter_expr & Attr('upload_status').eq(upload_status)
            
            if processing_status:
                filter_expr = filter_expr & Attr('processing_status').eq(processing_status)
            
            files_data = await dynamodb.scan_items(
                'file_metadata',
                filter_expression=filter_expr,
                limit=limit
            )
            
            return [FileMetadata.from_dict(file_data) for file_data in files_data]
        except Exception as e:
            logger.error(f"Error finding file metadata by status: {str(e)}")
            return []
    
    @staticmethod
    async def create_file_metadata(user_id: str, filename: str, file_size: int,
                                 file_type: str, mime_type: str, policy_id: str = None,
                                 s3_bucket: str = None, s3_key: str = None,
                                 file_hash: str = None) -> Optional['FileMetadata']:
        """Create new file metadata"""
        try:
            file_metadata = FileMetadata(
                user_id=user_id,
                policy_id=policy_id,
                filename=filename,
                original_filename=filename,
                file_size=file_size,
                file_type=file_type,
                mime_type=mime_type,
                s3_bucket=s3_bucket,
                s3_key=s3_key,
                file_hash=file_hash
            )
            
            if await file_metadata.save():
                return file_metadata
            return None
        except Exception as e:
            logger.error(f"Error creating file metadata: {str(e)}")
            return None
    
    async def update_upload_status(self, status: str, s3_url: str = None) -> bool:
        """Update upload status"""
        try:
            update_data = {'upload_status': status}
            if s3_url:
                update_data['s3_url'] = s3_url
            
            return await self.update(update_data)
        except Exception as e:
            logger.error(f"Error updating upload status: {str(e)}")
            return False
    
    async def update_processing_status(self, status: str, extracted_text: str = None,
                                     ai_analysis: Dict = None) -> bool:
        """Update processing status"""
        try:
            update_data = {'processing_status': status}
            
            if extracted_text:
                update_data['extracted_text'] = extracted_text
            
            if ai_analysis:
                update_data['ai_analysis'] = ai_analysis
            
            return await self.update(update_data)
        except Exception as e:
            logger.error(f"Error updating processing status: {str(e)}")
            return False
    
    @staticmethod
    async def get_user_storage_usage(user_id: str) -> Dict[str, Any]:
        """Get storage usage statistics for a user"""
        try:
            user_files = await FileMetadata.find_by_user_id(user_id)
            
            total_files = len(user_files)
            total_size = sum(file.file_size or 0 for file in user_files)
            total_downloads = sum(file.download_count for file in user_files)
            
            file_types = {}
            for file in user_files:
                file_type = file.file_type or 'unknown'
                if file_type not in file_types:
                    file_types[file_type] = {'count': 0, 'size': 0}
                file_types[file_type]['count'] += 1
                file_types[file_type]['size'] += file.file_size or 0
            
            return {
                'total_files': total_files,
                'total_size': total_size,
                'total_downloads': total_downloads,
                'file_types': file_types
            }
        except Exception as e:
            logger.error(f"Error getting user storage usage: {str(e)}")
            return {
                'total_files': 0,
                'total_size': 0,
                'total_downloads': 0,
                'file_types': {}
            }
    
    @staticmethod
    async def cleanup_expired_files() -> int:
        """Clean up expired files"""
        try:
            current_time = datetime.utcnow().isoformat()
            dynamodb = await get_dynamodb()
            
            expired_files = await dynamodb.scan_items(
                'file_metadata',
                filter_expression=Attr('expires_at').lt(current_time) & Attr('is_deleted').eq(False)
            )
            
            deleted_count = 0
            for file_data in expired_files:
                file_metadata = FileMetadata.from_dict(file_data)
                if await file_metadata.delete():
                    deleted_count += 1
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up expired files: {str(e)}")
            return 0
