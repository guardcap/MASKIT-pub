# llm.py
import hashlib
from typing import Dict, Any, List, Optional
import os
import ollama
import re

llm_cache: Dict[str, Dict[str, Any]] = {}

BASE_DIR = os.path.dirname(__file__)
PROMPT_SELECT_PATH = os.path.join(BASE_DIR, "prompt_select.txt")
PROMPT_VALIDATE_PATH = os.path.join(BASE_DIR, "prompt_validate.txt")

with open(PROMPT_SELECT_PATH, "r", encoding="utf-8") as f:
    PROMPT_SELECT_TEMPLATE = f.read()

with open(PROMPT_VALIDATE_PATH, "r", encoding="utf-8") as f:
    PROMPT_VALIDATE_TEMPLATE = f.read()

# TODO: 나중에 엔티티 불러오기 함수로 대체
entity_dict = {
    "EMAIL_ADDRESS": "이메일 주소",
    "DOMAIN": "도메인 주소",
    "PHONE_NUMBER": "전화번호",
    "IP_ADDRESS": "IP 주소",
    "PERSON_NAME": "사람 이름",
    "ACCOUNT_NUMBER": "계좌번호"
}

def format_entity_candidates(candidate_types: List[str]) -> str:
    return ", ".join(f"{etype}: {entity_dict.get(etype, '설명 없음')}" for etype in candidate_types)

def format_single_candidate(candidate_type: str) -> str:
    return f"{candidate_type}: {entity_dict.get(candidate_type, '설명 없음')}"

class OlamaLLMClient:
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name

    def call_llm(self, prompt: str) -> str:
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"[OLAMA ERROR] {e}")
            return "[SELECTED_ENTITY: UNKNOWN]"

llm_client = OlamaLLMClient(model_name="llama3")

def generate_cache_key(
    text: str,
    sentence: str,
    mode: str,
    candidate_types: Optional[List[str]] = None,
    score: Optional[float] = None
) -> str:
    ct = ",".join(sorted(candidate_types or []))
    raw = f"{mode}|{text}|{sentence}|{ct}|{score}"
    return hashlib.sha256(raw.encode()).hexdigest()

def parse_llm_entity_output(output: str) -> str:
    match = re.search(r'\[SELECTED_ENTITY:\s*([A-Z0-9_]+)\s*\]', output)
    return match.group(1) if match else "UNKNOWN"

def llm_check(
    text: str,
    sentence: str,
    candidate_entities: Optional[List[Dict[str, Any]]],
    score: Optional[float] = None
) -> Dict[str, Any]:
    """
    동작 규칙
    1) candidate_entities 가 있고 요소가 2개 이상 → 다중 선택 프롬프트로 LLM 호출
    2) candidate_entities 가 있고 요소가 1개
       - score 가 None 아님 → 단일 후보 '검증' 프롬프트로 LLM 호출
       - score 가 None → LLM 호출 없이 해당 엔티티 선택
    3) candidate_entities 가 없거나 빈 리스트 → UNKNOWN
    """
    candidate_entities = candidate_entities or []
    candidate_types = list({e.get("type") for e in candidate_entities if e.get("type")})
    num_candidates = len(candidate_types)

    # --- 케이스 분기 ---
    if num_candidates >= 2:
        mode = "select"
        cache_key = generate_cache_key(text, sentence, mode, candidate_types=candidate_types)
        if cache_key in llm_cache:
            print(f"[Cache HIT(select)] '{text}' → {llm_cache[cache_key]['selected_entity']}")
            return llm_cache[cache_key]

        # 다중 선택 프롬프트
        entity_candidates_str = format_entity_candidates(candidate_types)
        prompt = PROMPT_SELECT_TEMPLATE.format(
            text=text,
            sentence=sentence,
            entity_candidates=entity_candidates_str
        )

        print(f"[LLM CALL(select)] Prompt:\n{prompt}")
        raw_result = llm_client.call_llm(prompt)
        selected_entity = parse_llm_entity_output(raw_result)

    elif num_candidates == 1:
        only_type = candidate_types[0]
        if score is not None:
            mode = "validate"
            cache_key = generate_cache_key(
                text, sentence, mode, candidate_types=[only_type], score=score
            )
            if cache_key in llm_cache:
                print(f"[Cache HIT(validate)] '{text}' → {llm_cache[cache_key]['selected_entity']}")
                return llm_cache[cache_key]

            # 단일 후보 검증 프롬프트
            candidate_desc = format_single_candidate(only_type)
            prompt = PROMPT_VALIDATE_TEMPLATE.format(
                text=text,
                sentence=sentence,
                candidate=candidate_desc,
                score=score
            )

            print(f"[LLM CALL(validate)] Prompt:\n{prompt}")
            raw_result = llm_client.call_llm(prompt)
            selected_entity = parse_llm_entity_output(raw_result)
        else:
            # 점수 없고 후보 1개 → 그대로 채택 (LLM 미호출)
            selected_entity = only_type
            mode = "passthrough"
            cache_key = generate_cache_key(
                text, sentence, mode, candidate_types=[only_type], score=None
            )
            print(f"[PASSTHROUGH] '{text}' → selected: {selected_entity}")
            llm_cache[cache_key] = {
                "selected_entity": selected_entity,
                "candidate_types": candidate_types
            }
            return llm_cache[cache_key]

    else:
        # 후보 없음
        selected_entity = "UNKNOWN"
        cache_key = generate_cache_key(text, sentence, "no_candidate", candidate_types=[], score=score)

    # 공통 캐시 저장 및 반환
    llm_result = {
        "selected_entity": selected_entity,
        "candidate_types": candidate_types
    }
    llm_cache[cache_key] = llm_result
    print(f"[LLM RESULT] '{text}' → selected: {selected_entity}")
    return llm_result

