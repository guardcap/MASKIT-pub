import json
import time
import uuid
from typing import Dict, Any, Optional
from .llm_client import LLMClient
from .schema_utils import load_schema, validate_schema
from jsonschema import ValidationError

TASKPROFILE_SCHEMA_PATH = "schemas/TaskProfile.schema.json"

SYSTEM_PROMPT = """
너는 Task→Context 추출기이다.
입력으로 '체크리스트', '엔티티 요약', '문서 요약'이 주어진다.
너의 임무는 다음 두 가지를 수행하는 것이다:

1. 먼저 '문서 원문'을 2~3문장으로 요약하여 'doc_summary' 필드를 생성한다.
2. doc_summary와 다른 입력을 참고하여 TaskProfile.schema.json에 정의된 모든 속성을 포함한 JSON을 만든다.

그리고 고려해야할 사항은 다음과 같다.

다음 필수 필드를 반드시 포함해야 한다:
1. category (필수): '사내' 또는 '사외' 중 선택
2. audience (필수): 'PUBLIC', 'CUSTOMER', 'EMPLOYEE', 'PARTNER' 중 하나만 선택
3. channel (필수): 'WEB', 'EMAIL', 'SNS', 'PRINT' 중 선택
4. purpose (필수): 'ANNOUNCEMENT', 'HR_MOVE', 'WINNER_NOTICE', 'PRESS_RELEASE', 'OTHER' 중 선택
5. legal_priority (필수): 'LAW_OVER_POLICY' 또는 'POLICY_OVER_LAW' 중 선택
6. task_type (필수): 사전에 정의된 라벨을 쓰지 말고, 문서 내용을 보고 사람이 직관적으로 이해할 수 있는 한국어 자연어 태스크명을 생성
7. task_id (필수): 최소 3자 이상의 문자열
8. schema_version (필수): 'v' 접두사가 붙은 문자열 (예: "v1.0")

그 외 규칙:
- confidence 필드는 반드시 0에서 1 사이의 숫자값으로 생성 (문자열이 아님)
- 선택적 속성은 가능하면 null 또는 default로 채움
- enum 값은 위 목록의 값과 정확히 일치해야 함

**Enum 가이드:**
- category: ['사내', '사외']
- audience: ['PUBLIC', 'CUSTOMER', 'EMPLOYEE', 'PARTNER']
- channel: ['WEB', 'EMAIL', 'SNS', 'PRINT']
- purpose: ['ANNOUNCEMENT','HR_MOVE','WINNER_NOTICE','PRESS_RELEASE','OTHER']
- legal_priority: ['LAW_OVER_POLICY','POLICY_OVER_LAW']

반드시 task_type 필드를 포함하라.
task_type은 반드시 사람이 이해할 수 있는 한국어 자연어 태스크명으로 생성하라.
출력은 JSON 객체 하나만, 다른 텍스트는 절대 포함하지 말 것
"""

MAX_ATTEMPTS = 3
RETRY_SLEEP = 0.6

class entity:
    pass

