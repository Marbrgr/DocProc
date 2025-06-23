from fastapi import APIRouter, UploadFile, HTTPException, Depends
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
        })
    return document_list

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
        db.delete(document) # or set document is_active to False for soft delete
        db.commit()
        return {
            "message": "Document deleted successfully",
            "document_id": str(document_id),
            "file_name": document.file_name,
        }
    except Exception as e:
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
