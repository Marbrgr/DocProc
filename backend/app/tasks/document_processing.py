import os
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from app.celery_config import celery_app
from app.database import engine
from app.models import Document, ProcessingJob, JobStatus, FileType
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from app.services.llm_service import llm_service

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\Program Files\Poppler\poppler-24.08.0\Library\bin"

@celery_app.task
def process_document(document_id: str, user_id: str):
    db = SessionLocal()

    try:
        # Get document from db
        document = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
        if not document:
            return {"error": "Document not found"}

        # Update job status to PROCESSING
        job = db.query(ProcessingJob).filter(ProcessingJob.document_id == document_id).first()
        if job:
            job.job_status = JobStatus.PROCESSING
            db.commit()
        
        extracted_text = ""
        file_path = Path(document.file_path)

        if document.file_type == FileType.PDF:
            # convert pdf to images and OCR each page
            try:
                poppler_bin = Path(POPPLER_PATH)
                print(f"Poppler path exists: {poppler_bin.exists()}")
                if poppler_bin.exists():
                    executables = list(poppler_bin.glob("*.exe"))
                    print(f"Found executables: {[exe.name for exe in executables]}")
                images = convert_from_path(str(file_path), poppler_path=POPPLER_PATH)
                page_texts = []

                for i, image in enumerate(images):
                    page_text = pytesseract.image_to_string(image)
                    page_texts.append(f"--- Page {i+1} --- \n{page_text}")
                
                extracted_text = "\n\n".join(page_texts)
            except Exception as e:
                extracted_text = f"Error processing PDF: {str(e)}"

        elif document.file_type in [FileType.PNG, FileType.JPG]:
            # OCR for images
            try:
                image = Image.open(str(file_path))

                # Debug statements
                print(f"Image size: {image.size}")
                print(f"Image format: {image.format}")
                print(f"Image mode: {image.mode}")

                extracted_text = pytesseract.image_to_string(image)
                print(f"Raw OCR result: {extracted_text}")

                if len(extracted_text.strip()) < 5:
                    configs = [
                        '--psm 6', # PSM 6: Assumes a single text block
                        '--psm 8', # PSM 8: Assumes a single word
                        '--psm 13', # PSM 13: Raw line
                    ]

                    for config in configs:
                        try:
                            extracted_text = pytesseract.image_to_string(image, config=config)
                            if len(extracted_text.strip()) > 5:
                                break
                        except Exception as e:
                            print(f"Error with config {config}: {str(e)}")

                if len(extracted_text.strip()) < 5:
                    extracted_text = "OCR failed to extract text"

            except Exception as e:
                extracted_text = f"Error processing image: {str(e)}"
        else:
            extracted_text = f"Unsupported file type: {document.file_type}"
        
        document.extracted_text = extracted_text

        if len(extracted_text.strip()) > 5:
            try:
                # classify document type
                classification = llm_service.classify_document(extracted_text)
                print(f"Document classified as: {classification}")

                # TODO: possibly store structured data? 
            except Exception as e:
                print(f"AI analysis failed: {str(e)}")
                classification = {"document_type": "unknown", "confidence": 0.0}
        else:
            classification = {"document_type": "no_text", "confidence": 0.0}

        if job:
            job.job_status = JobStatus.COMPLETED

        db.commit()
        
        return {
            "document_id": document_id,
            "extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
            "classification": classification,
            "job_status": JobStatus.COMPLETED.value,
            "total_characters": len(extracted_text),
        }
    
    except Exception as e:
        if job:
            job.job_status = JobStatus.FAILED
            db.commit()
        
        return {"error": str(e)}

    finally:
        db.close()
        
