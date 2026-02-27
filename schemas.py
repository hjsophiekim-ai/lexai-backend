from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ----- Versions -----
class VersionCreate(BaseModel):
    document_title: Optional[str] = None
    document_id: Optional[int] = None
    version_label: str
    content: str


class VersionResponse(BaseModel):
    document_id: int
    version_id: int
    label: str

    class Config:
        from_attributes = True


class VersionListItem(BaseModel):
    document_id: int
    version_id: int
    label: str
    document_title: Optional[str] = None


# ----- Index -----
class IndexRequest(BaseModel):
    document_id: int
    base_version_id: int
    target_version_id: int


class IndexResponse(BaseModel):
    indexed_entries: int


# ----- Reverse Query -----
class ReverseQueryRequest(BaseModel):
    version_id: int
    start_offset: int
    end_offset: int


class EvidenceItem(BaseModel):
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    snippet: Optional[str] = None


class ReverseQueryHit(BaseModel):
    id: int
    start_offset: int
    end_offset: int
    line_start: int
    line_end: int
    kind: str
    summary: str
    evidence: Optional[List[Any]] = None


class ReverseQueryResponse(BaseModel):
    hits: List[ReverseQueryHit]
