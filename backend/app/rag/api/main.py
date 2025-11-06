"""
FastAPI 서버 메인
이메일 마스킹 API 엔드포인트 제공
"""
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import (
    EmailMaskingRequest,
    EmailMaskingResponse,
    PIIDecision,
    HealthCheckResponse
)
from agent.retrievers import HybridRetriever
from agent.graph import run_masking_pipeline


# FastAPI 앱 생성
app = FastAPI(
    title="Guardcap Email Masking API",
    description="LangGraph 기반 AI 에이전트를 활용한 이메일 PII 자동 마스킹 API",
    version="2.0.0"
)

# CORS 설정 (프론트엔드 연동을 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 Retriever 인스턴스 (앱 시작 시 초기화)
retriever = None


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 Retriever 초기화"""
    global retriever
    print("\n🚀 FastAPI 서버 시작 중...")
    print("📚 Retriever 초기화 중...")

    INDEX_BASE_PATH = os.getenv("INDEX_BASE_PATH", "./data/staging")

    try:
        retriever = HybridRetriever(index_base_path=INDEX_BASE_PATH)
        print("✅ Retriever 초기화 완료\n")
    except Exception as e:
        print(f"❌ Retriever 초기화 실패: {e}")
        print("⚠️  API는 시작되지만, 마스킹 기능이 제한될 수 있습니다.\n")


@app.get("/", response_model=dict)
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Guardcap Email Masking API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """헬스체크 엔드포인트"""
    llm_available = True
    try:
        # LLM factory를 통한 연결 확인
        from agent.llm_factory import get_llm
        # 환경변수나 기본 모델로 체크
        default_model = os.getenv("LLM_MODEL", "llama3")
        test_llm = get_llm(model=default_model, temperature=0.0)
        # 실제 호출은 비용이 크므로 객체 생성만 확인
    except Exception:
        llm_available = False

    return HealthCheckResponse(
        status="healthy" if retriever and llm_available else "degraded",
        retriever_initialized=retriever is not None,
        llm_available=llm_available
    )


@app.post("/mask-email", response_model=EmailMaskingResponse)
async def mask_email(request: EmailMaskingRequest):
    """
    이메일 마스킹 엔드포인트

    Args:
        request: 이메일 마스킹 요청 (email, llm_model)

    Returns:
        EmailMaskingResponse: 마스킹된 이메일 및 결정 정보
    """
    if not retriever:
        raise HTTPException(
            status_code=503,
            detail="Retriever가 초기화되지 않았습니다. 서버를 재시작해주세요."
        )

    try:
        print(f"\n📨 새로운 마스킹 요청 수신 (길이: {len(request.email)} 문자)")

        # 파이프라인 실행
        result = run_masking_pipeline(
            email=request.email,
            retriever=retriever,
            llm_model=request.llm_model
        )

        # 응답 생성
        response = EmailMaskingResponse(
            original_email=result['original_email'],
            masked_email=result['masked_email'],
            risk_level=result['risk_level'],
            should_block=result['should_block'],
            detected_piis_count=result['detected_piis_count'],
            masking_decisions=[
                PIIDecision(
                    pii_type=d['pii_type'],
                    pii_value=d['pii_value'],
                    action=d['action'],
                    reasoning=d['reasoning'],
                    confidence=d['confidence']
                )
                for d in result['masking_decisions']
            ],
            retrieved_guides_count=result['retrieved_guides_count'],
            retrieved_laws_count=result['retrieved_laws_count'],
            warnings=result.get('warnings', [])
        )

        print(f"✅ 마스킹 완료 (위험도: {response.risk_level})")

        return response

    except Exception as e:
        print(f"❌ 마스킹 처리 중 오류: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"마스킹 처리 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/guides/search")
async def search_guides(query: str, top_k: int = 3):
    """
    애플리케이션 가이드 검색 엔드포인트 (디버깅용)
    """
    if not retriever:
        raise HTTPException(status_code=503, detail="Retriever not initialized")

    try:
        results = retriever.search_application_guides(query=query, top_k=top_k)
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # 서버 실행
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 개발 모드: 코드 변경 시 자동 재시작
        log_level="info"
    )
