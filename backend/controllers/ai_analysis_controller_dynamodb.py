"""
DynamoDB-based AI Analysis controller.
"""
import logging
from typing import Dict, Any, List
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from middleware.auth import get_current_user, get_admin_user
from services.ai_analysis_service_dynamodb import ai_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

class PolicyAnalysisRequest(BaseModel):
    policy_data: Dict[str, Any]

class CountryComparisonRequest(BaseModel):
    countries: List[str]

@router.post("/analyze-policy")
async def analyze_policy(
    request: PolicyAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Analyze a policy submission and provide AI insights"""
    try:
        logger.info(f"AI policy analysis request from user: {current_user['email']}")
        
        analysis_result = await ai_analysis_service.analyze_policy(request.policy_data)
        
        return {
            "success": True,
            "data": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze policy"
        )

@router.get("/country-analysis/{country}")
async def get_country_analysis(
    country: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get comprehensive analysis for a country's policies"""
    try:
        logger.info(f"Country analysis request for {country} from user: {current_user['email']}")
        
        if not country or len(country.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid country name required"
            )
        
        analysis = await ai_analysis_service.get_country_analysis(country.strip())
        
        return {
            "success": True,
            "data": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Country analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze country policies"
        )

@router.post("/analyze-uploaded-file")
async def analyze_uploaded_file(
    file_id: str = Form(...),
    # current_user: Dict[str, Any] = Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Analyze an already uploaded file by file_id using AI (DynamoDB version).
    """
    try:
        # Check if Groq API key is configured
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key or groq_api_key == "gsk_placeholder_key_replace_with_actual_key":
            raise HTTPException(
                status_code=503, 
                detail="AI analysis service is not configured. Please set GROQ_API_KEY in environment variables."
            )

        # Validate file_id format
        if not file_id or len(file_id.strip()) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file ID format. Please upload the file first."
            )

        # Get file metadata from DynamoDB
        from models.file_metadata_dynamodb import FileMetadata
        
        file_metadata = await FileMetadata.find_by_id(file_id)
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file content from S3
        file_content = None
        filename = file_metadata.filename or 'unknown'
        
        try:
            from services.aws_service import aws_service
            s3_result = await aws_service.get_file(file_metadata.s3_key)
            file_content = s3_result['content']
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve file from S3: {str(e)}")
        
        if not file_content:
            raise HTTPException(status_code=404, detail="File content could not be retrieved")

        logger.info(f"Processing uploaded file: {filename} (file_id: {file_id})")
        
        # Extract text from file
        try:
            text_content = ai_analysis_service.extract_text_from_file(file_content, filename)
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
        
        logger.info(f"Successfully analyzed uploaded file: {filename}")
        
        # Include TEA scores in the response if available
        tea_scores = extracted_data.get("tea_scores", {})
        tea_analysis = extracted_data.get("tea_analysis", {})
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "File analyzed successfully",
                "data": extracted_data,
                "tea_scores": tea_scores,
                "tea_analysis": tea_analysis,
                "metadata": {
                    "filename": filename,
                    "file_id": file_id,
                    "text_length": len(text_content),
                    "storage_type": "s3",
                    "includes_tea_scores": bool(tea_scores)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error analyzing uploaded file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
        
        if not groq_api_key or groq_api_key == "gsk_placeholder_key_replace_with_actual_key":
            logger.error(f"GROQ_API_KEY validation failed. Key exists: {groq_api_key is not None}")
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
        
        # Extract text from file - we need to import the service
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
        
        # Include TEA scores in the response if available
        tea_scores = extracted_data.get("tea_scores", {})
        tea_analysis = extracted_data.get("tea_analysis", {})
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Document analyzed successfully",
                "data": extracted_data,
                "tea_scores": tea_scores,
                "tea_analysis": tea_analysis,
                "metadata": {
                    "filename": file.filename,
                    "file_size": len(file_content),
                    "text_length": len(text_content),
                    "processed_by": "anonymous",
                    "includes_tea_scores": bool(tea_scores)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in document analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during document analysis")

@router.post("/calculate-tea-scores")
async def calculate_tea_scores(
    file: UploadFile = File(...)
    # current_user: Dict[str, Any] = Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Calculate Transparency, Explainability, and Accountability (TEA) scores from policy document using AWS Bedrock.
    Returns structured scores that can be used to auto-fill submission forms.
    """
    try:
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
        
        logger.info(f"Calculating TEA scores for document: {file.filename}")
        
        # Extract text from file
        try:
            text_content = ai_analysis_service.extract_text_from_file(file_content, file.filename)
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to extract text from document: {str(e)}")
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No readable text found in the document")
        
        # Calculate TEA scores using Bedrock
        try:
            tea_results = ai_analysis_service.calculate_tea_scores(text_content)
        except Exception as e:
            logger.error(f"TEA scores calculation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"TEA scores calculation failed: {str(e)}")
        
        # Extract scores for easy access
        scores = tea_results.get("scores", {
            "transparency_score": 0,
            "explainability_score": 0,
            "accountability_score": 0
        })
        
        logger.info(f"Successfully calculated TEA scores for {file.filename}: "
                   f"T={scores.get('transparency_score', 0)}, "
                   f"E={scores.get('explainability_score', 0)}, "
                   f"A={scores.get('accountability_score', 0)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "TEA scores calculated successfully",
                "scores": scores,
                "detailed_analysis": {
                    "transparency_analysis": tea_results.get("transparency_analysis", []),
                    "explainability_analysis": tea_results.get("explainability_analysis", []),
                    "accountability_analysis": tea_results.get("accountability_analysis", [])
                },
                "metadata": {
                    "filename": file.filename,
                    "file_size": len(file_content),
                    "text_length": len(text_content),
                    "analysis_method": "aws_bedrock_claude"
                },
                "form_data": {
                    "transparency_score": scores.get('transparency_score', 0),
                    "explainability_score": scores.get('explainability_score', 0),
                    "accountability_score": scores.get('accountability_score', 0)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in TEA scores calculation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during TEA scores calculation")

@router.post("/calculate-tea-scores-by-file-id")
async def calculate_tea_scores_by_file_id(
    file_id: str = Form(...)
    # current_user: Dict[str, Any] = Depends(get_current_user)  # Temporarily disabled for testing
):
    """
    Calculate TEA scores for an already uploaded file by file_id using AWS Bedrock.
    """
    try:
        # Validate file_id format
        if not file_id or len(file_id.strip()) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file ID format. Please upload the file first."
            )

        # Get file metadata from DynamoDB
        from models.file_metadata_dynamodb import FileMetadata
        
        file_metadata = await FileMetadata.find_by_id(file_id)
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file content from S3
        file_content = None
        filename = file_metadata.filename or 'unknown'
        
        try:
            from services.aws_service import aws_service
            s3_result = await aws_service.get_file(file_metadata.s3_key)
            file_content = s3_result['content']
            
            if not file_content:
                raise HTTPException(status_code=404, detail="File content is empty")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"S3 retrieval failed for file_id {file_id}, s3_key {file_metadata.s3_key}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve file from S3: {str(e)}")

        logger.info(f"Calculating TEA scores for uploaded file: {filename} (file_id: {file_id})")
        
        # Extract text from file
        try:
            text_content = ai_analysis_service.extract_text_from_file(file_content, filename)
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to extract text from document: {str(e)}")
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No readable text found in the document")
        
        # Calculate TEA scores using Bedrock
        try:
            tea_results = ai_analysis_service.calculate_tea_scores(text_content)
        except Exception as e:
            logger.error(f"TEA scores calculation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"TEA scores calculation failed: {str(e)}")
        
        # Extract scores for easy access
        scores = tea_results.get("scores", {
            "transparency_score": 0,
            "explainability_score": 0,
            "accountability_score": 0
        })
        
        logger.info(f"Successfully calculated TEA scores for {filename}: "
                   f"T={scores.get('transparency_score', 0)}, "
                   f"E={scores.get('explainability_score', 0)}, "
                   f"A={scores.get('accountability_score', 0)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "TEA scores calculated successfully",
                "scores": scores,
                "detailed_analysis": {
                    "transparency_analysis": tea_results.get("transparency_analysis", []),
                    "explainability_analysis": tea_results.get("explainability_analysis", []),
                    "accountability_analysis": tea_results.get("accountability_analysis", [])
                },
                "metadata": {
                    "filename": filename,
                    "file_id": file_id,
                    "text_length": len(text_content),
                    "storage_type": "s3",
                    "analysis_method": "aws_bedrock_claude"
                },
                "form_data": {
                    "transparency_score": scores.get('transparency_score', 0),
                    "explainability_score": scores.get('explainability_score', 0),
                    "accountability_score": scores.get('accountability_score', 0)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error calculating TEA scores for file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/status")
async def get_ai_analysis_status():
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

@router.post("/compare-countries")
async def compare_countries(
    request: CountryComparisonRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Compare policy performance across multiple countries"""
    try:
        logger.info(f"Country comparison request from user: {current_user['email']}")
        
        if not request.countries or len(request.countries) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 countries required for comparison"
            )
        
        if len(request.countries) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 countries allowed for comparison"
            )
        
        # Clean country names
        clean_countries = [country.strip() for country in request.countries if country.strip()]
        
        if len(clean_countries) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 valid countries required"
            )
        
        comparison = await ai_analysis_service.compare_countries(clean_countries)
        
        return {
            "success": True,
            "data": comparison
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Country comparison error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare countries"
        )

@router.get("/insights/top-performers")
async def get_top_performers(
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get top performing countries by policy score"""
    try:
        logger.info(f"Top performers request from user: {current_user['email']}")
        
        # This would require scanning all countries and calculating their scores
        # For now, return a simple response
        return {
            "success": True,
            "data": {
                "message": "Top performers analysis requires more comprehensive data",
                "recommendation": "Use country comparison with specific countries for detailed analysis"
            }
        }
        
    except Exception as e:
        logger.error(f"Top performers error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get top performers"
        )

@router.get("/insights/policy-trends")
async def get_policy_trends(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get policy trends and insights"""
    try:
        logger.info(f"Policy trends request from user: {current_user['email']}")
        
        # This would require time-series analysis of policies
        # For now, return a simple response
        return {
            "success": True,
            "data": {
                "message": "Policy trends analysis requires historical data",
                "recommendation": "Use country analysis for current policy status"
            }
        }
        
    except Exception as e:
        logger.error(f"Policy trends error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get policy trends"
        )

@router.get("/health")
async def ai_analysis_health():
    """Health check for AI analysis service"""
    return {
        "success": True,
        "service": "AI Analysis Service",
        "status": "healthy",
        "features": [
            "policy_analysis",
            "country_analysis", 
            "country_comparison",
            "scoring_algorithms"
        ]
    }

# Export router
ai_analysis_router = router
