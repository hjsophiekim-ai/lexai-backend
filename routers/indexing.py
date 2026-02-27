from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import Document, Version
from schemas import IndexRequest, IndexResponse
from services.diff_indexer import compute_and_store_reverse_index

router = APIRouter(prefix="/index", tags=["index"])


@router.post("", response_model=IndexResponse)
def index_versions(payload: IndexRequest, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == payload.document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    base = db.query(Version).filter(Version.id == payload.base_version_id).first()
    target = db.query(Version).filter(Version.id == payload.target_version_id).first()
    if not base or not target:
        raise HTTPException(status_code=404, detail="Version not found")
    if base.document_id != payload.document_id or target.document_id != payload.document_id:
        raise HTTPException(status_code=400, detail="Versions must belong to the document")

    count = compute_and_store_reverse_index(
        db, payload.document_id, payload.base_version_id, payload.target_version_id
    )
    return IndexResponse(indexed_entries=count)
