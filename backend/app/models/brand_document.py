from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base


class BrandDocument(Base):
    __tablename__ = "brand_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    
    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer)
    file_path = Column(String(500), nullable=False)
    
    # Stato elaborazione
    extraction_status = Column(String(50), default="pending")
    analysis_status = Column(String(50), default="pending")
    
    # Metadata
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"))
    analyzed_at = Column(DateTime(timezone=True))
    description = Column(Text)
    
    # AI generated
    summary = Column(Text)
    key_topics = Column(JSON)
    
    # Relationships
    brand = relationship("Brand", back_populates="documents")
    uploaded_by = relationship("User")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("brand_documents.id", ondelete="CASCADE"), nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    
    # Contenuto
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
    
    # Embedding
    embedding = Column(Vector(1536))
    
    # Metadata
    chunk_type = Column(String(50))
    page_number = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("BrandDocument", back_populates="chunks")
