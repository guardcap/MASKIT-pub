from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.smtp.database import connect_to_mongo, close_mongo_connection
from app.smtp.routes import auth, users
from app.smtp.smtp_handler import start_smtp_server
from contextlib import asynccontextmanager
import os
import asyncio
import threading

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시: MongoDB 연결 및 SMTP 서버 시작
    print("\n" + "="*60)
    print("🚀 FastAPI 애플리케이션 시작")
    print("="*60 + "\n")

    # MongoDB 연결
    await connect_to_mongo()
    print("[FastAPI] ✅ MongoDB 연결 완료\n")

    # SMTP 서버를 백그라운드 태스크로 실행
    # (FastAPI의 메인 asyncio 루프와 동일한 루프에서 실행)
    smtp_task = asyncio.create_task(start_smtp_server())

    # SMTP 서버가 완전히 시작될 때까지 대기 (최대 5초)
    await asyncio.sleep(1)
    print("[FastAPI] ✅ SMTP 서버 시작 완료\n")

    yield

    # 종료 시
    print("\n[FastAPI] 종료 중...")
    smtp_task.cancel()
    try:
        await smtp_task
    except asyncio.CancelledError:
        pass
    await close_mongo_connection()
    print("[FastAPI] ✅ 종료 완료")

app = FastAPI(
    title="MASKIT API",
    description="MASKIT 이메일 DLP 시스템 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FE 정적 파일 제공 (회원가입, 로그인 페이지 등)
if os.path.exists("FE"):
    app.mount("/FE", StaticFiles(directory="FE"), name="fe")

# 라우터 등록
app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {
        "message": "MASKIT API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "register": "/FE/register.html",
            "login": "/FE/login.html",
            "api_docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)