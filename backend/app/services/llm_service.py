from typing import Dict, Any, Optional, List
import json
from openai import OpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMService:
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