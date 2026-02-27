"""
Demo DB seed: 문서 1개, v1/v2 버전 업로드 후 index 생성.
실행: server 루트에서
  python -m seeds.seed_demo
또는
  PYTHONPATH=. python seeds/seed_demo.py
"""
import os
import sys

# server 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from db import engine, SessionLocal, init_db
from models import Document, Version, VersionSegment, ReverseIndexEntry
from services.text_segmenter import segment_text
from services.diff_indexer import compute_and_store_reverse_index


SEED_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    init_db()
    db = SessionLocal()
    try:
        # 기존 demo 문서 정리 (선택)
        for doc in db.query(Document).filter(Document.title == "Demo Document").all():
            db.delete(doc)
        db.commit()

        with open(os.path.join(SEED_DIR, "demo_v1.txt"), "r", encoding="utf-8") as f:
            v1_content = f.read()
        with open(os.path.join(SEED_DIR, "demo_v2.txt"), "r", encoding="utf-8") as f:
            v2_content = f.read()

        doc = Document(title="Demo Document")
        db.add(doc)
        db.flush()

        v1 = Version(document_id=doc.id, label="v1", content=v1_content)
        db.add(v1)
        db.flush()
        for line_start, line_end, start_offset, end_offset, content in segment_text(v1_content):
            db.add(VersionSegment(version_id=v1.id, line_start=line_start, line_end=line_end,
                                  start_offset=start_offset, end_offset=end_offset, content=content))

        v2 = Version(document_id=doc.id, label="v2", content=v2_content)
        db.add(v2)
        db.flush()
        for line_start, line_end, start_offset, end_offset, content in segment_text(v2_content):
            db.add(VersionSegment(version_id=v2.id, line_start=line_start, line_end=line_end,
                                  start_offset=start_offset, end_offset=end_offset, content=content))

        db.commit()
        db.refresh(doc)
        db.refresh(v1)
        db.refresh(v2)

        # v1 -> v2 기준 reverse index 생성
        count = compute_and_store_reverse_index(db, doc.id, v1.id, v2.id)
        print(f"Document id={doc.id}, Version v1 id={v1.id}, v2 id={v2.id}. Indexed {count} entries.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
