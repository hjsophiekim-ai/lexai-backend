from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import Document, Version, VersionSegment, ReverseIndexEntry
from schemas import VersionCreate, VersionResponse, VersionListItem
from services.text_segmenter import segment_text

router = APIRouter(prefix="/versions", tags=["versions"])


@router.get("", response_model=list[VersionListItem])
def list_versions(db: Session = Depends(get_db)):
    """List all versions with document info (for demo selector)."""
    versions = db.query(Version).join(Document).order_by(Document.id, Version.created_at).all()
    return [
        VersionListItem(
            document_id=v.document_id,
            version_id=v.id,
            label=v.label,
            document_title=v.document.title if v.document else None,
        )
        for v in versions
    ]


@router.get("/{version_id}")
def get_version(version_id: int, db: Session = Depends(get_db)):
    """Get single version content (for viewer)."""
    version = db.query(Version).filter(Version.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"version_id": version.id, "document_id": version.document_id, "label": version.label, "content": version.content}


@router.post("", response_model=VersionResponse)
def create_version(payload: VersionCreate, db: Session = Depends(get_db)):
    if payload.document_id is not None:
        doc = db.query(Document).filter(Document.id == payload.document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
    else:
        doc = Document(title=payload.document_title or "Untitled")
        db.add(doc)
        db.flush()

    version = Version(
        document_id=doc.id,
        label=payload.version_label,
        content=payload.content,
    )
    db.add(version)
    db.flush()

    for line_start, line_end, start_offset, end_offset, content in segment_text(payload.content):
        seg = VersionSegment(
            version_id=version.id,
            line_start=line_start,
            line_end=line_end,
            start_offset=start_offset,
            end_offset=end_offset,
            content=content,
        )
        db.add(seg)

    db.commit()
    db.refresh(version)
    return VersionResponse(document_id=doc.id, version_id=version.id, label=version.label)


@router.get("/{version_id}/export")
def export_version(version_id: int, db: Session = Depends(get_db)):
    """Export version content + segments + reverse_index as JSON."""
    version = db.query(Version).filter(Version.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    segments = [{"line_start": s.line_start, "line_end": s.line_end, "start_offset": s.start_offset, "end_offset": s.end_offset, "content": s.content} for s in version.segments]
    entries = db.query(ReverseIndexEntry).filter(ReverseIndexEntry.version_id == version_id).order_by(ReverseIndexEntry.line_start).all()
    reverse_index = [{"start_offset": e.start_offset, "end_offset": e.end_offset, "line_start": e.line_start, "line_end": e.line_end, "kind": e.kind, "summary": e.summary, "evidence": e.evidence} for e in entries]
    return {
        "version_id": version.id,
        "document_id": version.document_id,
        "label": version.label,
        "content": version.content,
        "segments": segments,
        "reverse_index": reverse_index,
    }
