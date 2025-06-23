from .base import BaseModel
from sqlalchemy import Column, String, Integer, LargeBinary, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
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

class Document(BaseModel):
    __tablename__ = "documents"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    file_name = Column(String(255))
    file_size = Column(Integer)
    file_path = Column(String(255)) # in the future will point to s3
    file_type = Column(Enum(FileType), nullable=False, default=FileType.NOT_SPECIFIED)
    extracted_text = Column(Text, nullable=True)

    # python relationships
    user = relationship("User", back_populates="documents")
    processing_jobs = relationship("ProcessingJob", back_populates="document")


    