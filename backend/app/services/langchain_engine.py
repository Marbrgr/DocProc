from typing import Dict, Any, List, Optional
import json
import logging
from pathlib import Path
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain.chains import LLMChain, RetrievalQA
from langchain_core.exceptions import OutputParserException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

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
        self.embeddings = None
        self.vectorstore = None
        self.qa_chain = None
        self._is_available = False
        self.initialize()

    def initialize(self) -> bool:
        try:
            logger.info("🚀 Starting LangChain engine initialization...")
            
            if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip().startswith('sk-'):
                logger.error("❌ OpenAI API key is not found or invalid for LangChain")
                return False

            logger.info("✅ OpenAI API key validated")

            # Initialize LLM
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                openai_api_key=settings.OPENAI_API_KEY.strip()
            )
            logger.info("✅ LLM initialized")

            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY.strip()
            )
            logger.info("✅ Embeddings initialized")
            
            # Setup LangChain vector store
            vector_db_path = Path("./langchain_vector_db")
            vector_db_path.mkdir(exist_ok=True)
            logger.info(f"✅ Vector DB directory created: {vector_db_path.absolute()}")
            
            try:
                logger.info("🔍 Attempting to initialize Chroma vector store...")
                self.vectorstore = Chroma(
                    persist_directory=str(vector_db_path),
                    embedding_function=self.embeddings,
                    collection_name="langchain_documents"
                )
                logger.info("✅ Chroma vector store initialized successfully")
                
                # Test the vector store
                test_doc = Document(page_content="test", metadata={"test": "true"})
                self.vectorstore.add_documents([test_doc])
                logger.info("✅ Vector store test successful")
                
            except Exception as vector_error:
                logger.error(f"❌ Failed to initialize Chroma vector store: {str(vector_error)}")
                logger.error(f"❌ Vector error type: {type(vector_error)}")
                import traceback
                logger.error(f"❌ Vector traceback: {traceback.format_exc()}")
                # Don't fail the whole engine, just set vectorstore to None
                self.vectorstore = None
            
            # Setup Q&A chain only if vector store is available
            if self.vectorstore:
                try:
                    logger.info("🔍 Setting up Q&A chain...")
                    self.qa_chain = RetrievalQA.from_chain_type(
                        llm=self.llm,
                        chain_type="stuff",
                        retriever=self.vectorstore.as_retriever(
                            search_type="similarity",
                            search_kwargs={"k": 4}
                        ),
                        return_source_documents=True
                    )
                    logger.info("✅ Q&A chain initialized")
                except Exception as qa_error:
                    logger.error(f"❌ Failed to setup Q&A chain: {str(qa_error)}")
                    self.qa_chain = None
            else:
                logger.warning("⚠️ Skipping Q&A chain setup - no vector store available")
                self.qa_chain = None

            self._setup_classification_chain()
            logger.info("✅ Classification chain setup")

            # Test connection
            test_result = self.llm.invoke("Test connection")
            logger.info("✅ LLM connection test successful")
            
            self._is_available = True
            logger.info("🎉 LangChain engine initialized successfully!")
            logger.info(f"🔍 Final status - Vector store available: {self.vectorstore is not None}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize LangChain engine: {str(e)}")
            logger.error(f"❌ Exception type: {type(e)}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
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
    
    def search_documents(self, query: str, user_id: str, documents: List[str]) -> List[Dict[str, Any]]:
        """Search documents using LangChain's vector search"""
        if not self._is_available or not self.vectorstore:
            logger.error("LangChain vector store not available")
            return []
        
        try:
            docs = self.vectorstore.similarity_search(
                query, 
                k=4,
                filter={"user_id": user_id}
            )
            
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "doc_id": doc.metadata.get("doc_id", "unknown"),
                    "chunk_id": doc.metadata.get("chunk_id", "unknown"),
                    "engine": "langchain"
                })
            
            logger.info(f"🔍 LangChain found {len(results)} relevant documents")
            return results
            
        except Exception as e:
            logger.error(f"❌ LangChain search failed: {str(e)}")
            return []

    def answer_question(self, question: str, user_id: str, context: str) -> Dict[str, Any]:
        """Answer questions using LangChain's RAG pipeline with user filtering"""
        if not self._is_available or not self.vectorstore:
            logger.error("LangChain Q&A not available")
            return {"answer": "LangChain Q&A not available", "confidence": 0.0, "sources": []}
        
        try:
            # Create user-specific retriever
            user_retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4, "filter": {"user_id": user_id}}
            )
            
            # Create temporary Q&A chain with user-filtered retriever
            user_qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=user_retriever,
                return_source_documents=True
            )
            
            result = user_qa_chain.invoke({"query": question})
            
            sources = []
            if "source_documents" in result:
                for doc in result["source_documents"]:
                    sources.append({
                        "doc_id": doc.metadata.get("doc_id", "unknown"),
                        "chunk_id": doc.metadata.get("chunk_id", "unknown"),
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                    })
            
            confidence = min(1.0, len(sources) * 0.25) if sources else 0.3
            
            return {
                "answer": result.get("result", "No answer found"),
                "confidence": confidence,
                "sources": sources,
                "method": "langchain_rag",
                "engine": "langchain"
            }
            
        except Exception as e:
            logger.error(f"❌ LangChain Q&A failed: {str(e)}")
            return {
                "answer": f"Error: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "method": "error",
                "engine": "langchain"
            }
    
    def add_document_to_vectorstore(self, doc_id: str, text: str, user_id: str) -> bool:
        """Add document to LangChain vector store"""
        if not self._is_available or not self.vectorstore:
            logger.error("LangChain vector store not available")
            return False
            
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            chunks = text_splitter.split_text(text)
            
            documents = []
            for i, chunk in enumerate(chunks):
                doc_metadata = {
                    "doc_id": doc_id,
                    "chunk_id": f"{doc_id}_{i}",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "engine": "langchain",
                    "user_id": user_id
                }
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=doc_metadata
                ))
            
            self.vectorstore.add_documents(documents)
            
            logger.info(f"✅ LangChain added document {doc_id} ({len(chunks)} chunks)")
            return True
            
        except Exception as e:
            logger.error(f"❌ LangChain failed to add document {doc_id}: {str(e)}")
            return False
    
    def remove_document_from_vectorstore(self, doc_id: str, user_id: str) -> bool:
        """Remove document from LangChain vector store"""
        if not self._is_available or not self.vectorstore:
            logger.error("LangChain vector store not available")
            return False
            
        try:
            # Get all documents with this doc_id and user_id
            docs = self.vectorstore.similarity_search(
                query="*",  # Match all documents
                k=1000,     # Get many results to ensure we find all chunks
                filter={"doc_id": doc_id, "user_id": user_id}
            )
            
            if not docs:
                logger.info(f"Document {doc_id} not found in LangChain vector store")
                return True  # Consider it successful if document wasn't there
            
            # Delete documents by their IDs
            ids_to_delete = []
            for doc in docs:
                # Try to get the document ID from metadata
                chunk_id = doc.metadata.get("chunk_id")
                if chunk_id:
                    ids_to_delete.append(chunk_id)
            
            if ids_to_delete:
                # Use Chroma's delete method
                self.vectorstore.delete(ids=ids_to_delete)
                logger.info(f"✅ LangChain removed document {doc_id} ({len(ids_to_delete)} chunks) for user {user_id}")
            else:
                logger.warning(f"No chunk IDs found for document {doc_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ LangChain failed to remove document {doc_id}: {str(e)}")
            # Try alternative deletion method using collection access
            try:
                collection = self.vectorstore._collection
                collection.delete(where={"doc_id": doc_id, "user_id": user_id})
                logger.info(f"✅ LangChain removed document {doc_id} using collection.delete() for user {user_id}")
                return True
            except Exception as e2:
                logger.error(f"❌ LangChain alternative deletion also failed: {str(e2)}")
                return False
    
    def get_engine_info(self) -> Dict[str, Any]:
        return {
            "engine_type": self.engine_type.value,
            "model": settings.OPENAI_MODEL,
            "is_available": self._is_available,
            "rag_available": self.vectorstore is not None,
            "features": {
                "document_classification": True,
                "information_extraction": True,
                "document_search": self.vectorstore is not None,
                "question_answering": self.qa_chain is not None,
                "vector_storage": self.vectorstore is not None
            },
            "rag_implementation": "langchain_chroma",
            "version": "1.0.0"
        }

    @property
    def engine_type(self) -> WorkflowEngineType:
        return WorkflowEngineType.LANGCHAIN

    @property
    def is_available(self) -> bool:
        return self._is_available

# Register the engine
WorkflowEngineFactory.register_engine(WorkflowEngineType.LANGCHAIN, LangChainEngine)