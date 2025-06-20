from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum
import enum
from .base import BaseModel
from sqlalchemy.orm import relationship

class JobStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingJob(BaseModel):
    __tablename__ = "processing_jobs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    job_status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING)

    user = relationship("User", back_populates="processing_jobs")
    document = relationship("Document", back_populates="processing_jobs")