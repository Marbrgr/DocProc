from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum

class WorkflowEngineType(Enum):
    LANGCHAIN = "langchain"
    LLAMAINDEX = "llamaindex"
    HAYSTACK = "haystack"
    OPENAI_DIRECT = "openai_direct"

class WorkflowEngine(ABC):
    
    @abstractmethod
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def classify_document(self, text: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def search_documents(self, query: str, user_id: str, documents: List[str]) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def answer_question(self, question: str, user_id: str, context: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def add_document_to_vectorstore(self, doc_id: str, text: str, user_id: str) -> bool:
        pass
    
    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def engine_type(self) -> WorkflowEngineType:
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        pass

class WorkflowEngineFactory:

    _engines = {}
    _engine_instances = {}

    @classmethod
    def register_engine(cls, engine_type: WorkflowEngineType, engine_class):
        cls._engines[engine_type] = engine_class
    
    @classmethod
    def create_engine(cls, engine_type: WorkflowEngineType, **kwargs) -> WorkflowEngine:
        if engine_type not in cls._engines:
            raise ValueError(f"engine type {engine_type} not registered")
        
        return cls._engines[engine_type](**kwargs)
    
    @classmethod
    def get_engine(cls, engine_type: WorkflowEngineType) -> Optional[WorkflowEngine]:
        """Get an engine instance, creating it if it doesn't exist"""
        try:
            if engine_type not in cls._engine_instances:
                if engine_type not in cls._engines:
                    return None
                
                engine_instance = cls._engines[engine_type]()
                if engine_instance.initialize():
                    cls._engine_instances[engine_type] = engine_instance
                else:
                    return None
            
            return cls._engine_instances[engine_type]
        except Exception:
            return None
    
    @classmethod
    def get_available_engines(cls) -> List[WorkflowEngineType]:
        return list(cls._engines.keys())


    