class TaskProfileGenerator:
    """
    LLM을 통해 TaskProfile JSON을 생성하고 스키마 검증까지 수행하는 클래스
    """
    def __init__(self, llm: Optional[LLMClient] = None, schema_path: str = TASKPROFILE_SCHEMA_PATH):
        self.llm = llm or LLMClient()
        self.schema = load_schema(schema_path)

    # checklist는 사이드바에서 선택한, entities는 엔티티 추출 결과, doc_summary는 메일 본문+OCR 추출 텍스트 
    def generate(self, checklist: Dict[str, Any], entities: list[entity], doc_summary: str) -> Dict[str, Any]:
        """
        LLM을 사용하여 TaskProfile 생성 후 스키마 검증 및 보강 수행
        """

        for attempt in range(1, MAX_ATTEMPTS + 1):
            raw = self.llm.chat(system=SYSTEM_PROMPT, checklist=checklist, entities=entities, doc_summary=doc_summary)
            cleaned = self._extract_json(raw)
            if cleaned is None:
                last_err = f"모델 출력에서 JSON을 찾을 수 없음 (시도 {attempt}). raw={raw[:400]}"
                time.sleep(RETRY_SLEEP)
                continue

            try:
                obj = json.loads(cleaned)
            except json.JSONDecodeError as e:
                last_err = f"JSON 디코딩 오류: {e} (시도 {attempt}). cleaned_start={cleaned[:200]}"
                time.sleep(RETRY_SLEEP)
                continue

            # TaskProfile 필드 정규화
            
            # 1. task_id 생성
            if "task_id" not in obj or not obj.get("task_id"):
                obj["task_id"] = f"task-{uuid.uuid4().hex[:8]}"
            
            # 2. schema_version 문자열 변환
            if "schema_version" not in obj:
                obj["schema_version"] = "v1.0"
            elif isinstance(obj["schema_version"], (int, float)):
                obj["schema_version"] = f"v{obj['schema_version']}"
            
            # 3. task_type 설정
            if "task_type" not in obj or not obj.get("task_type"):
                if doc_summary:
                    obj["task_type"] = doc_summary[:30]
                else:
                    obj["task_type"] = "기타 업무"
            
            # 4. 필수 필드 기본값 설정
            # doc_summary와 entities를 분석하여 적절한 기본값 추정
            if "category" not in obj:
                # entities에 외부 이메일이나 외부 기관이 있으면 '사외', 없으면 '사내'
                has_external = any(e.entity in ['EMAIL', 'ORGANIZATION'] for e in entities)
                obj["category"] = "사외" if has_external else "사내"
                
            if "audience" not in obj:
                # entities에 EMAIL이 있으면 'EMPLOYEE', 없으면 'PUBLIC'
                has_employee = any(e.entity == 'EMAIL' for e in entities)
                obj["audience"] = "EMPLOYEE" if has_employee else "PUBLIC"
                
            if "channel" not in obj:
                # entities에 EMAIL이 있으면 'EMAIL', 없으면 'WEB'
                has_email = any(e.entity == 'EMAIL' for e in entities)
                obj["channel"] = "EMAIL" if has_email else "WEB"
                
            if "purpose" not in obj:
                # doc_summary에서 purpose 추정
                if any(word in doc_summary.lower() for word in ["공지", "안내"]):
                    obj["purpose"] = "ANNOUNCEMENT"
                elif "이동" in doc_summary.lower():
                    obj["purpose"] = "HR_MOVE"
                elif any(word in doc_summary.lower() for word in ["당첨", "합격"]):
                    obj["purpose"] = "WINNER_NOTICE"
                else:
                    obj["purpose"] = "OTHER"
                    
            if "legal_priority" not in obj:
                # 기본값은 LAW_OVER_POLICY
                obj["legal_priority"] = "LAW_OVER_POLICY"
                    
            # 4. audience를 단일 값으로 변환 (여러 값이 있으면 첫 번째 값 사용)
            if "audience" in obj and isinstance(obj["audience"], list):
                obj["audience"] = obj["audience"][0]
                    
            # 5. 숫자 타입 필드들의 타입 변환
            if "confidence" in obj and isinstance(obj["confidence"], str):
                try:
                    obj["confidence"] = float(obj["confidence"])
                except ValueError:
                    obj["confidence"] = 0.0

            allowed_keys = self.schema.get("properties", {}).keys()
            obj = {k: v for k, v in obj.items() if k in allowed_keys}

            try:
                validate_schema(obj, self.schema)
                return obj
            except ValidationError as e:
                last_err = f"스키마 검증 실패: {e.message} (시도 {attempt})\nJSON: {json.dumps(obj, ensure_ascii=False, indent=2)}"
                print(f"\n--- 디버그 정보 ---\n{last_err}\n---\n")  # 디버그 출력 추가
                time.sleep(RETRY_SLEEP)
                continue

        raise RuntimeError("TaskProfile 생성 실패. 마지막 오류=" + str(last_err))

    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        if "```" in text:
            parts = text.split("```")
            for p in parts:
                s = p.strip()
                if s.startswith("{") or s.startswith("["):
                    return s
        start = text.find("{")
        if start == -1:
            return None
        brace = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                brace += 1
            elif text[i] == "}":
                brace -= 1
                if brace == 0:
                    return text[start:i+1]
        return None
