"""
AI Analysis Service for Policy Document Extraction
This service uses AI to extract structured information from policy documents.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import PyPDF2
import docx
from io import BytesIO
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the backend directory
backend_dir = Path(__file__).parent.parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIAnalysisService:
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        
    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """Extract text content from uploaded file based on file type."""
        try:
            file_extension = filename.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                return self._extract_from_pdf(file_content)
            elif file_extension in ['docx']:
                return self._extract_from_docx(file_content)
            elif file_extension in ['txt']:
                return file_content.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            raise
    
    def _extract_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
                
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def _extract_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            doc_file = BytesIO(file_content)
            doc = docx.Document(doc_file)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
                
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise
    
    def analyze_policy_document(self, text_content: str) -> Dict[str, Any]:
        """Analyze policy document text using AI and extract structured information."""
        try:
            # Prepare the AI analysis prompt
            analysis_prompt = self._create_analysis_prompt(text_content)
            
            # Call Groq API
            response = self._call_groq_api(analysis_prompt)
            
            # Parse and validate the response
            extracted_data = self._parse_ai_response(response)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error analyzing policy document: {str(e)}")
            raise
    
    def _create_analysis_prompt(self, text_content: str) -> str:
        """Create the analysis prompt for AI."""
        prompt = f"""
You are an expert policy analyst AI. Analyze the uploaded policy document carefully and extract the following information to populate a structured digital policy form. Provide the output in VALID JSON format based on the structure below.

CRITICAL JSON FORMATTING RULES:
1. Use ONLY valid JSON syntax
2. All string values must be in double quotes, including "N/A" for missing values
3. Use null (not "null") for truly empty values
4. Use true/false (lowercase) for boolean values
5. Numbers should not be quoted unless they are strings
6. Do not use trailing commas

Extract these fields:

1. policyName: The official title of the policy.
2. policyId: A unique ID in the format "Policy Name - Policy Number" (if available).
3. policyDescription: A detailed summary or abstract of the policy, including its goals, scope, and key features.
4. targetGroups: List of all relevant stakeholder groups (select from: "Government", "Industry", "Academia", "Small Businesses", "General Public", "Specific Sector", "Researchers", "Students", "Healthcare Providers", "Financial Institutions", "NGOs", "International Organizations").
5. policyLink: URL if mentioned (use "N/A" if not available).
6. implementation:
   - yearlyBudget: Extract the allocated or estimated annual budget (as string, use "N/A" if not mentioned).
   - budgetCurrency: Mention the currency (e.g., "USD", "EUR", etc. Use "N/A" if not mentioned).
   - privateSecFunding: true/false – does the policy mention any private sector funding?
   - deploymentYear: Year the policy was deployed or is planned for deployment (as number, use null if not available).
7. evaluation:
   - isEvaluated: true/false – has the policy been evaluated?
   - evaluationType: "internal", "external", or "mixed" (use "N/A" if not available)
   - riskAssessment: true/false – was a risk assessment conducted?
   - transparencyScore: Give a score from 0–10 based on how open the policy is.
   - explainabilityScore: Score from 0–10 based on how clearly the policy or related AI systems explain decisions.
   - accountabilityScore: Score from 0–10 based on how strongly responsibility is assigned.
8. participation:
   - hasConsultation: true/false – was public or stakeholder consultation conducted?
   - consultationStartDate: "YYYY-MM-DD" format if available (use "N/A" if not available)
   - consultationEndDate: "YYYY-MM-DD" format if available (use "N/A" if not available)
   - commentsPublic: true/false – are consultation comments made public?
   - stakeholderScore: 0–10 rating of stakeholder participation based on detail and breadth
9. alignment:
   - aiPrinciples: List any AI principles explicitly aligned (e.g., "Transparency", "Privacy", "Human Control", etc.)
   - humanRightsAlignment: true/false
   - environmentalConsiderations: true/false
   - internationalCooperation: true/false

