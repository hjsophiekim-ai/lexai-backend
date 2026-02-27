from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import Version, ReverseIndexEntry
from schemas import ReverseQueryRequest, ReverseQueryResponse, ReverseQueryHit

router = APIRouter(prefix="/reverse-query", tags=["reverse-query"])


@router.post("", response_model=ReverseQueryResponse)
def reverse_query(payload: ReverseQueryRequest, db: Session = Depends(get_db)):
    version = db.query(Version).filter(Version.id == payload.version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # 선택 범위 [start_offset, end_offset]와 겹치는 모든 reverse index 엔트리
    entries = (
        db.query(ReverseIndexEntry)
        .filter(
            ReverseIndexEntry.version_id == payload.version_id,
            ReverseIndexEntry.start_offset < payload.end_offset,
            ReverseIndexEntry.end_offset > payload.start_offset,
        )
        .order_by(ReverseIndexEntry.line_start)
        .all()
    )

    hits = [
        ReverseQueryHit(
            id=e.id,
            start_offset=e.start_offset,
            end_offset=e.end_offset,
            line_start=e.line_start,
            line_end=e.line_end,
            kind=e.kind,
            summary=e.summary,
            evidence=e.evidence,
        )
        for e in entries
    ]
    return ReverseQueryResponse(hits=hits)
