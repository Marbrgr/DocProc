from fastapi import APIRouter, UploadFile, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import datetime
import os
from pathlib import Path
from app.models import Document, FileType, User, ProcessingJob, JobStatus
from app.database import get_db
from app.core.config import settings
from app.utils.jwt import get_current_user
from app.models import User
from app.tasks.document_processing import process_document
from app.services.llm_service import llm_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB

@router.post("/upload")
async def upload_document(
    file: UploadFile, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    if (file.size > MAX_FILE_SIZE):
        raise HTTPException(status_code=400, detail="File size exceeds the maximum allowed size of 10MB")
    

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{file.filename}_{timestamp}"
    file_path = upload_dir / unique_filename

    # try to save file to disk
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_type = FileType.NOT_SPECIFIED
        if (file.content_type == "application/pdf"):
            file_type = FileType.PDF
        elif file.content_type == "image/png":
            file_type = FileType.PNG
        elif file.content_type == "image/jpeg":
            file_type = FileType.JPG
        elif file.content_type == "text/plain":
            file_type = FileType.TXT
        else:
            if file.filename.lower().endswith('.pdf'):
                file_type = FileType.PDF
            elif file.filename.lower().endswith('.png'):
                file_type = FileType.PNG
            elif file.filename.lower().endswith('.jpg') or file.filename.lower().endswith('.jpeg'):
                file_type = FileType.JPG
            elif file.filename.lower().endswith('.txt'):
                file_type = FileType.TXT
            else:
                file_type = FileType.NOT_SPECIFIED
        


        new_doc = Document(
            user_id=current_user.id,
            file_name=file.filename,
            file_size=file.size,
            file_path=str(file_path),
            file_type=file_type
        )

        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        # create processing job
        processing_job = ProcessingJob(
            user_id=current_user.id,
            document_id=new_doc.id,
            job_status=JobStatus.PENDING
        )
        db.add(processing_job)
        db.commit()
        db.refresh(processing_job)

        # trigger background processing
        task = process_document.delay(str(new_doc.id), str(current_user.id))

        return {
            "message": "Document uploaded successfully",
            "document_id": str(new_doc.id),
            "processing_job_id": str(processing_job.id),
            "task_id": str(task.id),
            "file_path": str(file_path),
            "status": "processing_started",
            "file_name": file.filename,
            "file_size": file.size,
            "file_type": file_type,
            "user_id": str(current_user.id),
            "username": current_user.username,
            "created_at": new_doc.created_at,
        }
    
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/list")
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    documents = db.query(Document).filter(Document.user_id == current_user.id).all()
    document_list = []
    for doc in documents:
        document_list.append({
            "id": str(doc.id),
            "file_name": doc.file_name,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "created_at": doc.created_at,
            "ai_document_type": doc.ai_document_type.value if doc.ai_document_type else None,
            "ai_confidence": doc.ai_confidence,
            "ai_key_information": doc.ai_key_information,
            "ai_analysis_method": doc.ai_analysis_method,
            "ai_model_used": doc.ai_model_used,
        })
    return document_list

@router.get("/engines/status")
async def get_engine_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of all available engines"""
    try:
        status_info = llm_service.get_engine_status()
        return status_info
    except Exception as e:
        logger.error(f"Failed to get engine status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get engine status: {str(e)}"
        )

@router.post("/engines/switch")
async def switch_engine(
    engine_type: str,
    current_user: User = Depends(get_current_user)
):
    """Switch to a different engine"""
    try:
        from app.services.workflow_engine import WorkflowEngineType
        
        # Validate engine type
        try:
            engine_enum = WorkflowEngineType(engine_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid engine type. Available: {[e.value for e in WorkflowEngineType]}"
            )
        
        # Switch engine
        success = llm_service.switch_engine(engine_enum)
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Engine {engine_type} is not available"
            )
        
        return {
            "message": f"Successfully switched to {engine_type}",
            "current_engine": llm_service.current_engine.engine_type.value,
            "engine_info": llm_service.current_engine.get_engine_info()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to switch engine: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to switch engine: {str(e)}"
        )

@router.post("/cleanup-vectors")
async def cleanup_orphaned_vectors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up orphaned vector entries that reference deleted documents"""
    try:
        # Get all valid document IDs for this user
        valid_doc_ids = set(
            str(doc.id) for doc in 
            db.query(Document).filter(Document.user_id == current_user.id).all()
        )
        
        cleanup_results = []
        
        # Clean up each engine's vector store
        from app.services.workflow_engine import WorkflowEngineFactory, WorkflowEngineType
        
        for engine_type in WorkflowEngineType:
            try:
                engine = WorkflowEngineFactory.get_engine(engine_type)
                if not engine or not hasattr(engine, 'search_documents'):
                    continue
                
                # Get all documents in vector store for this user
                all_results = engine.search_documents(
                    query="*",  # Match everything
                    user_id=str(current_user.id),
                    documents=[]
                )
                
                orphaned_docs = []
                for result in all_results:
                    doc_id = result.get("doc_id")
                    if doc_id and doc_id not in valid_doc_ids:
                        orphaned_docs.append(doc_id)
                
                # Remove orphaned documents
                removed_count = 0
                if hasattr(engine, 'remove_document_from_vectorstore'):
                    for orphaned_doc_id in set(orphaned_docs):  # Remove duplicates
                        try:
                            removed = engine.remove_document_from_vectorstore(
                                doc_id=orphaned_doc_id,
                                user_id=str(current_user.id)
                            )
                            if removed:
                                removed_count += 1
                        except Exception as e:
                            logger.error(f"Failed to remove orphaned doc {orphaned_doc_id}: {str(e)}")
                
                cleanup_results.append({
                    "engine": engine_type.value,
                    "total_vector_docs": len(all_results),
                    "orphaned_found": len(set(orphaned_docs)),
                    "orphaned_removed": removed_count
                })
                
                logger.info(f"🧹 Vector cleanup for {engine_type.value}: found {len(set(orphaned_docs))} orphaned, removed {removed_count}")
                
            except Exception as engine_error:
                logger.error(f"❌ Vector cleanup failed for {engine_type.value}: {str(engine_error)}")
                cleanup_results.append({
                    "engine": engine_type.value,
                    "error": str(engine_error)
                })
        
        return {
            "message": "Vector cleanup completed",
            "user_id": str(current_user.id),
            "valid_documents": len(valid_doc_ids),
            "cleanup_results": cleanup_results
        }
        
    except Exception as e:
        logger.error(f"Vector cleanup failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Vector cleanup failed: {str(e)}"
        )

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(document.id),
        "file_name": document.file_name,
        "file_size": document.file_size,
        "file_type": document.file_type,
        "created_at": document.created_at,
        "extracted_text": document.extracted_text,
        "ai_document_type": document.ai_document_type.value if document.ai_document_type else None,
        "ai_confidence": document.ai_confidence,
        "ai_key_information": document.ai_key_information,
        "ai_analysis_method": document.ai_analysis_method,
        "ai_model_used": document.ai_model_used,
    }

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        filename=document.file_name,
        media_type="application/octet-stream"
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # 🆕 NEW: Clean up vector databases before deleting from main database
        vector_cleanup_results = []
        
        # Get all available engines and clean up their vector stores
        from app.services.llm_service import llm_service
        from app.services.workflow_engine import WorkflowEngineFactory, WorkflowEngineType
        
        for engine_type in WorkflowEngineType:
            try:
                engine = WorkflowEngineFactory.get_engine(engine_type)
                if engine and hasattr(engine, 'remove_document_from_vectorstore'):
                    removed = engine.remove_document_from_vectorstore(
                        doc_id=str(document_id),
                        user_id=str(current_user.id)
                    )
                    vector_cleanup_results.append({
                        "engine": engine_type.value,
                        "removed": removed
                    })
                    logger.info(f"🗑️ Vector cleanup for {engine_type.value}: {'✅' if removed else '❌'}")
            except Exception as vector_error:
                logger.error(f"❌ Vector cleanup failed for {engine_type.value}: {str(vector_error)}")
                vector_cleanup_results.append({
                    "engine": engine_type.value,
                    "removed": False,
                    "error": str(vector_error)
                })
        
        # Delete from main database
        db.delete(document)
        
        # 🆕 NEW: Update user's documents processed count
        user = db.query(User).filter(User.id == current_user.id).first()
        if user:
            user.documents_processed = db.query(Document).filter(Document.user_id == current_user.id).count()
        
        db.commit()
        
        return {
            "message": "Document deleted successfully",
            "document_id": str(document_id),
            "file_name": document.file_name,
            "vector_cleanup": vector_cleanup_results
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.get("/{document_id}/status")
async def get_processing_status(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(ProcessingJob).filter(
        ProcessingJob.document_id == document_id,
        ProcessingJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Processing job not found")

    return {
        "document_id": str(document_id),
        "status": job.job_status.value,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }

@router.post("/search")
async def search_documents(
    query: str,
    limit: int = Query(default=4, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search documents using semantic similarity"""
    try:
        if not query.strip():
            raise HTTPException(
                status_code=400,
                detail="Search query cannot be empty"
            )
        
        # Use current engine to search documents
        search_results = llm_service.current_engine.search_documents(
            query=query.strip(),
            user_id=str(current_user.id),
            documents=[]  # Could add document filtering here
        )
        
        return {
            "query": query,
            "results": search_results,
            "engine_used": llm_service.current_engine.engine_type.value if llm_service.current_engine else "none",
            "total_results": len(search_results)
        }
        
    except Exception as e:
        logger.error(f"Search failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@router.post("/question")
async def ask_question(
    question: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a question about user's documents using RAG"""
    try:
        if not question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )
        
        # Use current engine to answer question
        answer_result = llm_service.current_engine.answer_question(
            question=question.strip(),
            user_id=str(current_user.id),
            context=""  # Context will be retrieved automatically
        )
        
        return {
            "question": question,
            "answer": answer_result.get("answer", "No answer available"),
            "confidence": answer_result.get("confidence", 0.0),
            "sources": answer_result.get("sources", []),
            "method": answer_result.get("method", "unknown"),
            "engine_used": llm_service.current_engine.engine_type.value if llm_service.current_engine else "none"
        }
        
    except Exception as e:
        logger.error(f"Question answering failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Question answering failed: {str(e)}"
        )