IMPORTANT: Respond ONLY with valid JSON. Do not include any explanatory text before or after the JSON.

Document text to analyze:
{text_content[:8000]}  # Limit text to avoid token limits

Output example format:
{{
  "policyName": "Responsible AI Strategy",
  "policyId": "Responsible AI Strategy - 2024-01",
  "policyDescription": "This strategy aims to ensure ethical AI deployment by prioritizing transparency...",
  "targetGroups": ["Government", "Academia", "Industry"],
  "policyLink": "https://example.com/ai-policy",
  "implementation": {{
    "yearlyBudget": "5000000",
    "budgetCurrency": "USD",
    "privateSecFunding": true,
    "deploymentYear": 2024
  }},
  "evaluation": {{
    "isEvaluated": true,
    "evaluationType": "mixed",
    "riskAssessment": true,
    "transparencyScore": 8,
    "explainabilityScore": 7,
    "accountabilityScore": 9
  }},
  "participation": {{
    "hasConsultation": true,
    "consultationStartDate": "2023-03-01",
    "consultationEndDate": "2023-05-15",
    "commentsPublic": true,
    "stakeholderScore": 9
  }},
  "alignment": {{
    "aiPrinciples": ["Transparency", "Accountability", "Privacy", "Ethics"],
    "humanRightsAlignment": true,
    "environmentalConsiderations": true,
    "internationalCooperation": true
  }}
}}

