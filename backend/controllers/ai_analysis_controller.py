"""
AI Analysis Controller for Policy Document Processing
Handles document upload and AI-powered information extraction.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)

from services.ai_analysis_service import ai_analysis_service
from middleware.auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai-analysis"])

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

@router.post("/analyze-policy-document")
async def analyze_policy_document(
    file: UploadFile = File(...)
    # current_user: Dict[str, Any] = Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Analyze uploaded policy document and extract structured information using AI.
    """
    try:
        # Check if Groq API key is configured
        groq_api_key = os.getenv('GROQ_API_KEY')
        logger.info(f"GROQ_API_KEY found: {groq_api_key is not None}")
        logger.info(f"GROQ_API_KEY value (first 10 chars): {groq_api_key[:10] if groq_api_key else 'None'}")
        
        if not groq_api_key or groq_api_key == "gsk_placeholder_key_replace_with_actual_key":
            logger.error(f"GROQ_API_KEY validation failed. Key exists: {groq_api_key is not None}, Key value: {groq_api_key}")
            raise HTTPException(
                status_code=503, 
                detail="AI analysis service is not configured. Please set GROQ_API_KEY in environment variables."
            )
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Check file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
        file_extension = '.' + file.filename.lower().split('.')[-1]
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        logger.info(f"Processing document: {file.filename}")
        
        # Extract text from file
        try:
            text_content = ai_analysis_service.extract_text_from_file(file_content, file.filename)
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to extract text from document: {str(e)}")
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No readable text found in the document")
        
        # Analyze with AI
        try:
            extracted_data = ai_analysis_service.analyze_policy_document(text_content)
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
        
        logger.info(f"Successfully analyzed document: {file.filename}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Document analyzed successfully",
                "data": extracted_data,
                "metadata": {
                    "filename": file.filename,
                    "file_size": len(file_content),
                    "text_length": len(text_content),
                    "processed_by": "anonymous"
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in document analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during document analysis")

@router.get("/status")
async def get_ai_analysis_status():
    # current_user: Dict[str, Any] = Depends(get_current_user)  # Temporarily disabled
    """
    Get the status of AI analysis service.
    """
    try:
        # Check if Groq API key is configured
        groq_api_key = os.getenv('GROQ_API_KEY')
        is_configured = bool(groq_api_key and groq_api_key != "gsk_placeholder_key_replace_with_actual_key")
        
        return JSONResponse(
            status_code=200,
            content={
                "service_available": is_configured,
                "api_key_configured": is_configured,
                "supported_formats": [".pdf", ".doc", ".docx", ".txt"],
                "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
                "ai_model": "llama3-70b-8192",
                "message": "AI analysis service is ready" if is_configured else "Please configure GROQ_API_KEY to enable AI analysis"
            }
        )
        
    except Exception as e:
        logger.error(f"Error checking AI analysis status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error checking service status")
