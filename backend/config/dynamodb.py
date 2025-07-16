"""
DynamoDB Database Configuration
Replaces MongoDB with AWS DynamoDB for better AWS integration
"""
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from config.settings import settings
import logging
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DynamoDBClient:
    """DynamoDB client for managing database operations"""
    
    def __init__(self):
        """Initialize DynamoDB client and resources"""
        try:
            # Create DynamoDB resource
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=settings.AWS_DYNAMODB_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            # Create DynamoDB client for table operations
            self.client = boto3.client(
                'dynamodb',
                region_name=settings.AWS_DYNAMODB_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            # Table references
            self.tables = {
                'users': None,
                'policies': None,
                'chat_messages': None,
                'chat_sessions': None,
                'admin_data': None,
                'file_metadata': None,
                'map_policies': None
            }
            
            # Table name mapping - using ai_policy_database as base name
            self.table_names = {
                'users': 'ai_policy_database_users',
                'policies': 'ai_policy_database_policies', 
                'chat_messages': 'ai_policy_database_chat_messages',
                'chat_sessions': 'ai_policy_database_chat_sessions',
                'admin_data': 'ai_policy_database_admin_data',
                'file_metadata': 'ai_policy_database_file_metadata',
                'map_policies': 'ai_policy_database_map_policies'
            }
            
            logger.info("DynamoDB client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB client: {str(e)}")
            raise
    
    async def connect(self):
        """Connect to DynamoDB and create tables if they don't exist"""
        try:
            # Create tables
            await self._create_tables()
            
            # Initialize table references
            for table_key in self.tables.keys():
                table_name = self.table_names[table_key]
                self.tables[table_key] = self.dynamodb.Table(table_name)
            
            logger.info("DynamoDB connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB: {str(e)}")
            # For development, continue without DynamoDB if permissions are missing
            if "AccessDeniedException" in str(e) or "DynamoDB" in str(e):
                logger.warning("DynamoDB access denied - continuing with limited functionality")
                return False
            return False
    
    async def _create_tables(self):
        """Create DynamoDB tables if they don't exist"""
        tables_to_create = [
            {
                'name': 'users',
                'key_schema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                ],
                'attribute_definitions': [
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'email', 'AttributeType': 'S'},
                ],
                'global_secondary_indexes': [
                    {
                        'IndexName': 'email-index',
                        'KeySchema': [
                            {'AttributeName': 'email', 'KeyType': 'HASH'},
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            {
                'name': 'policies',
                'key_schema': [
                    {'AttributeName': 'policy_id', 'KeyType': 'HASH'},
                ],
                'attribute_definitions': [
                    {'AttributeName': 'policy_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'},
                ],
                'global_secondary_indexes': [
                    {
                        'IndexName': 'user-created-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'},
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            {
                'name': 'chat_messages',
                'key_schema': [
                    {'AttributeName': 'message_id', 'KeyType': 'HASH'},
                ],
                'attribute_definitions': [
                    {'AttributeName': 'message_id', 'AttributeType': 'S'},
                    {'AttributeName': 'session_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'},
                ],
                'global_secondary_indexes': [
                    {
                        'IndexName': 'session-created-index',
                        'KeySchema': [
                            {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'},
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    },
                    {
                        'IndexName': 'user-created-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'},
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            {
                'name': 'chat_sessions',
                'key_schema': [
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                ],
                'attribute_definitions': [
                    {'AttributeName': 'session_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'updated_at', 'AttributeType': 'S'},
                ],
                'global_secondary_indexes': [
                    {
                        'IndexName': 'user-updated-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'updated_at', 'KeyType': 'RANGE'},
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            {
                'name': 'admin_data',
                'key_schema': [
                    {'AttributeName': 'admin_id', 'KeyType': 'HASH'},
                ],
                'attribute_definitions': [
                    {'AttributeName': 'admin_id', 'AttributeType': 'S'},
                ],
            },
            {
                'name': 'file_metadata',
                'key_schema': [
                    {'AttributeName': 'file_id', 'KeyType': 'HASH'},
                ],
                'attribute_definitions': [
                    {'AttributeName': 'file_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'},
                ],
                'global_secondary_indexes': [
                    {
                        'IndexName': 'user-created-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'created_at', 'KeyType': 'RANGE'},
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            },
            {
                'name': 'map_policies',
                'key_schema': [
                    {'AttributeName': 'map_policy_id', 'KeyType': 'HASH'},
                ],
                'attribute_definitions': [
                    {'AttributeName': 'map_policy_id', 'AttributeType': 'S'},
                    {'AttributeName': 'country', 'AttributeType': 'S'},
                    {'AttributeName': 'approved_at', 'AttributeType': 'S'},
                    {'AttributeName': 'policy_area', 'AttributeType': 'S'},
                ],
                'global_secondary_indexes': [
                    {
                        'IndexName': 'country-approved-index',
                        'KeySchema': [
                            {'AttributeName': 'country', 'KeyType': 'HASH'},
                            {'AttributeName': 'approved_at', 'KeyType': 'RANGE'},
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    },
                    {
                        'IndexName': 'policy-area-approved-index',
                        'KeySchema': [
                            {'AttributeName': 'policy_area', 'KeyType': 'HASH'},
                            {'AttributeName': 'approved_at', 'KeyType': 'RANGE'},
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ]
            }
        ]
        
        for table_config in tables_to_create:
            await self._create_table(table_config)
    
    async def _create_table(self, table_config: Dict):
        """Create a single DynamoDB table"""
        table_key = table_config['name']
        table_name = self.table_names[table_key]
        
        try:
            # Check if table exists
            try:
                existing_tables = self.client.list_tables()['TableNames']
                if table_name in existing_tables:
                    logger.info(f"Table {table_name} already exists")
                    return
            except ClientError as e:
                if "AccessDeniedException" in str(e):
                    logger.warning(f"Cannot list tables due to permissions - skipping {table_name}")
                    return
                raise
            
            # Prepare table creation parameters
            create_params = {
                'TableName': table_name,
                'KeySchema': table_config['key_schema'],
                'AttributeDefinitions': table_config['attribute_definitions'],
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
            
            # Add Global Secondary Indexes if specified
            if 'global_secondary_indexes' in table_config:
                create_params['GlobalSecondaryIndexes'] = table_config['global_secondary_indexes']
            
            # Create table
            response = self.client.create_table(**create_params)
            
            # Wait for table to be created
            waiter = self.client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            logger.info(f"Table {table_name} created successfully")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceInUseException':
                logger.info(f"Table {table_name} already exists")
            elif error_code == 'AccessDeniedException':
                logger.warning(f"Access denied for DynamoDB table {table_name} - skipping creation")
            else:
                logger.error(f"Error creating table {table_name}: {str(e)}")
        except Exception as e:
            if "AccessDeniedException" in str(e):
                logger.warning(f"Access denied for DynamoDB table {table_name} - skipping creation")
            else:
                logger.error(f"Error creating table {table_name}: {str(e)}")
    
    # CRUD Operations
    async def insert_item(self, table_name: str, item: Dict) -> bool:
        """Insert an item into DynamoDB table"""
        try:
            table = self.tables[table_name]
            
            # Add timestamp fields
            item['created_at'] = datetime.utcnow().isoformat()
            item['updated_at'] = datetime.utcnow().isoformat()
            
            table.put_item(Item=item)
            logger.info(f"Item inserted into {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting item into {table_name}: {str(e)}")
            return False
    
    async def get_item(self, table_name: str, key: Dict) -> Optional[Dict]:
        """Get an item from DynamoDB table"""
        try:
            table = self.tables[table_name]
            response = table.get_item(Key=key)
            return response.get('Item')
            
        except Exception as e:
            logger.error(f"Error getting item from {table_name}: {str(e)}")
            return None
    
    async def update_item(self, table_name: str, key: Dict, update_data: Dict) -> bool:
        """Update an item in DynamoDB table"""
        try:
            table = self.tables[table_name]
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Build update expression
            update_expression = "SET "
            expression_attribute_values = {}
            
            for field, value in update_data.items():
                update_expression += f"{field} = :{field}, "
                expression_attribute_values[f":{field}"] = value
            
            update_expression = update_expression.rstrip(", ")
            
            table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            logger.info(f"Item updated in {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating item in {table_name}: {str(e)}")
            return False
    
    async def delete_item(self, table_name: str, key: Dict) -> bool:
        """Delete an item from DynamoDB table"""
        try:
            table = self.tables[table_name]
            table.delete_item(Key=key)
            logger.info(f"Item deleted from {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting item from {table_name}: {str(e)}")
            return False
    
    async def query_items(self, table_name: str, key_condition: Any, 
                         index_name: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Query items from DynamoDB table"""
        try:
            table = self.tables[table_name]
            
            query_params = {
                'KeyConditionExpression': key_condition
            }
            
            if index_name:
                query_params['IndexName'] = index_name
            
            if limit:
                query_params['Limit'] = limit
            
            response = table.query(**query_params)
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error querying items from {table_name}: {str(e)}")
            return []
    
    async def scan_items(self, table_name: str, filter_expression: Optional[Any] = None,
                        limit: Optional[int] = None) -> List[Dict]:
        """Scan items from DynamoDB table"""
        try:
            table = self.tables[table_name]
            
            scan_params = {}
            
            if filter_expression:
                scan_params['FilterExpression'] = filter_expression
            
            if limit:
                scan_params['Limit'] = limit
            
            response = table.scan(**scan_params)
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error scanning items from {table_name}: {str(e)}")
            return []

    async def scan_table(self, table_name: str) -> List[Dict]:
        """Scan all items from a table"""
        try:
            table = self.tables[table_name]
            if not table:
                logger.error(f"Table {table_name} not initialized")
                return []
            
            response = table.scan()
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error scanning table {table_name}: {str(e)}")
            return []

# Global DynamoDB client instance
dynamodb_client = DynamoDBClient()

async def get_dynamodb():
    """Get DynamoDB client instance"""
    try:
        if not dynamodb_client.tables['users']:
            await dynamodb_client.connect()
        return dynamodb_client
    except Exception as e:
        logger.error(f"Error getting DynamoDB client: {e}")
        # Force reconnection
        await dynamodb_client.connect()
        return dynamodb_client

# Helper functions for backward compatibility
async def init_dynamodb():
    """Initialize DynamoDB connection"""
    return await dynamodb_client.connect()
