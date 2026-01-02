from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import uuid
from pathlib import Path

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.brand import Brand
from app.models.brand_document import BrandDocument, DocumentChunk
from app.api.routes.auth import get_current_user
from app.services.rag_service import rag_service, UPLOAD_DIR

router = APIRouter()

# === SCHEMAS ===

class DocumentOut(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_type: str
    file_size: Optional[int]
    extraction_status: str
    analysis_status: str
    uploaded_at: datetime
    description: Optional[str]
    summary: Optional[str]
    key_topics: Optional[dict]
    chunks_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class SearchQuery(BaseModel):
    query: str
    limit: int = 5

class SearchResult(BaseModel):
    content: str
    filename: str
    similarity: float

# === ENDPOINTS ===

@router.post("/upload/{brand_id}")
async def upload_document(
    brand_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Carica un documento per un brand"""
    
    # Verifica brand
    brand = db.query(Brand).filter(
        Brand.id == brand_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand non trovato")
    
    # Verifica tipo file
    allowed_types = ['pdf', 'docx', 'doc', 'pptx', 'ppt', 'txt', 'md']
    file_ext = file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo file non supportato. Formati accettati: {', '.join(allowed_types)}"
        )
    
    # Salva file
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / str(brand_id)
    file_path.mkdir(parents=True, exist_ok=True)
    full_path = file_path / unique_filename
    
    content = await file.read()
    with open(full_path, 'wb') as f:
        f.write(content)
    
    # Crea record DB
    document = BrandDocument(
        brand_id=brand_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_type=file_ext,
        file_size=len(content),
        file_path=str(full_path),
        description=description,
        uploaded_by_user_id=current_user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Processa in background
    background_tasks.add_task(process_document_task, document.id)
    
    return {
        "id": document.id,
        "filename": document.original_filename,
        "status": "uploaded",
        "message": "Documento caricato. Elaborazione in corso..."
    }


async def process_document_task(document_id: int):
    """Task background per processare documento"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        document = db.query(BrandDocument).filter(BrandDocument.id == document_id).first()
        if document:
            await rag_service.process_document(document, db)
    finally:
        db.close()


@router.get("/list/{brand_id}", response_model=List[DocumentOut])
async def list_documents(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista documenti di un brand"""
    
    # Verifica brand
    brand = db.query(Brand).filter(
        Brand.id == brand_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand non trovato")
    
    documents = db.query(BrandDocument).filter(
        BrandDocument.brand_id == brand_id
    ).order_by(BrandDocument.uploaded_at.desc()).all()
    
    # Aggiungi count chunks
    result = []
    for doc in documents:
        chunks_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).count()
        
        doc_dict = {
            "id": doc.id,
            "filename": doc.filename,
            "original_filename": doc.original_filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "extraction_status": doc.extraction_status,
            "analysis_status": doc.analysis_status,
            "uploaded_at": doc.uploaded_at,
            "description": doc.description,
            "summary": doc.summary,
            "key_topics": doc.key_topics,
            "chunks_count": chunks_count
        }
        result.append(doc_dict)
    
    return result


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dettaglio documento"""
    
    document = db.query(BrandDocument).join(Brand).filter(
        BrandDocument.id == document_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    
    chunks_count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).count()
    
    return {
        "id": document.id,
        "original_filename": document.original_filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "extraction_status": document.extraction_status,
        "analysis_status": document.analysis_status,
        "uploaded_at": document.uploaded_at,
        "description": document.description,
        "summary": document.summary,
        "key_topics": document.key_topics,
        "chunks_count": chunks_count
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina documento"""
    
    document = db.query(BrandDocument).join(Brand).filter(
        BrandDocument.id == document_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    
    # Elimina file fisico
    try:
        os.remove(document.file_path)
    except:
        pass
    
    # Elimina da DB (cascade elimina anche chunks)
    db.delete(document)
    db.commit()
    
    return {"message": "Documento eliminato"}


@router.post("/search/{brand_id}")
async def search_documents(
    brand_id: int,
    query: SearchQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cerca nei documenti del brand (semantic search)"""
    
    # Verifica brand
    brand = db.query(Brand).filter(
        Brand.id == brand_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand non trovato")
    
    # Cerca
    results = rag_service.search_similar(db, brand_id, query.query, query.limit)
    
    return {
        "query": query.query,
        "results": results
    }


@router.post("/reprocess/{document_id}")
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Riprocessa un documento"""
    
    document = db.query(BrandDocument).join(Brand).filter(
        BrandDocument.id == document_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    
    # Reset status
    document.extraction_status = "pending"
    document.analysis_status = "pending"
    
    # Elimina vecchi chunks
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
    db.commit()
    
    # Riprocessa
    background_tasks.add_task(process_document_task, document_id)
    
    return {"message": "Riprocessamento avviato"}
