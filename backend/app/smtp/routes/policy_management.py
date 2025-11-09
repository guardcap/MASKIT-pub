"""
정책 관리 라우터
- 정책 추가/수정/삭제
- 멀티모달 파일 업로드 (PDF, 이미지)
- 임베딩 생성 및 VectorDB 저장
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
import hashlib
import fitz  # PyMuPDF
from dotenv import load_dotenv

# OpenAI imports
try:
    from openai import AsyncOpenAI
    from pyzerox import zerox
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Database imports
from ..database import get_db
from ..models import PolicyDocument, PolicyMetadata, PolicyResponse

# Background tasks
from .background_tasks import process_policy_background, get_task_status, clear_old_tasks
from fastapi import BackgroundTasks

load_dotenv()

router = APIRouter(prefix="/api/policies", tags=["Policy Management"])

# 설정
UPLOAD_DIR = Path("backend/app/uploads/policies")
TEMP_DIR = Path("backend/app/uploads/temp")
PROCESSED_DIR = Path("backend/app/uploads/processed")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI 클라이언트 초기화
if OPENAI_AVAILABLE:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai_client = AsyncOpenAI(api_key=openai_api_key)
    else:
        openai_client = None
else:
    openai_client = None


class PolicyProcessor:
    """정책 문서 처리 클래스"""

    def __init__(self):
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.vision_model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")

    async def process_pdf(self, file_path: str) -> dict:
        """PDF 파일을 처리하여 텍스트 추출"""
        try:
            # PDF 정보 확인
            doc = fitz.open(file_path)
            page_count = len(doc)
            file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            doc.close()

            # 작은 PDF는 Zerox 사용 (OCR + Vision)
            if page_count <= 50 and file_size_mb <= 20:
                if OPENAI_AVAILABLE and openai_client:
                    try:
                        result = await zerox(
                            file_path=file_path,
                            model=self.vision_model,
                            output_dir=str(TEMP_DIR),
                            cleanup=True,
                        )
                        markdown = result.get("content", "") if isinstance(result, dict) else str(result)
                        return {"text": markdown, "method": "zerox_ocr"}
                    except Exception as e:
                        print(f"Zerox failed: {e}, falling back to PyMuPDF")

            # Fallback: PyMuPDF로 텍스트 추출
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()

            return {"text": text, "method": "pymupdf"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF 처리 실패: {str(e)}")

    async def process_image(self, file_path: str) -> dict:
        """이미지 파일을 OCR 처리"""
        if not OPENAI_AVAILABLE or not openai_client:
            raise HTTPException(status_code=400, detail="OpenAI API가 설정되지 않았습니다")

        try:
            # Vision API로 이미지 분석
            with open(file_path, "rb") as image_file:
                import base64
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            response = await openai_client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "이미지에서 모든 텍스트를 추출하고 정책 내용을 구조화하여 마크다운으로 작성해주세요."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )

            text = response.choices[0].message.content
            return {"text": text, "method": "vision_api"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"이미지 처리 실패: {str(e)}")

    async def extract_policy_metadata(self, text: str, title: str, authority: str) -> dict:
        """정책 텍스트에서 메타데이터 추출"""
        if not OPENAI_AVAILABLE or not openai_client:
            # OpenAI 없이 기본 메타데이터만 반환
            return {
                "title": title,
                "authority": authority,
                "summary": text[:500],
                "keywords": [],
                "entity_types": []
            }

        prompt = f"""
다음 정책 문서에서 메타데이터를 추출하세요.

정책 제목: {title}
발행 기관: {authority}

문서 내용:
{text[:4000]}

다음 JSON 형식으로 반환하세요:
{{
    "summary": "정책 요약 (200자 이내)",
    "keywords": ["키워드1", "키워드2", ...],
    "entity_types": ["개인정보 유형1", "개인정보 유형2", ...],
    "scenarios": ["적용 시나리오1", "적용 시나리오2", ...],
    "directives": ["실행 지침1", "실행 지침2", ...]
}}

