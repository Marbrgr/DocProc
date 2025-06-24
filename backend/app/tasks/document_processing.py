import os
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from app.celery_config import celery_app
from app.database import engine
from app.models import Document, ProcessingJob, JobStatus, FileType, DocumentType
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
    job = None

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
        
        # Store extracted text
        document.extracted_text = extracted_text

        # 🆕 NEW: AI Analysis and Storage
        if len(extracted_text.strip()) > 5:
            try:
                print("🤖 Starting AI analysis...")
                classification = llm_service.classify_document(extracted_text)
                print(f"🤖 Document classified as: {classification}")

                # Map string document type to enum
                document_type_map = {
                    "invoice": DocumentType.INVOICE,
                    "contract": DocumentType.CONTRACT,
                    "receipt": DocumentType.RECEIPT,
                    "form": DocumentType.FORM,
                    "letter": DocumentType.LETTER,
                    "report": DocumentType.REPORT,
                    "other": DocumentType.OTHER,
                    "unknown": DocumentType.UNKNOWN
                }
                
                doc_type_str = classification.get("document_type", "unknown").lower()
                document.ai_document_type = document_type_map.get(doc_type_str, DocumentType.UNKNOWN)
                document.ai_confidence = classification.get("confidence", 0.0)
                document.ai_key_information = classification.get("key_information", {})
                document.ai_analysis_method = classification.get("analysis_method", "unknown")
                document.ai_model_used = classification.get("model_used")
                
                print(f"✅ AI analysis stored: {document.ai_document_type.value} (confidence: {document.ai_confidence:.2f})")
                
            except Exception as e:
                print(f"❌ AI analysis failed: {str(e)}")
                document.ai_document_type = DocumentType.UNKNOWN
                document.ai_confidence = 0.0
                document.ai_key_information = {"error": str(e)}
                document.ai_analysis_method = "error"
        else:
            document.ai_document_type = DocumentType.UNKNOWN
            document.ai_confidence = 0.0
            document.ai_key_information = {"reason": "insufficient_text"}
            document.ai_analysis_method = "no_analysis"

        if job:
            job.job_status = JobStatus.COMPLETED

        db.commit()
        
        return {
            "document_id": document_id,
            "extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
            "ai_analysis": {
                "document_type": document.ai_document_type.value,
                "confidence": document.ai_confidence,
                "method": document.ai_analysis_method
            },
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
        
