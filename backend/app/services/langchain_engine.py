from typing import Dict, Any, List, Optional
import json
import logging
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain.chains import LLMChain
from langchain_core.exceptions import OutputParserException

from app.core.config import settings
from app.services.workflow_engine import WorkflowEngine, WorkflowEngineType, WorkflowEngineFactory

logger = logging.getLogger(__name__)

class DocumentClassification(BaseModel):
    document_type: str = Field(description="Type of document: invoice, contract, receipt, form, letter, report, other")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    key_information: Dict[str, Any] = Field(description="Extracted key information based on document type")
    reasoning: str = Field(description="Brief explanation of the classification decision")

class LangChainEngine(WorkflowEngine):
    def __init__(self):
        self.llm = None
        self.classification_chain = None
        self._is_available = False
        self.initialize()

    def initialize(self) -> bool:
        try:
            if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip().startswith('sk-'):
                logger.error("❌ OpenAI API key is not found or invalid for LangChain")
                return False

            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                openai_api_key=settings.OPENAI_API_KEY.strip()
            )

            self._setup_classification_chain()

            # Test connection
            test_result = self.llm.invoke("Test connection")
            logger.info("✅ LangChain engine initialized successfully")
            self._is_available = True
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize LangChain engine: {str(e)}")
            self._is_available = False
            return False
    
    def _setup_classification_chain(self):
        # Escape the JSON structure with double curly braces
        classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert document classifier. You MUST return a JSON object with exactly these fields:

{{
  "document_type": "one of: invoice, contract, receipt, form, letter, report, other",
  "confidence": "float between 0.0 and 1.0",
  "key_information": {{
    "field1": "extracted_value1",
    "field2": "extracted_value2"
  }},
  "reasoning": "brief explanation of your decision"
}}

For different document types, extract these fields in key_information:
- Invoice: total_amount, vendor_name, invoice_number, due_date
- Contract: contract_type, parties, effective_date, key_terms
- Receipt: total_amount, merchant_name, transaction_date, payment_method
- Form: form_type, purpose, required_fields
- Letter: sender, recipient, date, subject
- Report: report_type, date_range, conclusions

Return ONLY the JSON object, no additional text."""),
            ("human", "Classify this document:\n\n{text}")
        ])

        # Use JsonOutputParser instead of PydanticOutputParser for more flexibility
        parser = JsonOutputParser()

        self.classification_chain = classification_prompt | self.llm | parser

    def classify_document(self, text: str) -> Dict[str, Any]:
        if not self._is_available:
            raise RuntimeError("LangChain engine is not available")

        if not text or len(text.strip()) < 10:
            return {
                "document_type": "unknown",
                "confidence": 0.0,
                "key_information": {},
                "analysis_method": "langchain",
                "reasoning": "Insufficient text for classification"
            }
        
        try:
            # Truncate for cost control
            max_chars = 8000
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[Document truncated for analysis...]"
                logger.info(f"Document truncated to {max_chars} characters for cost control")
            
            # Use the chain
            result = self.classification_chain.invoke({"text": text})
            
            # Validate and normalize the result
            classification_result = self._normalize_result(result)
            
            logger.info(f"🤖 LangChain classified document as: {classification_result['document_type']} (confidence: {classification_result['confidence']:.2f})")
            return classification_result
        
        except Exception as e:
            logger.error(f"❌ LangChain classification failed: {str(e)}")
            # Fall back to the keyword-based classification
            return self._fallback_classification(text)

    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the OpenAI result to our expected format"""
        try:
            # Handle various response formats from OpenAI
            if isinstance(result, dict):
                # Extract or default the required fields
                document_type = result.get("document_type", "other")
                confidence = result.get("confidence", 0.8)
                key_information = result.get("key_information", {})
                reasoning = result.get("reasoning", "Classified using AI analysis")
                
                # If OpenAI returned a different structure, try to extract what we can
                if not document_type or document_type == "other":
                    # Check if the result has document type as a key
                    for key in result.keys():
                        if key.lower() in ['invoice', 'contract', 'receipt', 'form', 'letter', 'report']:
                            document_type = key.lower()
                            key_information = result[key] if isinstance(result[key], dict) else {}
                            break
                
                return {
                    "document_type": document_type.lower(),
                    "confidence": max(0.0, min(1.0, float(confidence))),
                    "key_information": key_information,
                    "analysis_method": "langchain",
                    "model_used": settings.OPENAI_MODEL,
                    "reasoning": reasoning
                }
            else:
                raise ValueError(f"Unexpected result type: {type(result)}")
                
        except Exception as e:
            logger.error(f"❌ Failed to normalize LangChain result: {str(e)}")
            logger.error(f"Raw result was: {result}")
            raise

    def _fallback_classification(self, text: str) -> Dict[str, Any]:
        """Fallback classification when LangChain fails"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['invoice', 'bill', 'amount due', 'total', '$']):
            doc_type = "invoice"
        elif any(word in text_lower for word in ['contract', 'agreement', 'terms', 'party']):
            doc_type = "contract"
        elif any(word in text_lower for word in ['receipt', 'purchase', 'transaction']):
            doc_type = "receipt"
        else:
            doc_type = "other"
        
        return {
            "document_type": doc_type,
            "confidence": 0.6,
            "key_information": {"extraction_method": "fallback_keywords"},
            "analysis_method": "langchain_fallback",
            "model_used": settings.OPENAI_MODEL,
            "reasoning": "Used fallback classification due to LangChain error"
        }
    
    def search_documents(self, query: str, documents: List[str]) -> List[Dict[str, Any]]:
        logger.warning("Document search not implemented for LangChain Engine")
        return []

    def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        logger.warning("Question answering not yet implemented for LangChain Engine")
        return {"answer": "Not implemented yet", "confidence": 0.0}
    
    def get_engine_info(self) -> Dict[str, Any]:
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
            "version": "0.1.0"
        }

    @property
    def engine_type(self) -> WorkflowEngineType:
        return WorkflowEngineType.LANGCHAIN

    @property
    def is_available(self) -> bool:
        return self._is_available

# Register the engine
WorkflowEngineFactory.register_engine(WorkflowEngineType.LANGCHAIN, LangChainEngine)