Remember: Use "N/A" (with quotes) for missing string values, null for missing numbers, and ensure all JSON is properly quoted and formatted.
"""
        return prompt
    
    def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API for analysis."""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama3-70b-8192",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2048
            }
            
            response = requests.post(
                self.groq_api_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate AI response."""
        try:
            # Clean the response to extract JSON
            response = response.strip()
            
            # Try to find JSON content between curly braces
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                # If no JSON braces found, try to extract from code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
                if json_match:
                    json_content = json_match.group(1)
                else:
                    logger.error(f"No valid JSON found in AI response: {response}")
                    # Return default empty structure if JSON parsing fails
                    return self._get_default_extracted_data()
            else:
                json_content = response[start_idx:end_idx]
            
            # Fix common JSON issues before parsing
            json_content = self._fix_json_issues(json_content)
            
            # Attempt to parse JSON
            try:
                extracted_data = json.loads(json_content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {str(e)}")
                logger.error(f"Attempted to parse: {json_content}")
                # Return default structure if parsing fails
                return self._get_default_extracted_data()
            
            # Validate and set defaults for required fields
            validated_data = self._validate_extracted_data(extracted_data)
            
            return validated_data
            
        except Exception as e:
            logger.error(f"Error processing AI response: {str(e)}")
            logger.error(f"Full response: {response}")
            # Return default structure on any error
            return self._get_default_extracted_data()
    
    def _fix_json_issues(self, json_content: str) -> str:
        """Fix common JSON issues in AI responses."""
        import re
        
        # Fix unquoted N/A values
        json_content = re.sub(r':\s*N/A\s*([,}])', r': "N/A"\1', json_content)
        
        # Fix unquoted null values
        json_content = re.sub(r':\s*null\s*([,}])', r': null\1', json_content)
        
        # Fix unquoted true/false values (ensure they're lowercase)
        json_content = re.sub(r':\s*True\s*([,}])', r': true\1', json_content)
        json_content = re.sub(r':\s*False\s*([,}])', r': false\1', json_content)
        
        # Remove any trailing commas before closing braces
        json_content = re.sub(r',\s*}', '}', json_content)
        json_content = re.sub(r',\s*]', ']', json_content)
        
        return json_content
    
    def _get_default_extracted_data(self) -> Dict[str, Any]:
        """Return default extracted data structure when AI parsing fails."""
        return {
            "policyName": "",
            "policyId": "",
            "policyDescription": "",
            "targetGroups": [],
            "policyLink": "",
            "implementation": {
                "yearlyBudget": "",
                "budgetCurrency": "USD",
                "privateSecFunding": False,
                "deploymentYear": 2025
            },
            "evaluation": {
                "isEvaluated": False,
                "evaluationType": "",
                "riskAssessment": False,
                "transparencyScore": 0,
                "explainabilityScore": 0,
                "accountabilityScore": 0
            },
            "participation": {
                "hasConsultation": False,
                "consultationStartDate": "",
                "consultationEndDate": "",
                "commentsPublic": False,
                "stakeholderScore": 0
            },
            "alignment": {
                "aiPrinciples": [],
                "humanRightsAlignment": False,
                "environmentalConsiderations": False,
                "internationalCooperation": False
            },
            "error": "AI analysis returned invalid JSON - using default structure"
        }
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and set defaults for extracted data."""
        try:
            # Ensure all string values are not None
            def safe_string(value, default=""):
                if value is None:
                    return default
                return str(value) if value else default
            
            def safe_list(value):
                if value is None or not isinstance(value, list):
                    return []
                return value
            
            def safe_dict(value, default_dict=None):
                if value is None or not isinstance(value, dict):
                    return default_dict or {}
                return value
            
            def safe_bool(value, default=False):
                if value is None:
                    return default
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes']
                return bool(value)
            
            def safe_number(value, default=0):
                if value is None:
                    return default
                try:
                    return int(value) if isinstance(value, (int, str)) else default
                except (ValueError, TypeError):
                    return default
            
            # Set defaults for missing fields with null checking
            validated_data = {
                "policyName": safe_string(data.get("policyName")),
                "policyId": safe_string(data.get("policyId")),
                "policyDescription": safe_string(data.get("policyDescription")),
                "targetGroups": safe_list(data.get("targetGroups")),
                "policyLink": safe_string(data.get("policyLink")),
                "implementation": {
                    "yearlyBudget": safe_string(data.get("implementation", {}).get("yearlyBudget")),
                    "budgetCurrency": safe_string(data.get("implementation", {}).get("budgetCurrency"), "USD"),
                    "privateSecFunding": safe_bool(data.get("implementation", {}).get("privateSecFunding")),
                    "deploymentYear": safe_number(data.get("implementation", {}).get("deploymentYear"), datetime.now().year)
                },
                "evaluation": {
                    "isEvaluated": safe_bool(data.get("evaluation", {}).get("isEvaluated")),
                    "evaluationType": safe_string(data.get("evaluation", {}).get("evaluationType")),
                    "riskAssessment": safe_bool(data.get("evaluation", {}).get("riskAssessment")),
                    "transparencyScore": safe_number(data.get("evaluation", {}).get("transparencyScore")),
                    "explainabilityScore": safe_number(data.get("evaluation", {}).get("explainabilityScore")),
                    "accountabilityScore": safe_number(data.get("evaluation", {}).get("accountabilityScore"))
                },
                "participation": {
                    "hasConsultation": safe_bool(data.get("participation", {}).get("hasConsultation")),
                    "consultationStartDate": safe_string(data.get("participation", {}).get("consultationStartDate")),
                    "consultationEndDate": safe_string(data.get("participation", {}).get("consultationEndDate")),
                    "commentsPublic": safe_bool(data.get("participation", {}).get("commentsPublic")),
                    "stakeholderScore": safe_number(data.get("participation", {}).get("stakeholderScore"))
                },
                "alignment": {
                    "aiPrinciples": safe_list(data.get("alignment", {}).get("aiPrinciples")),
                    "humanRightsAlignment": safe_bool(data.get("alignment", {}).get("humanRightsAlignment")),
                    "environmentalConsiderations": safe_bool(data.get("alignment", {}).get("environmentalConsiderations")),
                    "internationalCooperation": safe_bool(data.get("alignment", {}).get("internationalCooperation"))
                }
            }
            
            return validated_data
            
        except Exception as e:
            logger.error(f"Error validating extracted data: {str(e)}")
            raise

# Create service instance
ai_analysis_service = AIAnalysisService()
