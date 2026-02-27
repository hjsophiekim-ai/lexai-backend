from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    versions = relationship("Version", back_populates="document", order_by="Version.created_at")


class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    label = Column(String(64), nullable=False)  # v1, v2, ...
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="versions")
    segments = relationship("VersionSegment", back_populates="version", order_by="VersionSegment.line_start")
    reverse_index_entries = relationship("ReverseIndexEntry", back_populates="version", foreign_keys="ReverseIndexEntry.version_id")


class VersionSegment(Base):
    __tablename__ = "version_segments"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("versions.id"), nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    version = relationship("Version", back_populates="segments")


class ReverseIndexEntry(Base):
    __tablename__ = "reverse_index"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("versions.id"), nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    kind = Column(String(32), nullable=False)  # added, removed, changed, moved
    summary = Column(Text, nullable=False)  # reverse query 응답 텍스트
    evidence = Column(JSON, nullable=True)  # [{ "line_start", "line_end", "snippet" }, ...]

    version = relationship("Version", back_populates="reverse_index_entries")
