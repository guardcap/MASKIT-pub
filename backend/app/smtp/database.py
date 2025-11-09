from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient, ASCENDING
import os

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://maskit:basakbasak@cluster0.bpbrvcu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "maskit")

# 비동기 클라이언트 (FastAPI 라우터용)
async_client = None
async_db = None

# 동기 클라이언트 (SMTP 핸들러용)
sync_client = None
sync_db = None

async def connect_to_mongo():
    global async_client, async_db, sync_client, sync_db

    # 비동기 클라이언트
    async_client = AsyncIOMotorClient(MONGODB_URI)
    async_db = async_client[DATABASE_NAME]

    # 인덱스 생성
    await async_db.users.create_index([("email", ASCENDING)], unique=True)
    await async_db.emails.create_index([("created_at", ASCENDING)])
    await async_db.policies.create_index([("policy_id", ASCENDING)], unique=True)
    await async_db.policies.create_index([("created_at", ASCENDING)])
    await async_db.policies.create_index([("authority", ASCENDING)])
    await async_db.entities.create_index([("entity_id", ASCENDING)], unique=True)
    await async_db.entities.create_index([("category", ASCENDING)])
    await async_db.entities.create_index([("is_active", ASCENDING)])

    # 동기 클라이언트 (SMTP용)
    sync_client = MongoClient(MONGODB_URI)
    sync_db = sync_client[DATABASE_NAME]

    print(f"✅ MongoDB 연결 완료: {DATABASE_NAME}")

async def close_mongo_connection():
    global async_client, sync_client
    if async_client:
        async_client.close()
    if sync_client:
        sync_client.close()
    print("❌ MongoDB 연결 종료")

def get_database():
    """FastAPI 라우터용 비동기 DB (async/await 사용)"""
    return async_db

def get_db():
    """FastAPI Dependency용 - async_db 반환"""
    return async_db

def get_sync_database():
    """SMTP 핸들러용 동기 DB (동기 방식)"""
    return sync_db