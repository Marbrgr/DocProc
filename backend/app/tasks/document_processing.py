import os
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from app.celery_config import celery_app
from app.database import engine
from app.models import Document, ProcessingJob, JobStatus, FileType, DocumentType, User
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
            # Try multiple PDF processing methods
            pdf_processing_success = False
            
            # Method 1: Try pdf2image + OCR (best for scanned PDFs)
            try:
                print("📄 Attempting PDF processing with pdf2image + OCR...")
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
                pdf_processing_success = True
                print("✅ PDF processed successfully with pdf2image + OCR")
                
            except Exception as e:
                print(f"❌ pdf2image method failed: {str(e)}")
                
                # Method 2: Try PyPDF2 for text extraction (good for text-based PDFs)
                try:
                    print("📄 Attempting PDF processing with PyPDF2...")
                    import PyPDF2
                    
                    with open(file_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        page_texts = []
                        
                        for i, page in enumerate(pdf_reader.pages):
                            try:
                                page_text = page.extract_text()
                                if page_text.strip():
                                    page_texts.append(f"--- Page {i+1} --- \n{page_text}")
                                else:
                                    page_texts.append(f"--- Page {i+1} --- \n[No extractable text]")
                            except Exception as page_error:
                                page_texts.append(f"--- Page {i+1} --- \n[Error extracting text: {str(page_error)}]")
                        
                        extracted_text = "\n\n".join(page_texts)
                        pdf_processing_success = True
                        print("✅ PDF processed successfully with PyPDF2")
                        
                except Exception as pypdf_error:
                    print(f"❌ PyPDF2 method also failed: {str(pypdf_error)}")
                    
                    # Method 3: Try pdfplumber as final fallback
                    try:
                        print("📄 Attempting PDF processing with pdfplumber...")
                        import pdfplumber
                        
                        with pdfplumber.open(file_path) as pdf:
                            page_texts = []
                            
                            for i, page in enumerate(pdf.pages):
                                try:
                                    page_text = page.extract_text()
                                    if page_text and page_text.strip():
                                        page_texts.append(f"--- Page {i+1} --- \n{page_text}")
                                    else:
                                        page_texts.append(f"--- Page {i+1} --- \n[No extractable text]")
                                except Exception as page_error:
                                    page_texts.append(f"--- Page {i+1} --- \n[Error extracting text: {str(page_error)}]")
                            
                            extracted_text = "\n\n".join(page_texts)
                            pdf_processing_success = True
                            print("✅ PDF processed successfully with pdfplumber")
                            
                    except Exception as plumber_error:
                        print(f"❌ pdfplumber method also failed: {str(plumber_error)}")
                        extracted_text = f"PDF Processing Failed - All methods exhausted:\n\n1. pdf2image + OCR: {str(e)}\n\n2. PyPDF2: {str(pypdf_error)}\n\n3. pdfplumber: {str(plumber_error)}\n\nThis PDF may be corrupted, password-protected, or use an unsupported format."

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
        elif document.file_type == FileType.TXT:
            # Read text file
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    extracted_text = file.read()
            except Exception as e:
                extracted_text = f"Error reading text file: {str(e)}"
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

        # 🆕 NEW: Vector Store Integration
                try:
                    print("🔍 Adding document to vector store...")
                    
                    if hasattr(llm_service.current_engine, 'add_document_to_vectorstore'):
                        vector_added = llm_service.current_engine.add_document_to_vectorstore(
                            doc_id=document_id,
                            text=extracted_text,
                            user_id=user_id
                        )

                        if vector_added:
                            print(f"✅ Document added to {llm_service.current_engine.engine_type.value} vector store")

                            if not document.ai_key_information:
                                document.ai_key_information = {}

                            document.ai_key_information["vector_stored"] = True
                            document.ai_key_information["vector_engine"] = llm_service.current_engine.engine_type.value
                        else:
                            print(f"❌ Failed to add document to {llm_service.current_engine.engine_type.value} vector store")
                            if not document.ai_key_information:
                                document.ai_key_information = {}
                            document.ai_key_information["vector_stored"] = False
                            document.ai_key_information["vector_error"] = "Storage failed"

                    else:
                        print(f"Current engine {llm_service.current_engine.engine_type.value} does not support vector storage")
                        if not document.ai_key_information:
                            document.ai_key_information = {}
                        document.ai_key_information["vector_stored"] = False
                        document.ai_key_information["vector_error"] = "Engine does not support vector storage"
                
                except Exception as vector_error:
                    print(f"Vector store error: {str(vector_error)}")
                    if not document.ai_key_information:
                        document.ai_key_information = {}
                    document.ai_key_information["vector_stored"] = False
                    document.ai_key_information["vector_error"] = str(vector_error)
        
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

        # 🆕 NEW: Update user's documents processed count
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.documents_processed = db.query(Document).filter(Document.user_id == user_id).count()
            print(f"✅ Updated user {user.username} documents_processed count to {user.documents_processed}")

        db.commit()
        
        return {
            "document_id": document_id,
            "extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
            "ai_analysis": {
                "document_type": document.ai_document_type.value,
                "confidence": document.ai_confidence,
                "method": document.ai_analysis_method,
                "vector_stored": document.ai_key_information.get("vector_stored", False),
                "vector_engine": document.ai_key_information.get("vector_engine", "unknown"),
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
        
