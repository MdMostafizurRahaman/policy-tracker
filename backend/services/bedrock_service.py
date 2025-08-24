"""
AWS Bedrock Service for AI-powered document analysis and scoring
Calculates Transparency, Explainability, and Accountability scores
"""
import boto3
import json
import logging
from typing import Dict, Any, Optional
import os
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BedrockService:
    def __init__(self):
        """Initialize Bedrock client"""
        try:
            # Initialize Bedrock client
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            logger.info("Bedrock service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock service: {str(e)}")
            self.bedrock_client = None

    def calculate_transparency_explainability_accountability_scores(self, document_text: str) -> Dict[str, Any]:
        """
        Calculate Transparency, Explainability, and Accountability scores based on document analysis
        
        Args:
            document_text: The extracted text from the policy document
            
        Returns:
            Dictionary containing the three scores and detailed analysis
        """
        if not self.bedrock_client:
            logger.error("Bedrock client not initialized")
            return {
                "transparency_score": 0,
                "explainability_score": 0,
                "accountability_score": 0,
                "error": "Bedrock service not available"
            }
        
        try:
            # Create comprehensive prompt for scoring
            prompt = self._create_scoring_prompt(document_text)
            
            # Call Bedrock with Claude model
            response = self._call_bedrock_claude(prompt)
            
            if response and 'scores' in response:
                return response
            else:
                logger.error("Invalid response from Bedrock")
                return self._get_default_scores("Invalid response from AI model")
                
        except Exception as e:
            logger.error(f"Error calculating scores: {str(e)}")
            return self._get_default_scores(f"Analysis failed: {str(e)}")

    def _create_scoring_prompt(self, document_text: str) -> str:
        """Create detailed prompt for scoring the document"""
        # Truncate document if too long for better analysis
        max_length = 8000
        if len(document_text) > max_length:
            document_text = document_text[:max_length] + "... [Document truncated for analysis]"
        
        prompt = f"""
You are an expert policy analyst specializing in AI governance and transparency. Analyze the following policy document and answer specific evaluation questions to calculate three key scores.

DOCUMENT TEXT:
{document_text}

Please carefully read the document and answer the following 15 questions. For each question, provide:
1. Your answer (Yes/Partial/No or Fully/Partial/No or Yes/Limited/No as specified)
2. A brief justification (1-2 sentences)
3. The score based on the scoring guide

TRANSPARENCY SCORE EVALUATION (Total: 0-10):

1. Is the full policy document publicly accessible?
   Scoring: Yes = 2, Partial = 1, No = 0

2. Does the policy clearly list the stakeholders involved in its creation?
   Scoring: Yes = 2, Partial = 1, No = 0

3. Was there public consultation or feedback collected?
   Scoring: Yes = 2, Limited = 1, No = 0

4. Does the policy provide open data or reporting on implementation?
   Scoring: Yes = 2, Partial = 1, No = 0

5. Are decision-making criteria or algorithms disclosed?
   Scoring: Fully = 2, Partial = 1, No = 0

EXPLAINABILITY SCORE EVALUATION (Total: 0-10):

6. Does the policy require systems to provide human-interpretable outputs?
   Scoring: Yes = 2, Partial = 1, No = 0

7. Are explanations tailored to the audience (technical/non-technical)?
   Scoring: Yes = 2, Partial = 1, No = 0

8. Are the decision-making processes (e.g., risk assessments) documented?
   Scoring: Yes = 2, Partial = 1, No = 0

9. Are users informed about how AI decisions are made?
   Scoring: Yes = 2, Partial = 1, No = 0

10. Does the policy include guidance for explainability in deployment?
    Scoring: Yes = 2, Partial = 1, No = 0

ACCOUNTABILITY SCORE EVALUATION (Total: 0-10):

11. Does the policy assign responsibility for AI decisions or harm?
    Scoring: Yes = 2, Partial = 1, No = 0

12. Are there auditing or oversight mechanisms in place?
    Scoring: Yes = 2, Partial = 1, No = 0

13. Can individuals seek redress or appeal AI decisions?
    Scoring: Yes = 2, Partial = 1, No = 0

14. Is liability for misuse or errors clearly outlined?
    Scoring: Yes = 2, Partial = 1, No = 0

15. Is there a governing/regulatory body identified?
    Scoring: Yes = 2, Partial = 1, No = 0

IMPORTANT: Return your analysis in the following JSON format ONLY:

{{
    "transparency_analysis": [
        {{"question": "Is the full policy document publicly accessible?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Does the policy clearly list the stakeholders involved in its creation?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Was there public consultation or feedback collected?", "answer": "Yes/Limited/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Does the policy provide open data or reporting on implementation?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Are decision-making criteria or algorithms disclosed?", "answer": "Fully/Partial/No", "justification": "Brief explanation", "score": 0-2}}
    ],
    "explainability_analysis": [
        {{"question": "Does the policy require systems to provide human-interpretable outputs?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Are explanations tailored to the audience (technical/non-technical)?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Are the decision-making processes (e.g., risk assessments) documented?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Are users informed about how AI decisions are made?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Does the policy include guidance for explainability in deployment?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}}
    ],
    "accountability_analysis": [
        {{"question": "Does the policy assign responsibility for AI decisions or harm?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Are there auditing or oversight mechanisms in place?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Can individuals seek redress or appeal AI decisions?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Is liability for misuse or errors clearly outlined?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}},
        {{"question": "Is there a governing/regulatory body identified?", "answer": "Yes/Partial/No", "justification": "Brief explanation", "score": 0-2}}
    ],
    "scores": {{
        "transparency_score": 0-10,
        "explainability_score": 0-10,
        "accountability_score": 0-10
    }}
}}

Analyze the document carefully and provide accurate, evidence-based answers. If information is not clearly present in the document, answer "No" and explain why.
"""
        return prompt

    def _call_bedrock_claude(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Bedrock with Claude model"""
        try:
            # Try multiple models in order of preference (updated for current AWS Bedrock)
            models = [
                "us.anthropic.claude-3-5-haiku-20241022-v1:0",   # Claude 3.5 Haiku inference profile - WORKING!
                "us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # Claude 3.5 Sonnet inference profile
                "anthropic.claude-3-sonnet-20240229-v1:0",       # Claude 3 Sonnet (if you have access)
                "anthropic.claude-3-haiku-20240307-v1:0",        # Claude 3 Haiku (if you have access)
            ]
            
            for model_id in models:
                try:
                    logger.info(f"Trying model: {model_id}")
                    
                    # Prepare the request body based on model type
                    if "claude-3" in model_id:
                        # Claude 3 format
                        body = {
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 4000,
                            "temperature": 0.1,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        }
                    else:
                        # Claude 2 format
                        body = {
                            "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                            "max_tokens_to_sample": 4000,
                            "temperature": 0.1,
                            "stop_sequences": ["\n\nHuman:"]
                        }
                    
                    # Make the request
                    response = self.bedrock_client.invoke_model(
                        modelId=model_id,
                        body=json.dumps(body),
                        contentType="application/json",
                        accept="application/json"
                    )
                    
                    # Parse the response
                    response_body = json.loads(response['body'].read())
                    
                    if "claude-3" in model_id:
                        ai_response = response_body.get('content', [{}])[0].get('text', '')
                    else:
                        ai_response = response_body.get('completion', '')
                    
                    logger.info(f"Received response from {model_id}: {ai_response[:200]}...")
                    
                    # Parse JSON from response
                    try:
                        # Extract JSON from the response
                        import re
                        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                        if json_match:
                            json_str = json_match.group()
                            result = json.loads(json_str)
                            
                            # Validate and calculate final scores
                            scores = self._calculate_final_scores(result)
                            result['scores'] = scores
                            
                            logger.info(f"Successfully used model: {model_id}")
                            return result
                        else:
                            logger.warning(f"No JSON found in response from {model_id}")
                            continue
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON from {model_id}: {e}")
                        continue
                        
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'AccessDeniedException':
                        logger.warning(f"No access to model {model_id}, trying next model")
                        continue
                    elif error_code == 'ValidationException':
                        logger.warning(f"Model {model_id} not available in region, trying next model")
                        continue
                    else:
                        logger.error(f"Bedrock API error with {model_id}: {e}")
                        continue
                except Exception as e:
                    logger.warning(f"Error with {model_id}: {e}, trying next model")
                    continue
            
            # If all models fail, try fallback analysis
            logger.error("All Bedrock models failed, attempting fallback analysis")
            return self._fallback_analysis(prompt)
                
        except Exception as e:
            logger.error(f"Unexpected error in Bedrock call: {e}")
            return self._fallback_analysis(prompt)

    def _calculate_final_scores(self, analysis_result: Dict[str, Any]) -> Dict[str, int]:
        """Calculate final scores from analysis results"""
        try:
            transparency_score = sum(item.get('score', 0) for item in analysis_result.get('transparency_analysis', []))
            explainability_score = sum(item.get('score', 0) for item in analysis_result.get('explainability_analysis', []))
            accountability_score = sum(item.get('score', 0) for item in analysis_result.get('accountability_analysis', []))
            
            return {
                "transparency_score": min(transparency_score, 10),  # Cap at 10
                "explainability_score": min(explainability_score, 10),
                "accountability_score": min(accountability_score, 10)
            }
        except Exception as e:
            logger.error(f"Error calculating final scores: {e}")
            return {
                "transparency_score": 0,
                "explainability_score": 0,
                "accountability_score": 0
            }

    def _fallback_analysis(self, prompt: str) -> Dict[str, Any]:
        """Fallback analysis using keyword matching when Bedrock is not available"""
        try:
            logger.info("Using fallback keyword-based analysis")
            
            # Extract document text from prompt
            import re
            doc_match = re.search(r'DOCUMENT TEXT:\s*(.*?)\s*Please carefully read', prompt, re.DOTALL)
            if not doc_match:
                return self._get_default_scores("Could not extract document text for fallback analysis")
            
            document_text = doc_match.group(1).lower()
            
            # Keyword-based scoring
            transparency_score = self._analyze_transparency_keywords(document_text)
            explainability_score = self._analyze_explainability_keywords(document_text)
            accountability_score = self._analyze_accountability_keywords(document_text)
            
            # Create structured response
            result = {
                "transparency_analysis": [
                    {"question": "Is the full policy document publicly accessible?", "answer": "Partial", "justification": "Based on keyword analysis", "score": transparency_score // 5},
                    {"question": "Does the policy clearly list the stakeholders involved in its creation?", "answer": "Partial", "justification": "Based on keyword analysis", "score": transparency_score // 5},
                    {"question": "Was there public consultation or feedback collected?", "answer": "Partial", "justification": "Based on keyword analysis", "score": transparency_score // 5},
                    {"question": "Does the policy provide open data or reporting on implementation?", "answer": "Partial", "justification": "Based on keyword analysis", "score": transparency_score // 5},
                    {"question": "Are decision-making criteria or algorithms disclosed?", "answer": "Partial", "justification": "Based on keyword analysis", "score": transparency_score // 5}
                ],
                "explainability_analysis": [
                    {"question": "Does the policy require systems to provide human-interpretable outputs?", "answer": "Partial", "justification": "Based on keyword analysis", "score": explainability_score // 5},
                    {"question": "Are explanations tailored to the audience (technical/non-technical)?", "answer": "Partial", "justification": "Based on keyword analysis", "score": explainability_score // 5},
                    {"question": "Are the decision-making processes (e.g., risk assessments) documented?", "answer": "Partial", "justification": "Based on keyword analysis", "score": explainability_score // 5},
                    {"question": "Are users informed about how AI decisions are made?", "answer": "Partial", "justification": "Based on keyword analysis", "score": explainability_score // 5},
                    {"question": "Does the policy include guidance for explainability in deployment?", "answer": "Partial", "justification": "Based on keyword analysis", "score": explainability_score // 5}
                ],
                "accountability_analysis": [
                    {"question": "Does the policy assign responsibility for AI decisions or harm?", "answer": "Partial", "justification": "Based on keyword analysis", "score": accountability_score // 5},
                    {"question": "Are there auditing or oversight mechanisms in place?", "answer": "Partial", "justification": "Based on keyword analysis", "score": accountability_score // 5},
                    {"question": "Can individuals seek redress or appeal AI decisions?", "answer": "Partial", "justification": "Based on keyword analysis", "score": accountability_score // 5},
                    {"question": "Is liability for misuse or errors clearly outlined?", "answer": "Partial", "justification": "Based on keyword analysis", "score": accountability_score // 5},
                    {"question": "Is there a governing/regulatory body identified?", "answer": "Partial", "justification": "Based on keyword analysis", "score": accountability_score // 5}
                ],
                "scores": {
                    "transparency_score": transparency_score,
                    "explainability_score": explainability_score,
                    "accountability_score": accountability_score
                },
                "fallback_used": True
            }
            
            logger.info(f"Fallback analysis completed. Scores: T={transparency_score}, E={explainability_score}, A={accountability_score}")
            return result
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return self._get_default_scores("Fallback analysis failed")

    def _analyze_transparency_keywords(self, text: str) -> int:
        """Analyze transparency using keyword matching"""
        transparency_keywords = [
            # Public access keywords
            'public', 'publicly', 'accessible', 'available', 'open', 'transparent',
            # Stakeholder keywords  
            'stakeholder', 'consultation', 'feedback', 'input', 'participation',
            # Data/reporting keywords
            'data', 'report', 'reporting', 'publish', 'disclosure', 'disclose',
            # Process keywords
            'process', 'procedure', 'method', 'criteria', 'algorithm'
        ]
        
        score = 0
        for keyword in transparency_keywords:
            if keyword in text:
                score += 1
        
        # Normalize to 0-10 scale
        return min(10, max(0, score // 2))

    def _analyze_explainability_keywords(self, text: str) -> int:
        """Analyze explainability using keyword matching"""
        explainability_keywords = [
            # Human interpretability
            'interpretable', 'understandable', 'explainable', 'clear', 'readable',
            # Explanations
            'explain', 'explanation', 'clarify', 'description', 'rationale',
            # Documentation
            'document', 'documentation', 'record', 'log', 'trace',
            # User information
            'inform', 'information', 'notify', 'communicate', 'guidance'
        ]
        
        score = 0
        for keyword in explainability_keywords:
            if keyword in text:
                score += 1
        
        # Normalize to 0-10 scale
        return min(10, max(0, score // 2))

    def _analyze_accountability_keywords(self, text: str) -> int:
        """Analyze accountability using keyword matching"""
        accountability_keywords = [
            # Responsibility
            'responsible', 'responsibility', 'liable', 'liability', 'accountable',
            # Oversight
            'audit', 'auditing', 'oversight', 'supervision', 'monitoring',
            # Redress
            'appeal', 'redress', 'complaint', 'grievance', 'remedy',
            # Governance
            'govern', 'governance', 'regulatory', 'authority', 'body', 'committee'
        ]
        
        score = 0
        for keyword in accountability_keywords:
            if keyword in text:
                score += 1
        
        # Normalize to 0-10 scale
        return min(10, max(0, score // 2))

    def _get_default_scores(self, error_message: str) -> Dict[str, Any]:
        """Return default scores when analysis fails"""
        return {
            "transparency_score": 0,
            "explainability_score": 0,
            "accountability_score": 0,
            "transparency_analysis": [],
            "explainability_analysis": [],
            "accountability_analysis": [],
            "error": error_message,
            "scores": {
                "transparency_score": 0,
                "explainability_score": 0,
                "accountability_score": 0
            }
        }

# Create singleton instance
bedrock_service = BedrockService()
