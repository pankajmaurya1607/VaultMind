from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class GuestDocument(Base):
    __tablename__ = "guest_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guest_token = Column(String(64), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending/processing/ready/failed
    error_message = Column(String(1000), nullable=True)
    chunk_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("GuestChunk", back_populates="document", cascade="all, delete-orphan")
