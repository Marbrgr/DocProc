from typing import Dict, Any
import json
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.mock_mode = True # TODO: change to False when ready to use real LLM

    def classify_document(self, text: str) -> Dict[str, Any]:
        if self.mock_mode:
            text_lower = text.lower()
            if any(word in text_lower for word in ['invoice', 'bill', 'amount due', 'total']):
                return {"document_type": "invoice", "confidence": 0.95}
            elif any(word in text_lower for word in ['contract', 'agreement', 'terms']):
                return {"document_type": "contract", "confidence": 0.90}
            else:
                return {"document_type": "form", "confidence": 0.85}
        
        # real implementation will go here
        return self._call_openai_classification(text)
    

llm_service = LLMService()