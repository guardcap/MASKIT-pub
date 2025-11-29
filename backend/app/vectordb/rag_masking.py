"""
RAG 기반 마스킹 결정 모듈
- OpenAI Vector Store에서 검색된 가이드라인을 LLM에게 전달
- LLM이 각 PII별로 마스킹 필요 여부, 방법, 법적 근거를 판단
"""

from typing import List, Dict, Any
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# PII 타입별 한글명 매핑
PII_TYPE_NAMES = {
    'email': '이메일',
    'phone': '전화번호',
    'jumin': '주민등록번호',
    'resident_id': '주민등록번호',
    'account': '계좌번호',
    'bank_account': '계좌번호',
    'passport': '여권번호',
    'driver_license': '운전면허번호',
    'name': '이름',
    'person': '이름',
    'address': '주소',
    'company': '회사명',
    'organization': '조직명',
    'card_number': '카드번호'
}


def normalize_receiver_type(context: Dict[str, Any]) -> str:
    """
    컨텍스트에서 수신자 타입을 추출하고 정규화

    Returns:
        'external', 'internal', 또는 'unknown'
    """
    receiver_type = context.get('receiver_type', '')
    purposes = context.get('purpose', [])

    # 사외 수신자 키워드
    external_categories = ['협력 업체', '고객사', '정부 기관']
    government_purposes = ['세무 신고', '재무 보고', '감사 대응', '규제 준수']

    # 사내 수신자 키워드
    internal_categories = ['인사팀', '고객지원팀', 'R&D팀', '대외협력팀', '개발팀']

    # 1. purpose 기반 판단
    if isinstance(purposes, list) and purposes:
        if any(cat in purpose for purpose in purposes for cat in external_categories):
            return 'external'
        elif any(gov_purpose in purpose for purpose in purposes for gov_purpose in government_purposes):
            return 'external'
        elif any(dept in purpose for purpose in purposes for dept in internal_categories):
            return 'internal'

    # 2. receiver_type 한글 → 영어 변환
    if receiver_type == '사외':
        return 'external'
    elif receiver_type == '사내':
        return 'internal'
    elif receiver_type in ['external', 'internal']:
        return receiver_type

    return 'unknown'


def build_guideline_context(guides: List[Dict[str, Any]], max_guides: int = 5) -> str:
    """
    검색된 가이드라인을 프롬프트용 텍스트로 구성
    """
    if not guides:
        return "관련 가이드라인을 찾을 수 없습니다."

    guideline_context = "검색된 정책 가이드라인:\n"
    for idx, guide in enumerate(guides[:max_guides], 1):
        content = guide.get('content', '')
        filename = guide.get('filename', '정책 문서')
        # 더 많은 내용 포함 (600자 → 1000자)
        guideline_context += f"\n[가이드라인 {idx}] 출처: {filename}\n{content[:1000]}\n"

    return guideline_context