"""테스트 코드로 넣었던 부분

def main():
    간단한 통합 테스트:
    - 케이스 A: 후보 2개(선택 프롬프트 호출)
    - 케이스 B: 후보 1개 + score 있음(검증 프롬프트 호출)
    - 케이스 C: 후보 1개 + score 없음(LLM 미호출, 그대로 채택)
    - 케이스 D: 후보 없음(UNKNOWN)
    - 케이스 E: 후보 2개 + score 있음(여전히 '선택' 프롬프트 호출)
    test_cases = [
        # A) multi-candidate selection
        {
            "text": "support@example.com",
            "sentence": "문의는 support@example.com 으로 주세요.",
            "candidate_entities": [{"type": "EMAIL_ADDRESS"}, {"type": "DOMAIN"}],
            "score": None,
            "label": "A: multi-candidate(select)"
        },
        # B) single-candidate validation (with score)
        {
            "text": "example.com",
            "sentence": "도메인은 example.com 입니다.",
            "candidate_entities": [{"type": "DOMAIN"}],
            "score": 0.72,
            "label": "B: single-candidate(validate)"
        },
        # C) single-candidate passthrough (no score)
        {
            "text": "010-1234-5678",
            "sentence": "연락처는 010-1234-5678 로 등록되어 있습니다.",
            "candidate_entities": [{"type": "PHONE_NUMBER"}],
            "score": None,
            "label": "C: single-candidate(passthrough)"
        },
        # D) no candidate
        {
            "text": "foobar",
            "sentence": "그냥 단어 foobar 입니다.",
            "candidate_entities": None,
            "score": None,
            "label": "D: no-candidate(UNKNOWN)"
        },
        # E) multi-candidate with score (still selection mode)
        {
            "text": "192.168.0.1",
            "sentence": "서버 내부 IP는 192.168.0.1 입니다.",
            "candidate_entities": [{"type": "IP_ADDRESS"}, {"type": "DOMAIN"}],
            "score": 0.85,
            "label": "E: multi-candidate(select, score given)"
        },
    ]

    print("\n=== LLM Check Demo ===")
    for case in test_cases:
        print(f"\n--- {case['label']} ---")
        result = llm_check(
            text=case["text"],
            sentence=case["sentence"],
            candidate_entities=case["candidate_entities"],
            score=case["score"],
        )
        print(
            f"Input: '{case['text']}' | Selected: {result['selected_entity']} "
            f"| Candidates: {result['candidate_types']}"
        )


if __name__ == "__main__":
    main()

"""