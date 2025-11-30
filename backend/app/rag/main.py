import json
import os

# --------------------------------------------------------------------------
# 필요한 클래스 및 모듈 임포트
# --------------------------------------------------------------------------
# 기존 파이프라인 구성 요소
from scripts.hybrid.retriever import GuardcapRetriever
from scripts.decision.decision_engine import DecisionEngine

# LLM 기반 TaskProfile 생성을 위한 실제 모듈
# (사용자께서 제공해주신 테스트 코드 기반)
from scripts.llm_taskprofile import TaskProfileGenerator
from scripts.llm_client import LLMClient, Entity

# --------------------------------------------------------------------------
# Phase 1: LLM을 이용한 TaskProfile 생성 (실제 구현)
# --------------------------------------------------------------------------
def generate_task_profile_with_llm(
    sample_data: dict, 
    llm_client: LLMClient, 
    schema_path: str
) -> dict:
    """
    실제 LLM 클라이언트를 사용하여 문서 요약, 엔티티, 체크리스트로부터
    TaskProfile을 생성합니다.
    """
    print("1. 실제 LLM으로 TaskProfile 생성 중...")
    
    # TaskProfile 생성기 인스턴스화
    generator = TaskProfileGenerator(llm=llm_client, schema_path=schema_path)
    
    # 생성기 실행
    profile = generator.generate(
        checklist=sample_data["checklist"],
        entities=sample_data["entities"],
        doc_summary=sample_data["doc_summary"]
    )
    
    print(" -> LLM 기반 TaskProfile 생성 완료.")
    return profile

# --------------------------------------------------------------------------
# Phase 2: Retriever를 사용한 근거 검색 및 점수 집계 (기존 함수 유지)
# --------------------------------------------------------------------------
def retrieve_evidence_and_calculate_scores(retriever, query, filters):
    """검색기로 근거를 검색하고 B, C로부터 DANGER/SAFE 점수를 집계합니다."""
    print("\n3. 특화 검색기로 근거 검색 중...")
    
    a_results = retriever.search_A_cases(query, filters=filters, top_k=3)
    b_results = retriever.search_B_policies(query, top_k=5)
    c_results = retriever.search_C_laws(query, top_k=5)
    
    print(f" -> A(사례) {len(a_results)}건, B(규정) {len(b_results)}건, C(법률) {len(c_results)}건의 근거를 찾음.")

    total_danger_score = 0
    total_safe_score = 0
    evidence_for_log = a_results + b_results + c_results

    for res in b_results + c_results:
        total_danger_score += res.get('CRITICAL_score', {}).get('CRITICAL_지수', 0)
        total_safe_score += res.get('OPEN_score', {}).get('OPEN_지수', 0)
    
    print(f" -> DANGER 점수 총합: {total_danger_score:.2f}, SAFE 점수 총합: {total_safe_score:.2f}")

    return a_results, total_danger_score, total_safe_score, evidence_for_log

# --------------------------------------------------------------------------
# Phase 3: Main Pipeline
# --------------------------------------------------------------------------
def run_guardcap_pipeline(sample_data: dict, llm_client: LLMClient, schema_path: str, index_path: str):
    """사용자 요청 데이터에 대해 전체 RAG 파이프라인을 실행합니다."""
    
    # 1. LLM으로 사용자 요청을 구조화된 TaskProfile로 변환
    task_profile = generate_task_profile_with_llm(sample_data, llm_client, schema_path)
    
    # 2. TaskProfile 기반으로 검색 쿼리 및 필터 생성
    # TaskProfile에 expected_entities가 없으므로, 감지된 엔티티를 기반으로 쿼리 생성
    detected_entities = [entity.entity for entity in sample_data.get("entities", [])]
    query = f"{task_profile['purpose']} 상황에서 {list(set(detected_entities))} 처리 방법"
    filters = {
        "category": task_profile.get("category"),
        "channel": task_profile.get("channel")
    }
    print(f"\n2. 생성된 검색 쿼리: \"{query}\"")
    print(f"   - 적용될 필터: {filters}")

    # 3. Retriever 초기화 및 근거 검색, 점수 집계
    retriever = GuardcapRetriever(index_base_path=index_path)
    a_results, danger_score, safe_score, all_evidence = retrieve_evidence_and_calculate_scores(retriever, query, filters)

    # 4. 결정 엔진으로 최종 결정 도출
    print("\n4. 결정 엔진으로 최종 결정 도출 중...")
    engine = DecisionEngine()
    decision = engine.make_decision(
        danger_score=danger_score,
        safe_score=safe_score,
        a_case_results=a_results
    )

    # 5. 최종 결과 출력
    print("\n" + "="*60)
    print(" 최종 분석 결과 ".center(60, "="))
    print("="*60)
    print(f"■ 사용자 요청 (문서 요약): {sample_data['doc_summary']}")
    print(f"■ 태스크 프로필: {json.dumps(task_profile, ensure_ascii=False, indent=2)}")
    print("-" * 60)
    print(f"■ 최종 결정: ✨ {decision['decision']} ✨")
    print(f"■ 결정 사유: {decision['reason']}")
    print(f"■ 추천 행동: {json.dumps(decision.get('action'), ensure_ascii=False, indent=4)}")

    print("\n■ 주요 근거:")
    if not all_evidence:
        print("  - 발견된 근거 없음")
    for ev in all_evidence[:5]:
        print(f"  - [{ev['source']}] (Score: {ev['score']:.2f}) {ev['paraphrases']}...")
    print("="*60)

