from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional

from db import init_db
from routers import versions, indexing, reverse_query

app = FastAPI(title="Reverse Query MVP API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(versions.router)
app.include_router(indexing.router)
app.include_router(reverse_query.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


class AdminSection(BaseModel):
    title: str
    description: str


class AdminContent(BaseModel):
    heroTitle: Optional[str] = ""
    heroSubtitle: Optional[str] = ""
    ctaPrimary: Optional[str] = ""
    ctaSecondary: Optional[str] = ""
    sections: List[AdminSection] = []


_CONTENT_STORE: Dict[str, AdminContent] = {}


@app.get("/admin/content/{page}", response_model=AdminContent)
def get_admin_content(page: str):
    """
    관리자 CMS용 콘텐츠 조회.
    콘텐츠가 없으면 404를 반환하고, 프론트는 기본값(fallback)을 사용한다.
    """
    content = _CONTENT_STORE.get(page)
    if not content:
        raise HTTPException(status_code=404, detail="No content for this page")
    return content


@app.put("/admin/content/{page}", response_model=AdminContent)
def put_admin_content(page: str, payload: AdminContent):
    """
    관리자 CMS용 콘텐츠 저장.
    메모리(dict)에만 저장하며, 서버 재시작 시 초기화된다.
    """
    _CONTENT_STORE[page] = payload
    return payload

