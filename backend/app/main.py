from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import uploads, process, ocr, analyzer, masking_pdf
from app.smtp.routes import auth as smtp_auth, users as smtp_users
from app.smtp.database import connect_to_mongo, close_mongo_connection
import os

app = FastAPI(
    title="Enterprise GuardCAP",
    description="통합 DLP 및 메일 보안 솔루션",
    version="2.0.0"
)

# CORS(교차 출처 리소스 공유) 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 앱 생명주기 이벤트 =====
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 MongoDB 연결"""
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 MongoDB 연결 해제"""
    await close_mongo_connection()

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