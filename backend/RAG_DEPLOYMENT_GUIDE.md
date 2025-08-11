# RAG Chatbot Deployment Guide

## Overview
This guide covers deploying the enhanced PolicyTracker with RAG (Retrieval-Augmented Generation) capabilities to Render.

## Prerequisites
- Render account
- AWS account with DynamoDB access
- OpenAI API key (for embeddings and chat)
- GROQ API key (backup)

## Environment Variables Required

Add these to your Render environment variables:

```
# Existing PolicyTracker variables
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=PolicyTracker
CONVERSATIONS_TABLE_NAME=Conversations

# RAG-specific tables
CONVERSATION_EMBEDDINGS_TABLE_NAME=ConversationEmbeddings
KEYWORD_INDEX_TABLE_NAME=KeywordIndex

# AI Service APIs
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key

# Application settings
ENVIRONMENT=production
DEBUG=false
```

## Deployment Steps

### 1. Database Migration
Run the migration script to set up RAG tables:

```bash
cd backend
python migrate_to_rag.py
```

### 2. Render Configuration
Update your `render.yaml`:

```yaml
services:
  - type: web
    name: policy-tracker-rag
    env: python
    plan: starter
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: AWS_ACCESS_KEY_ID
        fromDatabase:
          name: policy-tracker-db
          property: connectionString
      # Add all other environment variables
```

### 3. Test RAG Endpoints

After deployment, test the new RAG functionality:

```bash
# Test RAG chat
curl -X POST https://your-app.onrender.com/api/v1/rag/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the education policies in Bangladesh?", "user_id": "test_user"}'

# Search conversation history
curl -X GET "https://your-app.onrender.com/api/v1/rag/search?query=education&user_id=test_user"

# Get conversation context
curl -X GET "https://your-app.onrender.com/api/v1/rag/context/test_user"
```

## RAG Features

### 1. Semantic Search
- Uses OpenAI embeddings (text-embedding-ada-002)
- FAISS vector similarity search
- Finds relevant conversations based on meaning, not just keywords

### 2. Hybrid Retrieval
- Combines semantic search with keyword matching
- Fallback mechanisms for better coverage
- Context-aware response generation

### 3. Conversation Storage
- All conversations stored with embeddings
- Keyword indexing for fast retrieval
- User-specific conversation history

### 4. Enhanced Responses
- Context from previous conversations
- More relevant and personalized answers
- Maintains conversation flow

## API Endpoints

### RAG Chat
```
POST /api/v1/rag/chat
{
  "message": "Your question about policies",
  "user_id": "unique_user_identifier",
  "include_context": true
}
```

### Search Conversations
```
GET /api/v1/rag/search?query=search_term&user_id=user_id&limit=10
```

### Get Context
```
GET /api/v1/rag/context/{user_id}?limit=5
```

### Vector Statistics
```
GET /api/v1/rag/stats
```

## Performance Considerations

### 1. Vector Index Management
- FAISS index rebuilt periodically
- Consider persistent storage for large deployments
- Monitor memory usage

### 2. Embedding Generation
- OpenAI API rate limits
- Batch processing for efficiency
- Caching strategies

### 3. Database Optimization
- DynamoDB read/write capacity
- Query patterns and indexing
- Cost monitoring

## Monitoring and Maintenance

### 1. Health Checks
Monitor these endpoints:
- `/health` - Basic health check
- `/api/v1/rag/stats` - RAG system statistics

### 2. Logs to Monitor
- Embedding generation errors
- Vector search performance
- API response times
- Database connection issues

### 3. Regular Maintenance
- Clean up old conversations
- Rebuild vector indexes
- Update embeddings for new content

## Troubleshooting

### Common Issues

1. **Embedding Generation Fails**
   - Check OpenAI API key
   - Verify rate limits
   - Monitor API usage

2. **Vector Search Slow**
   - Check FAISS index size
   - Consider index optimization
   - Monitor memory usage

3. **Database Errors**
   - Verify AWS credentials
   - Check DynamoDB table creation
   - Monitor read/write capacity

### Debug Mode

Set `DEBUG=true` for detailed logging:
```
DEBUG=true
LOG_LEVEL=DEBUG
```

## Migration from Legacy System

The migration script (`migrate_to_rag.py`) handles:
- Creating new DynamoDB tables
- Migrating existing conversations
- Generating embeddings for historical data
- Verifying data integrity

Run with verification:
```bash
python migrate_to_rag.py --verify
```

## Cost Considerations

### OpenAI API Costs
- Embeddings: ~$0.0001 per 1K tokens
- Chat completions: varies by model
- Monitor usage in OpenAI dashboard

### AWS DynamoDB
- Storage costs for embeddings
- Read/write capacity units
- Consider on-demand vs provisioned

### Render Hosting
- Starter plan sufficient for testing
- Scale up based on usage
- Monitor resource utilization

## Security Notes

- Store API keys as environment variables
- Use HTTPS for all endpoints
- Implement rate limiting
- Monitor for abuse patterns
- Regular security updates

## Next Steps

1. Deploy to Render
2. Run migration script
3. Test RAG functionality
4. Monitor performance
5. Scale as needed

For support, check the logs and monitor the health endpoints. The RAG system enhances the existing PolicyTracker with intelligent conversation capabilities while maintaining all existing functionality.
