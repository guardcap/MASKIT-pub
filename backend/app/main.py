from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ✅ 버퍼링 비활성화 (로그 즉시 출력)
os.environ['PYTHONUNBUFFERED'] = '1'

# .env 파일 로드 (프로젝트 루트에서)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
print(f"[ENV] .env 파일 로드: {env_path}", flush=True)
print(f"[ENV] MONGODB_URI 확인: {os.getenv('MONGODB_URI', 'NOT_FOUND')[:50]}...", flush=True)

# Windows 한글/이모지 출력 설정 + 라인 버퍼링
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

# DLP 라우터
from app.routers import uploads, process, ocr, analyzer, masking_pdf
from app.routers import emails as email_routes


# Auth 및 User 관리
from app.auth import routes as auth_routes, users as user_routes

# Policy, Entity, VectorDB 관리
from app.policy import routes as policy_routes
from app.audit import routes as audit_routes
from app.entity import routes as entity_routes
from app.vectordb import routes as vectordb_routes

# Settings 관리
from app.api import settings as settings_routes

# SMTP 서버 및 라우터
from app.smtp_server.handler import start_smtp_server
from app.smtp_server import routes as smtp_routes

# Database
from app.database.mongodb import connect_to_mongo, close_mongo_connection

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
app.include_router(email_routes.router, tags=["Emails"])

# ===== Auth & User 라우터들 =====
app.include_router(auth_routes.router, prefix="/api", tags=["Auth"])
app.include_router(user_routes.router, prefix="/api", tags=["Users"])

# ===== Policy, Entity, VectorDB 라우터들 =====
app.include_router(policy_routes.router, tags=["Policy Management"])
app.include_router(entity_routes.router, tags=["Entity Management"])
app.include_router(vectordb_routes.router, tags=["VectorDB Management"])

# ===== Settings 라우터 =====
app.include_router(settings_routes.router, tags=["Settings"])

# ===== Audit 라우터 =====
app.include_router(audit_routes.router, tags=["Audit Logs"])

# ===== SMTP 메일 전송 라우터 =====
app.include_router(smtp_routes.router, prefix="/api/v1", tags=["SMTP Email"])

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