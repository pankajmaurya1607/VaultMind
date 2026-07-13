from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from pgvector.sqlalchemy import Vector


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_metadata = Column("metadata", JSON, default=dict)
    embedding = Column(Vector(1536), nullable=True)
    embedding_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="chunks")
