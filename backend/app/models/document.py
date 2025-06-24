from .base import BaseModel
from sqlalchemy import Column, String, Integer, LargeBinary, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Enum
import enum

class FileType(enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    CSV = "csv"
    XLSX = "xlsx"
    PNG = "png"
    JPG = "jpg"
    NOT_SPECIFIED = "not_specified"

class DocumentType(enum.Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    RECEIPT = "receipt"
    FORM = "form"
    LETTER = "letter"
    REPORT = "report"
    OTHER = "other"
    UNKNOWN = "unknown"

class Document(BaseModel):
    __tablename__ = "documents"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    file_name = Column(String(255))
    file_size = Column(Integer)
    file_path = Column(String(255)) # in the future will point to s3
    file_type = Column(Enum(FileType), nullable=False, default=FileType.NOT_SPECIFIED)
    extracted_text = Column(Text, nullable=True)
    
    # AI Analysis Fields
    ai_document_type = Column(Enum(DocumentType), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_key_information = Column(JSON, nullable=True)  # Store extracted data as JSON
    ai_analysis_method = Column(String(50), nullable=True)  # "openai" or "mock"
    ai_model_used = Column(String(100), nullable=True)  # "gpt-4o-mini" etc.

    # python relationships
    user = relationship("User", back_populates="documents")
    processing_jobs = relationship("ProcessingJob", back_populates="document")


    