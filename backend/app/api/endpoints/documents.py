from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
import datetime
import os
from pathlib import Path
from app.models import Document, FileType
from app.database import get_db
from app.core.config import settings

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB

@router.post("/upload")
async def upload_document(file: UploadFile, db: Session = Depends(get_db)):
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
            user_id=None,
            file_name=file.filename,
            file_size=file.size,
            file_path=str(file_path),
            file_type=file_type
        )

        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        return {
            "message": "Document uploaded successfully",
            "document_id": str(new_doc.id),
            "file_path": str(file_path),
            "file_name": file.filename,
            "file_size": file.size,
            "file_type": file_type,
            "created_at": new_doc.created_at,
        }
    
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")