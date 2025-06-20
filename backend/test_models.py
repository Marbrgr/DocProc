import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import User, Document, ProcessingJob, FileType, JobStatus

def test_models():
    # Create database engine and session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        print("🧪 Testing database models...")
        
        # Create a test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            password="hashed_password_here",  # In real app, this would be hashed
            documents_processed=0,
            is_admin=False
        )
        session.add(test_user)
        session.commit()
        print(f"✅ Created user: {test_user.username} (ID: {test_user.id})")
        
        # Create a test document
        test_document = Document(
            user_id=test_user.id,
            file_name="test_invoice.pdf",
            file_size=1024000,  # 1MB
            file_path="/uploads/test_invoice_2024.pdf",
            file_type=FileType.PDF
        )
        session.add(test_document)
        session.commit()
        print(f"✅ Created document: {test_document.file_name} (ID: {test_document.id})")
        
        # Create a processing job
        test_job = ProcessingJob(
            user_id=test_user.id,
            document_id=test_document.id,
            job_status=JobStatus.PENDING
        )
        session.add(test_job)
        session.commit()
        print(f"✅ Created processing job: {test_job.job_status.value} (ID: {test_job.id})")
        
        # Test relationships by querying back
        print("\n🔍 Testing relationships...")
        
        # Get user and their documents
        user_with_docs = session.query(User).filter(User.username == "testuser").first()
        print(f"📄 User '{user_with_docs.username}' has {len(user_with_docs.documents)} document(s)")
        
        # Get document and its owner
        doc_with_user = session.query(Document).filter(Document.file_name == "test_invoice.pdf").first()
        print(f"👤 Document '{doc_with_user.file_name}' belongs to user '{doc_with_user.user.username}'")
        
        # Get processing job and related data
        job_with_relations = session.query(ProcessingJob).first()
        print(f"⚡ Processing job status: {job_with_relations.job_status.value}")
        print(f"   - User: {job_with_relations.user.username}")
        print(f"   - Document: {job_with_relations.document.file_name}")
        
        print("\n🎉 All tests passed! Database models are working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        session.rollback()
        
    finally:
        session.close()

if __name__ == "__main__":
    test_models()
