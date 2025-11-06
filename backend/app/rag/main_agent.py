"""
새로운 Agentic RAG 파이프라인 메인 실행 파일
LangGraph 기반 워크플로우 테스트
"""
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.retrievers import HybridRetriever
from agent.graph import run_masking_pipeline


def main():
    """메인 실행 함수"""

    # 설정
    INDEX_BASE_PATH = './data/staging'
    # 환경 변수에서 LLM 모델 가져오기 (기본값: llama3)
    LLM_MODEL = os.getenv('LLM_MODEL', 'llama3')

    print("\n🚀 Guardcap Agentic RAG 파이프라인 초기화 중...")
    print(f"   🤖 사용할 LLM 모델: {LLM_MODEL}\n")

    # Retriever 초기화
    retriever = HybridRetriever(index_base_path=INDEX_BASE_PATH)

    # 테스트 샘플 이메일
    test_emails = [
        {
            "name": "고객 문의 회신",
            "email": """안녕하세요, 김철수 고객님.

문의하신 견적서를 첨부하여 보내드립니다.
추가 문의사항이 있으시면 언제든지 연락 주세요.

담당자: 이영희
연락처: 02-1234-5678
이메일: yhlee@company.com"""
        },
        {
            "name": "마케팅 이메일 (위험)",
            "email": """[프로모션] 신규 고객 특별 할인!

안녕하세요, 박민지 고객님.
특별한 혜택을 준비했습니다.

연락처: 010-9876-5432
이메일: minji.park@email.com

지금 바로 확인하세요!"""
        },
        {
            "name": "민감정보 포함 (차단 예상)",
            "email": """인사팀 공지

신입사원 홍길동님의 정보입니다.
주민등록번호: 901225-1234567
이메일: gdhong@company.com

입사 서류 확인 바랍니다."""
        },
        {
            "name": "사내 부서 이동 공지",
            "email": """전 직원 공지

다음과 같이 인사 발령을 공지합니다.

- 홍길동 사원: 영업팀 → 마케팅팀 이동
- 발령일: 2025년 1월 1일

감사합니다."""
        },
        {
            "name": "협력사 프로젝트 정보 공유",
            "email": """외부 협력사 담당자님께,

프로젝트 관련하여 내부 담당자 정보를 공유드립니다.

담당자: 김민수 대리
연락처: 010-1111-2222
이메일: mskim@company.com

협조 부탁드립니다."""
        }
    ]

    # 각 테스트 케이스 실행
    for i, test_case in enumerate(test_emails, 1):
        print(f"\n\n{'=' * 80}")
        print(f" 테스트 케이스 {i}: {test_case['name']} ".center(80, "="))
        print(f"{'=' * 80}\n")

        try:
            result = run_masking_pipeline(
                email=test_case['email'],
                retriever=retriever,
                llm_model=LLM_MODEL
            )

            # 결과 저장 (옵션)
            # import json
            # with open(f'./results/test_{i}_result.json', 'w', encoding='utf-8') as f:
            #     json.dump(result, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"\n❌ 테스트 케이스 {i} 실행 실패: {e}")
            import traceback
            traceback.print_exc()

        # 다음 테스트로 넘어가기 전 잠시 대기
        input("\nEnter를 눌러 다음 테스트로 진행...")

    print("\n\n🎉 모든 테스트 완료!")


if __name__ == '__main__':
    main()
