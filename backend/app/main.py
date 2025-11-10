from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import uploads, process, ocr, analyzer, masking_pdf
from app.smtp.routes import auth as smtp_auth, users as smtp_users, policy_management, entity_management, vectordb_management
from app.smtp.database import connect_to_mongo, close_mongo_connection
from app.smtp.smtp_handler import start_smtp_server
from contextlib import asynccontextmanager
import asyncio
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    # 시작 시
    print("\n" + "="*60)
    print("🚀 Enterprise GuardCAP 서버 시작")
    print("="*60 + "\n")

    # MongoDB 연결
    await connect_to_mongo()
    print("[App] ✅ MongoDB 연결 완료\n")

    # SMTP 서버 시작
    smtp_task = asyncio.create_task(start_smtp_server())
    await asyncio.sleep(1)
    print("[App] ✅ SMTP 서버 시작 완료\n")

    yield

    # 종료 시
    print("\n[App] 종료 중...")
    smtp_task.cancel()
    try:
        await smtp_task
    except asyncio.CancelledError:
        pass
    await close_mongo_connection()
    print("[App] ✅ 종료 완료")

app = FastAPI(
    title="Enterprise GuardCAP",
    description="통합 DLP 및 메일 보안 솔루션",
    version="2.0.0",
    lifespan=lifespan
)

# CORS(교차 출처 리소스 공유) 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# uploads 폴더를 정적 파일로 서빙
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ===== Core DLP 라우터들 =====
app.include_router(uploads.router, prefix="/api/v1/files", tags=["Files"])
app.include_router(process.router, prefix="/api/v1/process", tags=["Process"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR"])
app.include_router(analyzer.router, prefix="/api/v1/analyzer", tags=["Analyzer"])
app.include_router(masking_pdf.router, prefix="/api/v1/process")

# ===== SMTP 라우터들 =====
app.include_router(smtp_auth.router, prefix="/api/v1/smtp", tags=["SMTP Auth"])
app.include_router(smtp_users.router, prefix="/api/v1/smtp", tags=["SMTP Users"])
app.include_router(policy_management.router, tags=["Policy Management"])
app.include_router(entity_management.router, tags=["Entity Management"])
app.include_router(vectordb_management.router, tags=["VectorDB Management"])

# RAG 라우터는 추후 추가 가능
# from app.rag import rag_router
# app.include_router(rag_router.router, prefix="/api/v1/rag", tags=["RAG"])

@app.get("/")
def read_root():
    return {
        "message": "Enterprise GuardCAP API",
        "version": "2.0.0",
        "services": {
            "dlp": "/api/v1/process",
            "ocr": "/api/v1/ocr",
            "analyzer": "/api/v1/analyzer",
            "smtp": "/api/v1/smtp",
            "files": "/api/v1/files"
        },
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Enterprise GuardCAP"}