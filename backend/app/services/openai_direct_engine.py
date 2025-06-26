from typing import Dict, Any, List, Optional
import json
import logging
import numpy as np
from pathlib import Path
import pickle
from openai import OpenAI

from app.core.config import settings
from app.services.workflow_engine import WorkflowEngine, WorkflowEngineType, WorkflowEngineFactory

logger = logging.getLogger(__name__)

class OpenAIDirectEngine(WorkflowEngine):
    def __init__(self):
        self.client = None
        self._is_available = False
        # Custom vector storage for OpenAI Direct
        self.documents = {}  # doc_id -> {text, chunks, embeddings}
        self.vector_store_path = Path("./openai_direct_vectors")
        self.vector_store_path.mkdir(exist_ok=True)
        self.initialize()

    def initialize(self) -> bool:
        """Initialize OpenAI client and load existing vectors"""
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip().startswith('sk-'):
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY.strip())
                self._load_vector_store()
                self._is_available = True
                logger.info("✅ OpenAI direct engine initialized with custom RAG")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI direct engine: {str(e)}")
                self._is_available = False
                return False
        else:
            logger.warning("⚠️ OpenAI API key not found for direct engine")
            self._is_available = False
            return False
    
    def _load_vector_store(self):
        """Load existing vector store from disk"""
        try:
            store_file = self.vector_store_path / "documents.pkl"
            if store_file.exists():
                with open(store_file, 'rb') as f:
                    self.documents = pickle.load(f)
                logger.info(f"📚 Loaded {len(self.documents)} documents from OpenAI Direct vector store")
        except Exception as e:
            logger.error(f"❌ Failed to load vector store: {str(e)}")
            self.documents = {}
    
    def _save_vector_store(self):
        """Save vector store to disk"""
        try:
            store_file = self.vector_store_path / "documents.pkl"
            with open(store_file, 'wb') as f:
                pickle.dump(self.documents, f)
        except Exception as e:
            logger.error(f"❌ Failed to save vector store: {str(e)}")
    
    def _create_embedding(self, text: str) -> List[float]:
        """Create embedding using OpenAI's embedding API"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ Failed to create embedding: {str(e)}")
            return []
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple text chunking implementation"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunks.append(' '.join(chunk_words))
            
            if i + chunk_size >= len(words):
                break
                
        return chunks
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            np_vec1 = np.array(vec1)
            np_vec2 = np.array(vec2)
            
            dot_product = np.dot(np_vec1, np_vec2)
            norm1 = np.linalg.norm(np_vec1)
            norm2 = np.linalg.norm(np_vec2)
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0

    def classify_document(self, text: str) -> Dict[str, Any]:
        """Your existing classification logic"""
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
        """Your existing OpenAI classification"""
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Document truncated for analysis...]"

        classification_prompt = """
You are an expert document classifier. Analyze this document and return a JSON response with:

1. "document_type": Choose from ["invoice", "contract", "receipt", "form", "letter", "report", "other"]
2. "confidence": Float between 0.0-1.0 indicating your confidence level
3. "key_information": Object with extracted details based on document type

