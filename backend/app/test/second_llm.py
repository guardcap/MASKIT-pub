import json
import sys
import ollama
import os

# 프롬프트 파일 경로
PROMPT_FILE = "second_prompt.txt"

# 프롬프트 파일 읽기
if not os.path.exists(PROMPT_FILE):
    print(f"[ERROR] 프롬프트 파일을 찾을 수 없습니다: {PROMPT_FILE}", file=sys.stderr)
    sys.exit(1)

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

# 실제 서비스에서 들어올 법한 일관된 내부 보고서 예시
INPUT_TEXT = """
[마케팅본부 주간 보고서]
작성자: 정지윤 대리 (1985년 7월 22일생, 서울 강남구 거주)
작성일: 2025-08-08

1. 이번 주 주요 일정
- 불교 신자 고객 대상 맞춤형 캠페인 ‘마음의 등불’ 진행 현황 보고.
- 지난 주 진행된 민주당 후원 행사와의 마케팅 제휴 효과 분석.
- ABC테크와의 ‘오로라’ 프로젝트 협업 건: 인공지능 기반 신규 광고 플랫폼.
  (출시 계획: 2026년 2분기, 현재 기밀 유지 계약(NDA) 하에 진행 중)

2. 인력 현황 및 특이사항
- 김영희 과장(청각장애 1급): 시청각장애인 커뮤니티 대상 홍보 영상 제작 책임.
- 신입사원 박성민: 동성애자임을 공개하고 성소수자 인권 캠페인 참여 의사 표명.

3. 위험 요인 및 대응 계획
- B사와의 미공개 계약 조건 관련 분쟁 조짐. 법무팀 검토 중이며, 소송 가능성 있음.
- 일부 캠페인 데이터베이스에서 고객 주소(서울시 강서구, 부산 해운대구)와 연락처 유출 가능성 발견 → 보안팀 즉시 점검 요청.

4. 기타
- 다음 주 회의에서는 고객 가족관계 기반 세분화 타겟팅 방안 논의 예정.
""".strip()


def call_llm(text: str, max_retries: int = 2) -> dict:
    """LLM을 호출해 JSON을 반환. 출력이 JSON이 아니면 제한적 재시도."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    options = {
        "temperature": 0,
        "top_p": 1,
        "repeat_penalty": 1.1,
        "num_ctx": 4096,
    }

    last_err = None
    for attempt in range(max_retries + 1):
        resp = ollama.chat(model="mistral", messages=messages, options=options)
        content = resp["message"]["content"].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            last_err = e
            # 재시도 시: "JSON만 출력"을 더 강하게 재요청
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
