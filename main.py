from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional

from db import init_db
from routers import versions, indexing, reverse_query

# 1) FastAPI 앱 생성
app = FastAPI(title="Reverse Query MVP API", version="0.1.0")

# 2) CORS 설정 (중요)
# - 배포(프론트): https://lexai.ai.kr
# - 로컬 개발: http://localhost:3000 등
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # ✅ 배포 프론트 도메인 (반드시 포함)
        "https://lexai.ai.kr",
        "https://www.lexai.ai.kr",
        # (선택) Render 기본 도메인에서도 테스트할 수 있게 허용
        # 필요 없으면 지워도 됨
        "https://lexai-backend-2.onrender.com",
        # ✅ 로컬 개발용
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # OPTIONS 포함
    allow_headers=["*"],
)

# 3) 라우터 등록
app.include_router(versions.router)
app.include_router(indexing.router)
app.include_router(reverse_query.router)

# 4) 시작 시 DB 초기화
@app.on_event("startup")
def startup():
    init_db()

# 5) 헬스 체크
@app.get("/health")
def health():
    return {"status": "ok"}

# 6) Admin CMS 모델
class AdminSection(BaseModel):
    title: str
    description: str

class AdminContent(BaseModel):
    heroTitle: Optional[str] = ""
    heroSubtitle: Optional[str] = ""
    ctaPrimary: Optional[str] = ""
    ctaSecondary: Optional[str] = ""
    sections: List[AdminSection] = []

# 메모리 저장소(서버 재시작 시 초기화)
_CONTENT_STORE: Dict[str, AdminContent] = {}

# 7) Admin CMS 조회
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

# 8) Admin CMS 저장
@app.put("/admin/content/{page}", response_model=AdminContent)
def put_admin_content(page: str, payload: AdminContent):
    """
    관리자 CMS용 콘텐츠 저장.
    메모리(dict)에만 저장하며, 서버 재시작 시 초기화된다.
    """
    _CONTENT_STORE[page] = payload
    return payload