Return ONLY valid JSON, no additional text.
        """
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a document classification expert that returns only valid JSON."},
                    {"role": "user", "content": f"{classification_prompt}\n\nDocument text:\n{text}"}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                response_format={"type": "json_object"}
            )

            result = response.choices[0].message.content
            parsed_result = json.loads(result)
            
            parsed_result["analysis_method"] = "openai_direct"
            parsed_result["model_used"] = settings.OPENAI_MODEL
            parsed_result["confidence"] = max(0.0, min(1.0, float(parsed_result.get("confidence", 0.8))))
            
            logger.info(f"🤖 OpenAI direct classified document as: {parsed_result['document_type']}")
            return parsed_result

        except Exception as e:
            logger.error(f"❌ OpenAI API call failed: {str(e)}")
            raise
    
    def _mock_classification(self, text: str) -> Dict[str, Any]:
        """Your existing mock classification"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['invoice', 'bill', 'amount due', 'total', 'payment', '$']):
            return {
                "document_type": "invoice",
                "confidence": 0.75,
                "key_information": {"extraction_method": "keyword_mock"},
                "analysis_method": "openai_direct_mock"
            }
        elif any(word in text_lower for word in ['contract', 'agreement', 'terms', 'party']):
            return {
                "document_type": "contract", 
                "confidence": 0.70,
                "key_information": {"extraction_method": "keyword_mock"},
                "analysis_method": "openai_direct_mock"
            }
        else:
            return {
                "document_type": "other", 
                "confidence": 0.60,
                "key_information": {"extraction_method": "keyword_mock"},
                "analysis_method": "openai_direct_mock"
            }
    
    def search_documents(self, query: str, user_id: str, documents: List[str]) -> List[Dict[str, Any]]:
        """Search documents using custom vector similarity with user filtering"""
        if not self._is_available:
            logger.error("OpenAI Direct engine not available for search")
            return []
        
        if not self.documents:
            logger.info("No documents in OpenAI Direct vector store")
            return []
        
        try:
            # Create embedding for query
            query_embedding = self._create_embedding(query)
            if not query_embedding:
                return []
            
            # Search across user's document chunks only
            results = []
            for doc_id, doc_data in self.documents.items():
                # Filter by user_id stored in document metadata
                if doc_data.get('metadata', {}).get('user_id') != user_id:
                    continue
                    
                for chunk_idx, chunk_data in enumerate(doc_data.get('chunks', [])):
                    chunk_embedding = chunk_data.get('embedding', [])
                    if chunk_embedding:
                        similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                        results.append({
                            "content": chunk_data['text'],
                            "metadata": {
                                "doc_id": doc_id,
                                "chunk_id": f"{doc_id}_{chunk_idx}",
                                "chunk_index": chunk_idx,
                                "engine": "openai_direct",
                                "user_id": user_id
                            },
                            "doc_id": doc_id,
                            "chunk_id": f"{doc_id}_{chunk_idx}",
                            "similarity": similarity,
                            "engine": "openai_direct"
                        })
            
            # Sort by similarity and return top 4
            results.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = results[:4]
            
            logger.info(f"🔍 OpenAI Direct found {len(top_results)} relevant documents for user {user_id}")
            return top_results
            
        except Exception as e:
            logger.error(f"❌ OpenAI Direct search failed: {str(e)}")
            return []

    def answer_question(self, question: str, user_id: str, context: str) -> Dict[str, Any]:
        """Answer questions using direct OpenAI calls with user-filtered context"""
        if not self._is_available:
            return {"answer": "OpenAI Direct not available", "confidence": 0.0, "sources": []}
        
        try:
            # First, search for relevant documents (now user-filtered)
            search_results = self.search_documents(question, user_id, [])  # Pass user_id
            
            if not search_results:
                return {
                    "answer": "No relevant documents found to answer the question.",
                    "confidence": 0.1,
                    "sources": [],
                    "method": "openai_direct_no_context",
                    "engine": "openai_direct"
                }
            
            # Prepare context from search results
            context_parts = []
            sources = []
            
            for result in search_results:
                context_parts.append(result['content'])
                sources.append({
                    "doc_id": result['doc_id'],
                    "chunk_id": result['chunk_id'],
                    "content": result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                })
            
            combined_context = "\n\n".join(context_parts)
            
            # Create Q&A prompt
            qa_prompt = f"""Based on the following context, answer the question. If the answer is not in the context, say so.

Context:
{combined_context}

Question: {question}

Answer:"""
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                    {"role": "user", "content": qa_prompt}
                ],
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=0.1
            )
            
            answer = response.choices[0].message.content
            confidence = min(1.0, len(sources) * 0.25) if sources else 0.3
            
            return {
                "answer": answer,
                "confidence": confidence,
                "sources": sources,
                "method": "openai_direct_rag",
                "engine": "openai_direct"
            }
            
        except Exception as e:
            logger.error(f"❌ OpenAI Direct Q&A failed: {str(e)}")
            return {
                "answer": f"Error: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "method": "error",
                "engine": "openai_direct"
            }
    
    def add_document_to_vectorstore(self, doc_id: str, text: str, user_id: str) -> bool:
        """Add document to custom OpenAI Direct vector store with user isolation"""
        if not self._is_available:
            logger.error("OpenAI Direct engine not available")
            return False
            
        try:
            # Chunk the text
            chunks = self._chunk_text(text)
            
            # Create embeddings for each chunk
            chunk_data = []
            for i, chunk in enumerate(chunks):
                embedding = self._create_embedding(chunk)
                if embedding:
                    chunk_data.append({
                        'text': chunk,
                        'embedding': embedding,
                        'chunk_index': i
                    })
            
            # Store document with user metadata
            self.documents[doc_id] = {
                'text': text,
                'chunks': chunk_data,
                'metadata': {
                    'total_chunks': len(chunk_data),
                    'engine': 'openai_direct',
                    'user_id': user_id  # Store user_id for filtering
                }
            }
            
            # Save to disk
            self._save_vector_store()
            
            logger.info(f"✅ OpenAI Direct added document {doc_id} for user {user_id} ({len(chunk_data)} chunks)")
            return True
            
        except Exception as e:
            logger.error(f"❌ OpenAI Direct failed to add document {doc_id}: {str(e)}")
            return False
    
    def remove_document_from_vectorstore(self, doc_id: str, user_id: str) -> bool:
        """Remove document from custom OpenAI Direct vector store"""
        if not self._is_available:
            logger.error("OpenAI Direct engine not available")
            return False
            
        try:
            if doc_id in self.documents:
                # Verify user ownership before deletion
                doc_user_id = self.documents[doc_id].get('metadata', {}).get('user_id')
                if doc_user_id != user_id:
                    logger.warning(f"User {user_id} attempted to delete document {doc_id} owned by {doc_user_id}")
                    return False
                
                # Remove document
                del self.documents[doc_id]
                
                # Save to disk
                self._save_vector_store()
                
                logger.info(f"✅ OpenAI Direct removed document {doc_id} for user {user_id}")
                return True
            else:
                logger.info(f"Document {doc_id} not found in OpenAI Direct vector store")
                return True  # Consider it successful if document wasn't there
                
        except Exception as e:
            logger.error(f"❌ OpenAI Direct failed to remove document {doc_id}: {str(e)}")
            return False
    
    def get_engine_info(self) -> Dict[str, Any]:
        return {
            "engine_type": self.engine_type.value,
            "model": settings.OPENAI_MODEL,
            "is_available": self._is_available,
            "documents_stored": len(self.documents),
            "features": {
                "document_classification": True,
                "information_extraction": True,
                "document_search": True,
                "question_answering": True,
                "vector_storage": True
            },
            "rag_implementation": "openai_direct_custom",
            "version": "1.0.0"
        }
    
    @property
    def engine_type(self) -> WorkflowEngineType:
        return WorkflowEngineType.OPENAI_DIRECT
    
    @property
    def is_available(self) -> bool:
        return self._is_available

# Register the engine
WorkflowEngineFactory.register_engine(WorkflowEngineType.OPENAI_DIRECT, OpenAIDirectEngine)