from typing import Dict, Any, Optional, List
import json
from openai import OpenAI
from app.core.config import settings
import logging
from app.services.workflow_engine import WorkflowEngine, WorkflowEngineType, WorkflowEngineFactory

from app.services.langchain_engine import LangChainEngine
from app.services.openai_direct_engine import OpenAIDirectEngine

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