# --------------------------------------------------------------------------
# 실행
# --------------------------------------------------------------------------
if __name__ == '__main__':
    # --- 설정값 ---
    # 인덱스 파일들이 저장된 상대 경로
    INDEX_BASE_PATH = './data/staging'
    # TaskProfile JSON 스키마 파일 경로
    SCHEMA_PATH = './schemas/TaskProfile.schema.json'
    # 사용할 LLM 모델 이름 (Ollama 기준)
    LLM_MODEL = 'llama3' # 필요시 모델명을 수정하세요

    # --- 샘플 데이터 준비 (테스트 코드의 self.samples 활용) ---
    samples = [
        {
            "doc_summary": "2025년 하반기 신입사원 최종 합격자 명단 공지",
            "checklist": {"중요": True},
            "entities": [
                Entity(entity="NAME", score=0.99, word="김민지", start=105, end=108),
                Entity(entity="NAME", score=0.99, word="박준호", start=110, end=113)
            ]
        },
        {
            "doc_summary": "신입사원 홍길동의 부서 이동 및 관련 담당자 안내 공지",
            "checklist": {},
            "entities": [
                Entity(entity="NAME", score=0.99, word="홍길동", start=46, end=49),
                Entity(entity="EMAIL", score=0.99, word="hong.gildong@example.com", start=70, end=95)
            ]
        },
        {
            "doc_summary": "고객센터를 통해 개인정보(주민번호) 유출이 의심된다는 민원이 접수됨.",
            "checklist": {"긴급": True, "보안": True, "고객": True},
            "entities": [
                Entity(entity="PII", score=0.99, word="주민번호", start=15, end=19),
                Entity(entity="NAME", score=0.98, word="김철수", start=25, end=28)
            ]
        },
        {
            "doc_summary": "사내 기술 공유를 위한 AI 활용 세미나 개최 안내문 초안",
            "checklist": {"내부공유": True},
            "entities": [
                Entity(entity="ORGANIZATION", score=0.9, word="AI팀", start=30, end=33)
            ]
        },
        {
            "doc_summary": "SNS 경품 이벤트를 통해 신규 고객의 휴대폰 번호를 수집하려고 합니다.",
            "checklist": {"마케팅": True, "개인정보": True},
            "entities": [
                Entity(entity="PHONE_NUMBER", score=0.95, word="휴대폰 번호", start=23, end=29)
            ]
        },
        {
            "doc_summary": "전사 조직 개편에 따른 일부 팀 해체 및 통합 공지 (대외비)",
            "checklist": {"인사": True, "대외비": True},
            "entities": [
                Entity(entity="DEPARTMENT", score=0.99, word="알파팀", start=30, end=33),
                Entity(entity="DEPARTMENT", score=0.99, word="베타팀", start=35, end=38)
            ]
        },
        {
            "doc_summary": "고객 만족도 조사를 위한 이메일 발송 및 참여자 대상 기프티콘 증정 안내",
            "checklist": {"고객": True, "마케팅": True},
            "entities": [
                Entity(entity="EMAIL", score=0.98, word="이메일", start=16, end=19),
                Entity(entity="NAME", score=0.92, word="고객명", start=25, end=28)
            ]
        }
    ]

    # --- 파이프라인 실행 ---
    # 실제 LLM 클라이언트 초기화
    # 이 코드를 실행하기 전에 Ollama 서버가 실행 중이어야 합니다.
    llm_client = LLMClient(model=LLM_MODEL)
    
    # 테스트할 샘플 데이터를 선택하세요.
    # sample_to_run = samples[0] # 합격자 명단 공지
    for sample in samples:
        print(f"\n--- 파이프라인 시작: \"{sample['doc_summary']}\" ---")
        run_guardcap_pipeline(sample, llm_client, SCHEMA_PATH, INDEX_BASE_PATH)