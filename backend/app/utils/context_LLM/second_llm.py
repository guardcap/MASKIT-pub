import json
import sys
import ollama
import os
import io

PROMPT_FILE = "second_prompt.txt"

if not os.path.exists(PROMPT_FILE):
    print(f"[ERROR] 프롬프트 파일을 찾을 수 없습니다: {PROMPT_FILE}", file=sys.stderr)
    sys.exit(1)

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

INPUT_TEXT = """
[재무팀 기밀 보고서]
작성자: 박지현 차장 (1988년 6월 1일생, 인천 남동구 거주, 이메일: jihyun.park@financecorp.com)
작성일: 2025-08-16

1. 주요 재무 현황
- 내부 계좌번호 123-456-789012 (하나은행)로 외부 투자금 유입 확인.
- 고객 상담 기록에서 010-9876-5432 번호와 함께 서울시 강남구 주소 수집됨.
- 내부 서버 접근 기록 중 IP 192.168.1.45에서 비정상 접속 시도 탐지.

2. 전략적 프로젝트
- 비공개 M&A 프로젝트 ‘네뷸라’ 진행 상황 보고.
  (계약 조항: 2025년 12월까지 독점 협상, NDA 체결 완료)
- 신규 블록체인 기반 결제 시스템 개발 로드맵 초안 공유.

3. 법적/규제 리스크
- 금융감독원으로부터 미신고 투자상품 판매 관련 조사 착수.
- 외부 컨설팅사와의 용역 계약 해지 건 소송 가능성 있음.

4. 기타
- 임직원 배우자 및 자녀 복리후생 프로그램 개선안 논의 예정.
- 최근 인사이동으로 인해 팀원 간 업무 재조정 필요.
- 차기 회의 일정: 2025년 8월 20일 오후 3시, 본사 5층 대회의실
- 비상 연락망 업데이트: 김민수(010-1234-5678), 이영희(010-2345-6789)
- 보안 교육 일정: 2025년 9월 1일, 온라인 세미나 (링크: https://financecorp.com/security-training)
- 최근 고객 불만 사항: 2025년 8월 15일, 김철수(010-3456-7890) 고객이 서비스 지연으로 불만 제기
- 내부 감사 결과: 2025년 8월 10일, 재무팀의 비용 처리 과정에서 일부 부적절한 지출 발견 (총액: 500,000원)
- 신규 프로젝트 제안: 2025년 8월 18일, AI 기반 고객 분석 시스템 개발 제안 (예산: 2억 원)
- 최근 보안 사고: 2025년 8월 14일, 내부 시스템 해킹 시도
""".strip()


def call_llm(text: str, max_retries: int = 2) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    options = {"temperature": 0, "top_p": 1, "repeat_penalty": 1.1, "num_ctx": 4096}

    last_err = None
    for attempt in range(max_retries + 1):
        resp = ollama.chat(model="llama3", messages=messages, options=options)
        content = resp["message"]["content"].strip()

        try:
            # json.load() 사용 (io.StringIO로 문자열 감쌈)
            return json.load(io.StringIO(content))
        except json.JSONDecodeError as e:
            last_err = e
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "JSON만 출력하세요. 다음 텍스트:\n" + text},
            ]
    raise ValueError(f"LLM 응답을 JSON으로 파싱하지 못했습니다: {last_err}")


def pretty_print(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> int:
    try:
        result = call_llm(INPUT_TEXT)
    except Exception as e:
        print(f"[ERROR] LLM 호출/파싱 실패: {e}", file=sys.stderr)
        return 1

    print("\n📊 민감 정보 탐지 결과(JSON):")
    pretty_print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