반드시 유효한 JSON만 반환하세요.
"""

        try:
            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()
            # JSON 추출
            import re
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

            metadata = json.loads(content)
            metadata["title"] = title
            metadata["authority"] = authority

            return metadata

        except Exception as e:
            print(f"메타데이터 추출 실패: {e}")
            return {
                "title": title,
                "authority": authority,
                "summary": text[:500],
                "keywords": [],
                "entity_types": []
            }


# 현재 사용자 확인 (정책 관리자 권한)
async def get_current_policy_admin(db = Depends(get_db)):
    """정책 관리자 권한 확인"""
    # TODO: JWT 토큰 검증 로직 추가
    # 임시로 모든 요청 허용
    return None


@router.post("/upload")
async def upload_policy_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    authority: str = Form(default="내부"),
    description: str = Form(default=""),
    db = Depends(get_db),
    current_user = Depends(get_current_policy_admin)
):
    """
    정책 파일 업로드 (PDF, 이미지 등)
    멀티모달 처리 및 임베딩 생성
    """

    # 파일 확장자 확인
    file_ext = os.path.splitext(file.filename)[1].lower()
    supported_exts = ['.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff']

    if file_ext not in supported_exts:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(supported_exts)}"
        )

    # 파일 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    try:
        # 파일 저장
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 파일 처리
        processor = PolicyProcessor()

        if file_ext == '.pdf':
            result = await processor.process_pdf(str(file_path))
        else:
            result = await processor.process_image(str(file_path))

        extracted_text = result["text"]
        processing_method = result["method"]

        # 메타데이터 추출
        metadata_dict = await processor.extract_policy_metadata(
            extracted_text,
            title,
            authority
        )

        # PolicyMetadata 모델로 변환
        metadata = PolicyMetadata(**metadata_dict)

        # 정책 ID 생성
        policy_id = hashlib.md5(f"{title}_{timestamp}".encode()).hexdigest()[:12]

        # PolicyDocument 모델 생성
        policy_doc = PolicyDocument(
            policy_id=policy_id,
            title=title,
            authority=authority,
            description=description,
            original_filename=file.filename,
            saved_filename=safe_filename,
            file_type=file_ext,
            file_size_mb=len(content) / (1024 * 1024),
            processing_method=processing_method,
            extracted_text=extracted_text,
            metadata=metadata,
            created_by=None  # TODO: 현재 사용자 이메일
        )

        # MongoDB에 저장
        await db["policies"].insert_one(policy_doc.model_dump(mode='json'))

        # 백업용으로 파일에도 저장
        processed_file = PROCESSED_DIR / f"policy_{policy_id}.json"
        with open(processed_file, "w", encoding="utf-8") as f:
            json.dump(policy_doc.model_dump(mode='json'), f, ensure_ascii=False, indent=2)

        # 백그라운드에서 가이드라인 추출 및 VectorDB 임베딩 실행
        background_tasks.add_task(
            process_policy_background,
            policy_id,
            policy_doc.model_dump(mode='json'),
            db
        )

        return JSONResponse({
            "success": True,
            "message": "정책 파일이 성공적으로 업로드되었습니다. 백그라운드에서 가이드라인 추출 중입니다.",
            "data": {
                "policy_id": policy_id,
                "title": title,
                "authority": authority,
                "file_type": file_ext,
                "processing_method": processing_method,
                "metadata": metadata_dict,
                "text_length": len(extracted_text),
                "created_at": policy_doc.created_at.isoformat(),
                "task_id": f"policy_{policy_id}"
            }
        })

    except Exception as e:
        # 오류 발생 시 업로드된 파일 삭제
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류 발생: {str(e)}")


@router.get("/list")
async def list_policies(
    skip: int = 0,
    limit: int = 50,
    authority: str = None,
    db = Depends(get_db)
):
    """정책 목록 조회"""
    try:
        # 필터 조건
        query = {}
        if authority:
            query["authority"] = authority

        # 총 개수 조회
        total = await db["policies"].count_documents(query)

        # 정책 목록 조회 (전체 텍스트 제외)
        cursor = db["policies"].find(
            query,
            {
                "extracted_text": 0  # 전체 텍스트는 제외
            }
        ).sort("created_at", -1).skip(skip).limit(limit)

        policies = []
        async for doc in cursor:
            # _id를 문자열로 변환
            doc["_id"] = str(doc["_id"])
            policies.append(doc)

        return JSONResponse({
            "success": True,
            "data": {
                "policies": policies,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 목록 조회 실패: {str(e)}")


@router.get("/{policy_id}")
async def get_policy_detail(
    policy_id: str,
    db = Depends(get_db)
):
    """정책 상세 조회"""
    try:
        policy = await db["policies"].find_one({"policy_id": policy_id})

        if not policy:
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다")

        # _id를 문자열로 변환
        policy["_id"] = str(policy["_id"])

        return JSONResponse({
            "success": True,
            "data": policy
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 조회 실패: {str(e)}")


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: str,
    db = Depends(get_db),
    current_user = Depends(get_current_policy_admin)
):
    """정책 삭제"""
    try:
        # 정책 조회
        policy = await db["policies"].find_one({"policy_id": policy_id})

        if not policy:
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다")

        # 원본 파일 삭제
        original_file = UPLOAD_DIR / policy["saved_filename"]
        if original_file.exists():
            original_file.unlink()

        # 백업 파일 삭제
        backup_file = PROCESSED_DIR / f"policy_{policy_id}.json"
        if backup_file.exists():
            backup_file.unlink()

        # MongoDB에서 삭제
        await db["policies"].delete_one({"policy_id": policy_id})

        return JSONResponse({
            "success": True,
            "message": "정책이 성공적으로 삭제되었습니다"
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정책 삭제 실패: {str(e)}")


@router.get("/stats/summary")
async def get_policy_stats(db = Depends(get_db)):
    """정책 통계 조회"""
    try:
        # 총 정책 수
        total_policies = await db["policies"].count_documents({})

        # 기관별 집계
        authority_pipeline = [
            {"$group": {"_id": "$authority", "count": {"$sum": 1}}}
        ]
        authority_cursor = db["policies"].aggregate(authority_pipeline)
        authority_count = {}
        async for doc in authority_cursor:
            authority_count[doc["_id"]] = doc["count"]

        # 파일 타입별 집계
        file_type_pipeline = [
            {"$group": {"_id": "$file_type", "count": {"$sum": 1}}}
        ]
        file_type_cursor = db["policies"].aggregate(file_type_pipeline)
        file_type_count = {}
        async for doc in file_type_cursor:
            file_type_count[doc["_id"]] = doc["count"]

        return JSONResponse({
            "success": True,
            "data": {
                "total_policies": total_policies,
                "by_authority": authority_count,
                "by_file_type": file_type_count
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/tasks/{task_id}/status")
async def get_background_task_status(task_id: str):
    """백그라운드 작업 상태 조회"""
    # 오래된 작업 정리
    clear_old_tasks()

    status = get_task_status(task_id)

    if not status:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")

    return JSONResponse({
        "success": True,
        "data": status
    })