async def decide_masking_with_rag(
    pii_type: str,
    pii_value: str,
    context: Dict[str, Any],
    guides: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    RAG 기반으로 단일 PII에 대한 마스킹 결정

    Args:
        pii_type: PII 타입 (예: 'email', 'person', 'resident_id')
        pii_value: PII 실제 값
        context: 이메일 전송 컨텍스트 (receiver_type, purpose, regulations 등)
        guides: Vector Store에서 검색된 가이드라인 목록

    Returns:
        {
            "should_mask": bool,
            "masking_method": "full" | "none",
            "legal_basis": str,
            "reason": str,
            "confidence": float,
            "cited_guidelines": List[str]
        }
    """

    # 수신자 타입 정규화
    receiver_type = normalize_receiver_type(context)
    receiver_type_kr = '사외' if receiver_type == 'external' else '사내' if receiver_type == 'internal' else '알 수 없음'

    # 컨텍스트 정보
    purposes = context.get('purpose', [])
    regulations = context.get('regulations', [])
    purpose_str = ', '.join(purposes) if purposes else '미지정'
    regulation_str = ', '.join(regulations) if regulations else '미지정'

    # PII 타입 한글명
    pii_type_lower = pii_type.lower()
    pii_type_kr = PII_TYPE_NAMES.get(pii_type_lower, pii_type)

    # 가이드라인 컨텍스트 구성
    guideline_context = build_guideline_context(guides)

    # 규정 우선순위 결정
    is_company_policy_first = '사내 규칙' in regulation_str or '회사 정책' in regulation_str
    is_law_first = '국내 법률' in regulation_str or '개인정보보호법' in regulation_str
    is_gdpr_first = 'GDPR' in regulation_str

    # LLM 프롬프트 구성
    if is_company_policy_first:
        prompt_intro = """당신은 개인정보 보호 전문가입니다. **회사 내부 정책 가이드라인을 최우선으로** 참고하여 개인정보 마스킹 여부를 판단하세요."""
        guideline_instruction = """**반드시 위의 회사 정책 가이드라인을 최우선으로 참고**하여 다음을 결정하세요.
가이드라인에 명시된 조항과 정책을 정확히 인용하세요. 가이드라인이 우선이며, 법률은 보조 참고용입니다:"""
    elif is_gdpr_first:
        prompt_intro = """당신은 개인정보 보호 전문가입니다. **EU GDPR(General Data Protection Regulation)을 최우선으로** 참고하여 개인정보 마스킹 여부를 판단하세요."""
        guideline_instruction = """**반드시 EU GDPR을 최우선으로 참고**하여 다음을 결정하세요.
GDPR 조항을 정확히 명시하고, 국내 법률 및 회사 정책은 보조 참고용으로만 활용하세요:"""
    else:
        prompt_intro = """당신은 개인정보 보호 전문가입니다. **개인정보보호법 등 국내 법률을 최우선으로** 참고하여 개인정보 마스킹 여부를 판단하세요."""
        guideline_instruction = """**반드시 개인정보보호법 등 국내 법률을 최우선으로 참고**하여 다음을 결정하세요.
법 조항을 정확히 명시하고, 회사 정책 가이드라인은 보조 참고용으로만 활용하세요:"""

    prompt = f"""{prompt_intro}

## 이메일 전송 상황
- 수신자 타입: {receiver_type_kr} ({receiver_type})
- 전송 목적: {purpose_str}
- 적용 법률/규정: {regulation_str}

## 개인정보 항목
- PII 타입: {pii_type_kr} ({pii_type_lower})
- 값: {pii_value}

## 회사 정책 가이드라인
{guideline_context}

## 판단 요청
{guideline_instruction}

1. 마스킹 필요 여부 (true/false)
2. 마스킹 방법:
   - full: 마스킹 필요
   - none: 마스킹 불필요
3. 법적 근거: 상황에 맞는 구체적인 조항 명시 (회사 정책 조항 또는 법 조항)
4. 판단 이유: 1-2문장으로 명확하게 설명

**조직명/회사명에 대한 특별 지침**:
- 조직명은 **일반적으로 개인정보가 아닙니다** (개인정보보호법 제2조)
- 단, **개인과 연결된 조직명**의 경우 마스킹이 필요할 수 있습니다:
  * "홍길동이 근무하는 삼성전자" → 개인의 소속 정보로 간접 식별 가능
  * "김철수의 학교인 서울여자대학교" → 개인의 학력 정보로 간접 식별 가능
  * "이영희 법률사무소" → 개인명이 포함된 조직명
- **단독으로 언급된 조직명**은 마스킹 불필요:
  * "삼성전자 제품", "국민은행 계좌" → 단순 조직명 언급
- 법적 근거: "개인정보보호법 제2조 (정의) - 다른 정보와 결합하여 개인 식별 가능 시 개인정보"

**적용 가능한 개인정보보호법 조항 (참고용)**:
- 제15조: 개인정보의 수집·이용
- 제17조: 개인정보의 제공 (제3자 제공)
- 제18조: 목적 외 이용·제공 제한
- 제23조: 민감정보의 처리 제한
- 제24조: 고유식별정보의 처리 제한
- 제24조의2: 주민등록번호 처리의 제한
- 제29조: 안전조치의무

**적용 가능한 GDPR 조항 (참고용)**:
- Article 5: 개인정보 처리의 원칙 (Principles relating to processing of personal data)
- Article 6: 처리의 적법성 (Lawfulness of processing)
- Article 9: 특수 범주 개인정보의 처리 (Processing of special categories of personal data)
- Article 32: 처리의 보안 (Security of processing)
- Article 44-50: 제3국 또는 국제기구로의 이전 (Transfers of personal data to third countries or international organisations)

**응답 형식 (JSON만)**:
"""

    # 조직명 처리
    if pii_type_lower in ['organization', 'company']:
        response_example = """{
  "should_mask": false,
  "masking_method": "none",
  "legal_basis": "개인정보보호법 제2조 (정의)",
  "reason": "단독으로 언급된 조직명은 특정 개인을 식별할 수 없어 마스킹이 불필요합니다. 단, 개인과 연결된 조직명(예: 홍길동의 근무지)의 경우 마스킹이 필요할 수 있습니다.",
  "confidence": 0.90
}"""
    # 응답 예시를 우선순위에 따라 다르게 설정
    elif is_company_policy_first:
        response_example = """{
  "should_mask": true,
  "masking_method": "full",
  "legal_basis": "회사 정책 제5조 (등급별 처리 기준) - 1등급 개인정보 외부 전송 금지",
  "reason": "회사 정책에 따라 1등급 개인정보는 외부 전송이 원칙적으로 금지되어 마스킹이 필수입니다.",
  "confidence": 0.95
}"""
    elif is_gdpr_first:
        response_example = """{
  "should_mask": true,
  "masking_method": "full",
  "legal_basis": "GDPR Article 9 (특수 범주 개인정보의 처리)",
  "reason": "GDPR에 따라 민감한 개인정보는 EU 외부로 전송 시 엄격한 보호조치가 필요하여 마스킹이 필수입니다.",
  "confidence": 0.95
}"""
    else:
        response_example = """{
  "should_mask": true,
  "masking_method": "full",
  "legal_basis": "개인정보보호법 제24조 (고유식별정보의 처리 제한)",
  "reason": "주민등록번호는 고유식별정보로 제3자 제공 시 법적 제한이 있어 마스킹이 필수입니다.",
  "confidence": 0.95
}"""

    prompt += response_example
    prompt += "\n\"\"\""

    try:
        # OpenAI GPT 호출
        llm_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 한국의 개인정보보호법 전문가입니다. 모든 응답은 반드시 한국어로만 작성하고, JSON 형식으로만 응답하세요. legal_basis와 reason 필드는 반드시 한국어로만 작성해야 합니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=600
        )

        # LLM 응답 파싱
        llm_result = json.loads(llm_response.choices[0].message.content)

        should_mask = llm_result.get('should_mask', False)
        masking_method = llm_result.get('masking_method', 'none')
        legal_basis = llm_result.get('legal_basis', '')
        reason = llm_result.get('reason', '')
        confidence = llm_result.get('confidence', 0.8)

        cited_guidelines = [legal_basis] if legal_basis else []

        return {
            "should_mask": should_mask,
            "masking_method": masking_method,
            "legal_basis": legal_basis,
            "reason": reason,
            "confidence": confidence,
            "cited_guidelines": cited_guidelines,
            "reasoning_steps": [
                f"1. 컨텍스트: {receiver_type_kr} 전송, 목적={purpose_str}",
                f"2. PII 유형: {pii_type_kr}",
                f"3. RAG 검색: {len(guides)}개 가이드라인 참조",
                f"4. AI 판단: {masking_method.upper()} 마스킹",
                f"5. 법적 근거: {legal_basis}",
                f"6. 판단 이유: {reason}"
            ]
        }

    except Exception as e:
        print(f"❌ RAG 마스킹 판단 실패: {e}")
        # Fallback: 기본 규칙
        should_mask = receiver_type == 'external'
        masking_method = "full" if should_mask else "none"
        legal_basis = "개인정보보호법 제17조 (개인정보 제3자 제공)"

        return {
            "should_mask": should_mask,
            "masking_method": masking_method,
            "legal_basis": legal_basis,
            "reason": f"LLM 판단 실패, 기본 규칙 적용: {receiver_type_kr} 전송",
            "confidence": 0.5,
            "cited_guidelines": [legal_basis],
            "reasoning_steps": [
                f"1. LLM 판단 실패, fallback 사용",
                f"2. 수신자: {receiver_type_kr}",
                f"3. 기본 마스킹: {masking_method}"
            ]
        }


async def decide_all_pii_with_rag(
    detected_pii: List[Dict[str, str]],
    context: Dict[str, Any],
    guides: List[Dict[str, Any]],
    progress_callback=None
) -> Dict[str, Any]:
    """
    모든 PII에 대해 RAG 기반 마스킹 결정

    Args:
        progress_callback: 진행 상황을 전달할 콜백 함수

    Returns:
        {
            "pii_0": {...},
            "pii_1": {...},
            ...
        }
    """
    decisions = {}

    for i, pii in enumerate(detected_pii):
        pii_type = pii.get('type', '')
        pii_value = pii.get('value', '')

        log_msg = f"[RAG] PII #{i+1}/{len(detected_pii)}: type={pii_type}, value={pii_value[:10]}..."
        print(log_msg)
        if progress_callback:
            progress_callback(log_msg)

        # RAG 기반 판단
        decision = await decide_masking_with_rag(pii_type, pii_value, context, guides)

        # 마스킹 미리보기 생성
        masked_value = None
        if decision['should_mask']:
            from app.utils.masking_rules import MaskingRules
            try:
                masked_value = MaskingRules.apply_masking(pii_value, pii_type.lower(), 'full')
            except Exception as e:
                print(f"❌ 마스킹 미리보기 실패: {e}")
                masked_value = "***"

        # 결과 저장
        decisions[f"pii_{i}"] = {
            "pii_id": f"pii_{i}",
            "type": pii_type,
            "value": pii_value,
            "should_mask": decision['should_mask'],
            "masking_method": decision['masking_method'],
            "masked_value": masked_value,
            "reason": decision['reason'],
            "reasoning": "\n".join(decision['reasoning_steps']),
            "cited_guidelines": decision['cited_guidelines'],
            "confidence": decision['confidence'],
            "risk_level": (
                "high" if pii_type.lower() in ['jumin', 'resident_id', 'account', 'bank_account', 'card_number', 'passport', 'driver_license']
                else "medium" if pii_type.lower() in ['person', 'email', 'phone', 'address'] and decision['should_mask']
                else "low"
            )
        }

        print(f"✅ PII #{i} 판단 완료: {decision['masking_method']}, 근거: {decision['legal_basis']}")

    return decisions
