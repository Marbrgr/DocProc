from typing import Dict, Any, Optional, List
import json
from openai import OpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, preferred_engine: WorkflowEngineType = None):
        self.current_engine: Optional[WorkflowEngine] = None
        self.available_engines: Dict[WorkflowEngineType, WorkflowEngine] = {}

        preferred = preferred_engine or self._get_preferred_engine_from_config()

        self._initialize_engines()

        self._set_current_engine(preferred)
    
    def _get_preferred_engine_from_config(self) -> WorkflowEngineType:
        engine_name = getattr(settings, 'WORKFLOW_ENGINE', 'langchain').lower()
        try:
            return WorkflowEngineType(engine_name)
        except ValueError:
            logger.warning(f"Unknown engine type: '{engine_name}', defaulting to LangChain")
            return WorkflowEngineType.LANGCHAIN
    
    def _initialize_engines(self):
        engine_types = [WorkflowEngineType.LANGCHAIN, WorkflowEngineType.OPENAI_DIRECT]

        for engine_type in engine_types:
            try:
                engine = WorkflowEngineFactory.create_engine(engine_type)
                if engine.is_available:
                    self.available_engines[engine_type] = engine
                    logger.info(f"{engine_type.value} engine initialized and available")
                else:
                    logger.warning(f"{engine_type.value} engine initialized but not available")
            except Exception as e:
                logger.error(f"Failed to initialize {engine_type.value} engine: {str(e)}")
            
    def _set_current_engine(self, engine_type: WorkflowEngineType):
        if engine_type in self.available_engines:
            self.current_engine = self.available_engines[engine_type]
            logger.info(f"Active engine set to {engine_type.value}")
        else:
            if self.available_engines:
                fallback_type = next(iter(self.available_engines.keys()))
                self.current_engine = self.available_engines[fallback_type]
                logger.info(f"Requested engine {engine_type.value} not available, using {fallback_type.value} as fallback")
            else:
                logger.error("No workflow engines available")
                self.current_engine = None
    
    def switch_engine(self, engine_type: WorkflowEngineType) -> bool:
        if engine_type not in self.available_engines:
            logger.error(f"Engine {engine_type.value} not available")
            return False
        
        old_engine = self.current_engine.engine_type if self.current_engine else None
        self.current_engine = self.available_engines[engine_type]
        logger.info(f"Switched engine from {old_engine} to {engine_type.value}")
        return True
    
    def classify_document(self, text: str) -> Dict[str, Any]:
        """Classify document using the current workflow engine"""
        if not self.current_engine:
            return {
                "document_type": "unknown",
                "confidence": 0.0,
                "key_information": {},
                "analysis_method": "no_engine_available",
                "error": "No workflow engine available"
            }
        
        try:
            result = self.current_engine.classify_document(text)
            # Add engine information to result
            result["engine_used"] = self.current_engine.engine_type.value
            return result
        except Exception as e:
            logger.error(f"❌ Classification failed with {self.current_engine.engine_type.value}: {str(e)}")
            
            # Try fallback to other engines
            for engine_type, engine in self.available_engines.items():
                if engine != self.current_engine:
                    try:
                        logger.info(f"🔄 Trying fallback engine: {engine_type.value}")
                        result = engine.classify_document(text)
                        result["engine_used"] = engine_type.value
                        result["fallback_reason"] = str(e)
                        return result
                    except Exception as fallback_error:
                        logger.error(f"❌ Fallback engine {engine_type.value} also failed: {str(fallback_error)}")
            
            # All engines failed
            return {
                "document_type": "unknown",
                "confidence": 0.0,
                "key_information": {},
                "analysis_method": "all_engines_failed",
                "error": str(e)
            }
    
    def search_documents(self, query: str, documents: List[str]) -> List[Dict[str, Any]]:
        """Search documents using current engine"""
        if not self.current_engine:
            return []
        return self.current_engine.search_documents(query, documents)
    
    def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        """Answer questions using current engine"""
        if not self.current_engine:
            return {"answer": "No engine available", "confidence": 0.0}
        return self.current_engine.answer_question(question, context)
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get status of all engines"""
        return {
            "current_engine": self.current_engine.engine_type.value if self.current_engine else None,
            "available_engines": [engine_type.value for engine_type in self.available_engines.keys()],
            "engine_details": {
                engine_type.value: engine.get_engine_info()
                for engine_type, engine in self.available_engines.items()
            }
        }
    
    def get_available_engines(self) -> List[str]:
        """Get list of available engine names"""
        return [engine_type.value for engine_type in self.available_engines.keys()]
    
llm_service = LLMService()









    def __init__(self):
        self.client = None
        
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip().startswith('sk-'):
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY.strip())
                self.mock_mode = False
                logger.info("✅ OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
                self.mock_mode = True
        else:
            self.mock_mode = True
            logger.warning("⚠️ OpenAI API key not found or invalid. Using mock mode.")

    def _mock_classification(self, text: str) -> Dict[str, Any]:
        """Enhanced fallback when OpenAI isn't available"""
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
                "analysis_method": "mock"
            }
        elif any(word in text_lower for word in ['contract', 'agreement', 'terms', 'party', 'effective date']):
            return {
                "document_type": "contract", 
                "confidence": 0.70,
                "key_information": {
                    "contract_type": "Not extracted (mock mode)",
                    "parties": "Not extracted (mock mode)"
                },
                "analysis_method": "mock"
            }
        else:
            return {
                "document_type": "document", 
                "confidence": 0.60,
                "key_information": {},
                "analysis_method": "mock"
            }

    def _call_openai_classification(self, text: str) -> Dict[str, Any]:
        """Real AI classification using OpenAI"""
        
        # Control costs by truncating long documents
        max_chars = 8000  # About 2000 tokens
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
            parsed_result["analysis_method"] = "openai"
            parsed_result["model_used"] = settings.OPENAI_MODEL
            
            # Validate required fields
            required_fields = ["document_type", "confidence", "key_information"]
            if not all(field in parsed_result for field in required_fields):
                raise ValueError(f"Missing required fields in OpenAI response")
            
            # Ensure confidence is valid
            parsed_result["confidence"] = max(0.0, min(1.0, float(parsed_result["confidence"])))
            
            logger.info(f"🤖 OpenAI classified document as: {parsed_result['document_type']} (confidence: {parsed_result['confidence']:.2f})")
            return parsed_result

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse OpenAI JSON response: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ OpenAI API call failed: {str(e)}")
            raise

    def classify_document(self, text: str) -> Dict[str, Any]:
        """Main entry point for document classification"""
        
        if not text or len(text.strip()) < 10:
            return {
                "document_type": "unknown",
                "confidence": 0.0,
                "key_information": {},
                "analysis_method": "insufficient_text"
            }

        if self.mock_mode:
            logger.info("Using mock classification")
            return self._mock_classification(text)
        
        try:
            return self._call_openai_classification(text)
        except Exception as e:
            logger.error(f"OpenAI failed, falling back to mock: {str(e)}")
            result = self._mock_classification(text)
            result["fallback_reason"] = str(e)
            return result

# Global instance
llm_service = LLMService()