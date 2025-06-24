from typing import Dict, Any, List
import json
import logging
from openai import OpenAI

from app.core.config import settings
from app.services.workflow_engine import WorkflowEngine, WorkflowEngineType, WorkflowEngineFactory

logger = logging.getLogger(__name__)

class OpenAIDirectEngine(WorkflowEngine):
    def __init__(self):
        self.client = None
        self._is_available = False
        self.initialize()

    def initialize(self) -> bool:
        """Initialize OpenAI client"""
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip().startswith('sk-'):
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY.strip())
                self._is_available = True
                logger.info("✅ OpenAI direct client initialized successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI direct client: {str(e)}")
                self._is_available = False
                return False
        else:
            logger.warning("⚠️ OpenAI API key not found or invalid for direct engine")
            self._is_available = False
            return False
    
    def classify_document(self, text: str) -> Dict[str, Any]:
        """Your original classification logic"""
        if not self._is_available:
            return self._mock_classification(text)
        
        if not text or len(text.strip()) < 10:
            return {
                "document_type": "unknown",
                "confidence": 0.0,
                "key_information": {},
                "analysis_method": "insufficient_text"
            }
        
        try:
            return self._call_openai_classification(text)
        except Exception as e:
            logger.error(f"OpenAI direct failed, falling back to mock: {str(e)}")
            result = self._mock_classification(text)
            result["fallback_reason"] = str(e)
            return result
    
    def _call_openai_classification(self, text: str) -> Dict[str, Any]:
        """Your original OpenAI classification method"""
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Document truncated for analysis...]"
            logger.info(f"Document truncated to {max_chars} characters for cost control")

        classification_prompt = """
You are an expert document classifier. Analyze this document and return a JSON response with:

1. "document_type": Choose from ["invoice", "contract", "receipt", "form", "letter", "report", "other"]
2. "confidence": Float between 0.0-1.0 indicating your confidence level
3. "key_information": Object with extracted details based on document type:

For invoices: {"total_amount": "$X.XX", "vendor_name": "Company", "invoice_number": "#123", "due_date": "YYYY-MM-DD"}
For contracts: {"contract_type": "Service Agreement", "parties": ["Party A", "Party B"], "effective_date": "YYYY-MM-DD"}
For receipts: {"total_amount": "$X.XX", "merchant_name": "Store", "transaction_date": "YYYY-MM-DD"}
For forms: {"form_type": "Application Form", "purpose": "Job Application"}

If information isn't found, use "Unknown" as the value.

Return ONLY valid JSON, no additional text.
        """
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a document classification expert that returns only valid JSON."
                    },
                    {
                        "role": "user", 
                        "content": f"{classification_prompt}\n\nDocument text:\n{text}"
                    }
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                response_format={"type": "json_object"}
            )

            result = response.choices[0].message.content
            parsed_result = json.loads(result)
            
            # Add metadata
            parsed_result["analysis_method"] = "openai_direct"
            parsed_result["model_used"] = settings.OPENAI_MODEL
            
            # Validate required fields
            required_fields = ["document_type", "confidence", "key_information"]
            if not all(field in parsed_result for field in required_fields):
                raise ValueError(f"Missing required fields in OpenAI response")
            
            # Ensure confidence is valid
            parsed_result["confidence"] = max(0.0, min(1.0, float(parsed_result["confidence"])))
            
            logger.info(f"🤖 OpenAI direct classified document as: {parsed_result['document_type']} (confidence: {parsed_result['confidence']:.2f})")
            return parsed_result

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse OpenAI JSON response: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ OpenAI API call failed: {str(e)}")
            raise
    
    def _mock_classification(self, text: str) -> Dict[str, Any]:
        """Your original mock classification"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['invoice', 'bill', 'amount due', 'total', 'payment', '$']):
            return {
                "document_type": "invoice",
                "confidence": 0.75,
                "key_information": {
                    "total_amount": "Not extracted (mock mode)",
                    "vendor_name": "Not extracted (mock mode)",
                    "invoice_number": "Not extracted (mock mode)"
                },
                "analysis_method": "openai_direct_mock"
            }
        elif any(word in text_lower for word in ['contract', 'agreement', 'terms', 'party', 'effective date']):
            return {
                "document_type": "contract", 
                "confidence": 0.70,
                "key_information": {
                    "contract_type": "Not extracted (mock mode)",
                    "parties": "Not extracted (mock mode)"
                },
                "analysis_method": "openai_direct_mock"
            }
        else:
            return {
                "document_type": "other", 
                "confidence": 0.60,
                "key_information": {},
                "analysis_method": "openai_direct_mock"
            }
    
    def search_documents(self, query: str, documents: List[str]) -> List[Dict[str, Any]]:
        """Not implemented in direct engine"""
        return []
    
    def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        """Not implemented in direct engine"""
        return {"answer": "Not implemented in direct engine", "confidence": 0.0}
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get engine information"""
        return {
            "engine_type": self.engine_type.value,
            "model": settings.OPENAI_MODEL,
            "is_available": self._is_available,
            "features": {
                "document_classification": True,
                "information_extraction": True,
                "document_search": False,
                "question_answering": False
            },
            "version": "1.0.0 (original)"
        }
    
    @property
    def engine_type(self) -> WorkflowEngineType:
        return WorkflowEngineType.OPENAI_DIRECT
    
    @property
    def is_available(self) -> bool:
        return self._is_available

# Register the engine
WorkflowEngineFactory.register_engine(WorkflowEngineType.OPENAI_DIRECT, OpenAIDirectEngine)