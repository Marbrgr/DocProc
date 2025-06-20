from sqlalchemy import Column, String, Boolean, Integer
from .base import BaseModel
from sqlalchemy.orm import relationship

class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(30), unique=True, nullable=False)
    password = Column(String(255),  nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    documents_processed = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)

    documents = relationship("Document", back_populates="user")
    processing_jobs = relationship("ProcessingJob", back_populates="user")
