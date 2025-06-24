from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum

class WorkflowengineType(Enum):
    LANGCHAIN = "langchain"
    LLAMAINDEX = "llamaindex"
    HAYSTACK = "haystack"
    OPENAI_DIRECT = "openai_direct"

class Workflowengine(ABC):
    
    @abstract method
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def classify_document(self, text: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def search_documents(self, query: str, documents: List[str]) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def answer_question(self, question: str, context: str) -> dict[str, Any]:
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

    @classmethod
    def register_engine(cls, engine_type: WorkFlowEngineType, engine_class):
        cls._engines[engine_type] = engine_class
    
    @classmethod
    def create_engine(cls, engine_type: WorkflowengineType, **kwargs) -> Workflowengine:
        if engine_type not in cls._engines:
            raise ValueError(f"engine type {engine_type} not registered")
        
        return cls._engines[engine_type](**kwargs)
    
    @classmethod
    def get_available_engines(cls) -> List[WorkflowEngineType]:
        return list(cls._engines.keys())


    