"""
AWS S3 Service for Professional File Storage, Caching, and CDN Integration
Handles file uploads, storage, caching, and optimized delivery
"""
import boto3
import os
import hashlib
import mimetypes
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from fastapi import UploadFile, HTTPException
from botocore.exceptions import ClientError, NoCredentialsError
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import redis
from PIL import Image
import io
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from the backend directory
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
env_path = backend_dir / '.env'

# Try multiple locations for the .env file
env_locations = [
    env_path,  # backend/.env
    current_dir / '.env',  # services/.env
    Path.cwd() / '.env',  # current working directory
    Path.cwd() / 'backend' / '.env'  # cwd/backend/.env
]

env_loaded = False
for env_location in env_locations:
    if env_location.exists():
        load_dotenv(dotenv_path=env_location)
        logger.info(f"Loaded environment variables from: {env_location}")
        env_loaded = True
        break

if not env_loaded:
    # Fallback: try to load from any .env file in the environment
    load_dotenv()
    logger.warning("No .env file found in expected locations, using system environment variables")

class AWSService:
    def __init__(self):
        # Load environment variables
        logger.info("Initializing AWS Service...")
        
        # Force reload environment variables to ensure they're available
        self._ensure_env_loaded()
        
        # AWS Configuration - Environment variables loaded from backend/.env
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')  # -> AWS_ACCESS_KEY_ID in .env
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')  # -> AWS_SECRET_ACCESS_KEY in .env
        self.aws_region = os.getenv('AWS_REGION')  # -> AWS_REGION in .env
        self.bucket_name = os.getenv('AWS_S3_BUCKET')  # -> AWS_S3_BUCKET in .env
        self.cloudfront_domain = os.getenv('CLOUDFRONT_DOMAIN', '')  # -> CLOUDFRONT_DOMAIN in .env
        
        # Debug: Log what we found (masked for security)
        logger.info(f"AWS Access Key: {'SET' if self.aws_access_key else 'NOT SET'}")
        logger.info(f"AWS Secret Key: {'SET' if self.aws_secret_key else 'NOT SET'}")
        logger.info(f"AWS Region: {self.aws_region}")
        logger.info(f"S3 Bucket: {self.bucket_name}")
        

        # Validate required configuration
        missing_config = []
        if not self.aws_access_key:
            missing_config.append('AWS_ACCESS_KEY_ID')
        if not self.aws_secret_key:
            missing_config.append('AWS_SECRET_ACCESS_KEY')
        if not self.aws_region:
            missing_config.append('AWS_REGION')
        if not self.bucket_name:
            missing_config.append('AWS_S3_BUCKET')
            
        if missing_config:
            error_msg = f"Missing required AWS environment variables: {', '.join(missing_config)}"
            logger.error(error_msg)
            logger.error("Please ensure these variables are set in your .env file")
            # Don't raise an exception here to allow the application to start
            # but the service won't work properly
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            self.s3_resource = boto3.resource(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        
        # Initialize Redis for caching (optional)
        try:
            # Create Redis client but don't test connection during init
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True,
                socket_connect_timeout=1,  # Quick timeout
                socket_timeout=1
            )
            self.cache_enabled = True
            logger.info("Redis client created, caching enabled (will test on first use)")
        except Exception as e:
            logger.warning(f"Redis client creation failed ({str(e)}), caching disabled")
            self.redis_client = None
            self.cache_enabled = False
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # File type configurations
        self.allowed_file_types = {
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
            'data': ['.csv', '.xlsx', '.json', '.xml'],
            'archives': ['.zip', '.tar', '.gz']
        }
        
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        
    def _test_redis_connection(self):
        """Test Redis connection on first use and disable if it fails"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis connection test failed: {e}, disabling cache")
            self.cache_enabled = False
            self.redis_client = None
            return False

    def _ensure_env_loaded(self):
        """Ensure environment variables are loaded, try multiple approaches"""
        # Try to reload from the most likely location
        current_dir = Path(__file__).parent
        backend_dir = current_dir.parent
        env_path = backend_dir / '.env'
        
        if env_path.exists():
            logger.info(f"Force-loading environment from: {env_path}")
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            # Fallback to default loading
            load_dotenv(override=True)

    async def initialize(self):
        """Async initialization method for startup"""
        try:
            # Verify bucket exists and is accessible
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.ensure_bucket_exists_sync
            )
            logger.info(f"AWS S3 service initialized successfully with bucket: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"AWS S3 service startup failed (will continue without S3): {e}")
    
    def ensure_bucket_exists_sync(self):
        """Check if S3 bucket is accessible (don't try to create)"""
        try:
            # Check if bucket exists and is accessible
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' is accessible")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket '{self.bucket_name}' does not exist. Please create it manually in AWS Console.")
                return False
            elif error_code == '403':
                logger.warning(f"No permission to access bucket '{self.bucket_name}' metadata, but proceeding (bucket may still work for uploads)")
                return True  # Proceed anyway, bucket might exist but head_bucket permission is missing
            else:
                logger.error(f"Error checking bucket '{self.bucket_name}': {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error checking bucket: {str(e)}")
            return False

    async def _configure_bucket(self):
        """Configure bucket with CORS, lifecycle, and security policies"""
        try:
            # CORS Configuration
            cors_config = {
                'CORSRules': [
                    {
                        'AllowedHeaders': ['*'],
                        'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                        'AllowedOrigins': ['*'],
                        'ExposeHeaders': ['ETag'],
                        'MaxAgeSeconds': 3000
                    }
                ]
            }
            self.s3_client.put_bucket_cors(Bucket=self.bucket_name, CORSConfiguration=cors_config)
            
            # Lifecycle Configuration for cost optimization
            lifecycle_config = {
                'Rules': [
                    {
                        'ID': 'OptimizeStorage',
                        'Status': 'Enabled',
                        'Transitions': [
                            {
                                'Days': 30,
                                'StorageClass': 'STANDARD_IA'
                            },
                            {
                                'Days': 90,
                                'StorageClass': 'GLACIER'
                            }
                        ]
                    }
                ]
            }
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            
            # Versioning
            self.s3_client.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            logger.info("Bucket configuration completed")
        except ClientError as e:
            logger.error(f"Error configuring bucket: {e}")

    def _get_file_category(self, filename: str) -> str:
        """Determine file category based on extension"""
        ext = os.path.splitext(filename)[1].lower()
        for category, extensions in self.allowed_file_types.items():
            if ext in extensions:
                return category
        return 'other'

    def _generate_s3_key(self, file: UploadFile, metadata: Dict = None) -> str:
        """Generate optimized S3 key for file organization"""
        # Create hash of content for deduplication
        content_hash = hashlib.md5(file.filename.encode()).hexdigest()[:8]
        
        # Get file category
        category = self._get_file_category(file.filename)
        
        # Get metadata
        country = metadata.get('country', 'unknown') if metadata else 'unknown'
        policy_area = metadata.get('policy_area', 'general') if metadata else 'general'
        
        # Create organized path
        date_prefix = datetime.now().strftime('%Y/%m')
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in '._-')
        
        s3_key = f"policy-files/{category}/{country}/{policy_area}/{date_prefix}/{content_hash}_{safe_filename}"
        
        return s3_key

    async def upload_file(self, file: UploadFile, metadata: Dict = None) -> Dict[str, Any]:
        """Upload file to S3 with optimization and caching"""
        try:
            # Validate file
            await self._validate_file(file)
            
            # Generate S3 key
            s3_key = self._generate_s3_key(file, metadata)
            
            # Check cache first
            cache_key = f"file_upload:{hashlib.md5(s3_key.encode()).hexdigest()}"
            if self.cache_enabled and self.redis_client and self._test_redis_connection():
                try:
                    cached_result = self.redis_client.get(cache_key)
                    if cached_result:
                        logger.info(f"File found in cache: {s3_key}")
                        return json.loads(cached_result)
                except Exception as e:
                    logger.warning(f"Cache read failed: {e}")
                    # Continue without cache
            
            # Read file content
            file_content = await file.read()
            await file.seek(0)
            
            # Process file based on type
            processed_content, extra_metadata = await self._process_file(file, file_content)
            
            # Upload to S3
            upload_result = await self._upload_to_s3(
                s3_key, 
                processed_content, 
                file.content_type,
                metadata,
                extra_metadata
            )
            
            # Cache result
            if self.cache_enabled and self.redis_client and self._test_redis_connection():
                try:
                    self.redis_client.setex(cache_key, 3600, json.dumps(upload_result))
                except Exception as e:
                    logger.warning(f"Cache write failed: {e}")
                    # Continue without cache
            
            logger.info(f"File uploaded successfully: {s3_key}")
            return upload_result
            
        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    async def _validate_file(self, file: UploadFile):
        """Validate file size and type"""
        # Check file size
        file_content = await file.read()
        await file.seek(0)
        
        if len(file_content) > self.max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {self.max_file_size / 1024 / 1024}MB"
            )
        
        # Check file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        all_allowed = []
        for extensions in self.allowed_file_types.values():
            all_allowed.extend(extensions)
        
        if file_ext not in all_allowed:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(all_allowed)}"
            )

    async def _process_file(self, file: UploadFile, content: bytes) -> tuple:
        """Process file based on type (compression, optimization, etc.)"""
        extra_metadata = {}
        
        # Image optimization
        if file.content_type and file.content_type.startswith('image/'):
            try:
                processed_content, image_metadata = await self._optimize_image(content)
                extra_metadata.update(image_metadata)
                return processed_content, extra_metadata
            except Exception as e:
                logger.warning(f"Image optimization failed: {e}")
        
        return content, extra_metadata

    async def _optimize_image(self, content: bytes) -> tuple:
        """Optimize images for web delivery"""
        def optimize():
            try:
                # Open image
                image = Image.open(io.BytesIO(content))
                
                # Convert to RGB if necessary
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                # Resize if too large
                max_dimension = 2048
                if max(image.size) > max_dimension:
                    ratio = max_dimension / max(image.size)
                    new_size = tuple(int(dim * ratio) for dim in image.size)
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                
                # Optimize and save
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=85, optimize=True)
                optimized_content = output.getvalue()
                
                metadata = {
                    'original_size': len(content),
                    'optimized_size': len(optimized_content),
                    'compression_ratio': len(optimized_content) / len(content),
                    'dimensions': f"{image.size[0]}x{image.size[1]}"
                }
                
                return optimized_content, metadata
            except Exception as e:
                logger.error(f"Image optimization error: {e}")
                return content, {}
        
        # Run optimization in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, optimize)

    async def _upload_to_s3(self, s3_key: str, content: bytes, content_type: str, 
                           metadata: Dict = None, extra_metadata: Dict = None) -> Dict[str, Any]:
        """Upload file to S3 with proper metadata and caching headers"""
        
        # Prepare metadata
        s3_metadata = {
            'upload_date': datetime.utcnow().isoformat(),
            'file_size': str(len(content)),
            'content_type': content_type or 'application/octet-stream'
        }
        
        if metadata:
            s3_metadata.update({k: str(v) for k, v in metadata.items()})
        
        if extra_metadata:
            s3_metadata.update({k: str(v) for k, v in extra_metadata.items()})
        
        # Upload parameters
        upload_params = {
            'Bucket': self.bucket_name,
            'Key': s3_key,
            'Body': content,
            'ContentType': content_type or 'application/octet-stream',
            'Metadata': s3_metadata,
            'CacheControl': 'max-age=31536000',  # 1 year cache
            'ServerSideEncryption': 'AES256'
        }
        
        def upload():
            return self.s3_client.put_object(**upload_params)
        
        # Run upload in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(self.executor, upload)
        
        # Generate URLs
        file_url = self._generate_file_url(s3_key)
        cdn_url = self._generate_cdn_url(s3_key) if self.cloudfront_domain else file_url
        
        return {
            'file_id': s3_key,
            's3_key': s3_key,
            'file_url': file_url,
            'cdn_url': cdn_url,
            'bucket': self.bucket_name,
            'size': len(content),
            'content_type': content_type,
            'etag': response['ETag'].strip('"'),
            'metadata': s3_metadata,
            'upload_date': datetime.utcnow().isoformat()
        }

    def _generate_file_url(self, s3_key: str) -> str:
        """Generate direct S3 URL"""
        return f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"

    def _generate_cdn_url(self, s3_key: str) -> str:
        """Generate CloudFront CDN URL"""
        return f"https://{self.cloudfront_domain}/{s3_key}"

    async def get_file(self, s3_key: str) -> Dict[str, Any]:
        """Get file from S3 with caching"""
        try:
            # Note: We don't cache full file content, only fetch fresh from S3
            # Cache is only used for metadata optimization elsewhere
            
            def get_object():
                return self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            
            # Get object from S3
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(self.executor, get_object)
            
            result = {
                'content': response['Body'].read(),
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified', '').isoformat() if response.get('LastModified') else '',
                'metadata': response.get('Metadata', {}),
                'etag': response.get('ETag', '').strip('"')
            }
            
            return result
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(status_code=404, detail="File not found")
            raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

    async def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3 and cache"""
        try:
            def delete_object():
                return self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, delete_object)
            
            # Clear from cache
            if self.cache_enabled and self.redis_client:
                try:
                    cache_keys = [f"file_get:{s3_key}", f"file_upload:*{s3_key}*"]
                    for pattern in cache_keys:
                        keys = self.redis_client.keys(pattern)
                        if keys:
                            self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Cache clear failed: {e}")
                    # Continue without cache
            
            logger.info(f"File deleted: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file: {e}")
            return False

    async def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for secure file access"""
        try:
            def generate_url():
                return self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration
                )
            
            loop = asyncio.get_event_loop()
            url = await loop.run_in_executor(self.executor, generate_url)
            return url
            
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")

    async def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List files in S3 bucket with pagination"""
        try:
            def list_objects():
                return self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=limit
                )
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(self.executor, list_objects)
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"'),
                    'url': self._generate_file_url(obj['Key']),
                    'cdn_url': self._generate_cdn_url(obj['Key']) if self.cloudfront_domain else None
                })
            
            return files
            
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

    async def get_bucket_stats(self) -> Dict[str, Any]:
        """Get bucket statistics and usage information"""
        try:
            # Get bucket size and object count
            total_size = 0
            object_count = 0
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            def get_stats():
                nonlocal total_size, object_count
                for page in paginator.paginate(Bucket=self.bucket_name):
                    for obj in page.get('Contents', []):
                        total_size += obj['Size']
                        object_count += 1
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, get_stats)
            
            return {
                'bucket_name': self.bucket_name,
                'total_objects': object_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'total_size_gb': round(total_size / 1024 / 1024 / 1024, 2),
                'region': self.aws_region,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error getting bucket stats: {str(e)}")

    async def close(self):
        """Cleanup method for shutdown compatibility"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
            
            if self.redis_client:
                try:
                    self.redis_client.close()
                except:
                    pass
            
            logger.info("AWS service cleanup completed")
        except Exception as e:
            logger.error(f"AWS service cleanup error: {str(e)}")

# Create singleton instance
aws_service = AWSService()

# Initialize function
async def init_aws_service():
    """Initialize AWS service and ensure bucket exists"""
    await aws_service.ensure_bucket_exists()
    logger.info("AWS S3 service initialized successfully")
