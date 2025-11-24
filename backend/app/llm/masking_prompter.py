"""
LLM 마스킹 결정을 위한 프롬프트 생성 및 응답 파싱
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


async def load_entity_masking_rules(db_client) -> Dict[str, Dict[str, Any]]:
    """
    MongoDB에서 모든 활성화된 엔티티의 마스킹 규칙을 로드

    Returns:
        {
            "PHONE": {"masking_type": "partial", "masking_char": "*", "masking_pattern": "###-****-####"},
            "EMAIL": {"masking_type": "full", "masking_char": "*", "masking_pattern": None},
            ...
        }
    """
    if db_client is None:
        return {}

    rules = {}
    try:
        cursor = db_client["entities"].find({"is_active": True})
        async for entity in cursor:
            entity_id = entity.get("entity_id", "").upper()
            if entity_id:
                rules[entity_id] = {
                    "masking_type": entity.get("masking_type", "full"),
                    "masking_char": entity.get("masking_char", "*"),
                    "masking_pattern": entity.get("masking_pattern"),
                    "name": entity.get("name", entity_id),
                }
        print(f"📋 {len(rules)}개의 엔티티 마스킹 규칙 로드 완료")
    except Exception as e:
        print(f"⚠️ 엔티티 마스킹 규칙 로드 실패: {e}")

    return rules


class MaskingPrompter:
    """LLM 프롬프트 생성 및 응답 처리"""

    SYSTEM_PROMPT = """You are an expert data privacy compliance assistant for a Korean enterprise.

Your task is to analyze emails containing personally identifiable information (PII) and determine appropriate masking strategies based on:
- Korean Personal Information Protection Act (PIPA, 개인정보보호법)
- Relevant data protection guidelines
- Company internal policies
- Email context (sender/receiver type, purpose)
- **Entity-specific masking rules defined by the organization**

**Decision Criteria:**
1. **External transmission**: Most PII should be masked when sending to external parties
2. **Sensitive PII**: 주민등록번호 (jumin), 계좌번호 (account) should ALWAYS be masked
3. **Internal transmission**: Less strict, but sensitive PII still requires masking
4. **Business necessity**: Consider if the PII is essential for the email's purpose
5. **Entity-specific rules**: Follow the pre-defined masking configuration for each entity type

**Masking Methods:**
- `full`: Complete masking (예: hong@example.com → ***@***.com)
- `partial`: Partial masking (예: hong@example.com → ho***@example.com)
- `custom`: Apply entity-specific custom pattern (예: 123-45-67890 → 123-45-*****)
- `hash`: One-way hash (for audit trail)
- `redact`: Complete removal
- `none`: No masking (only when clearly safe)

**IMPORTANT:** When an entity has a pre-defined masking rule, you MUST respect that rule unless there's a compelling security reason to apply stricter masking.

Always err on the side of caution. When in doubt, mask it."""

    USER_PROMPT_TEMPLATE = """# Email Analysis Request

## Email Information
- **Subject**: {email_subject}
- **Context**: {context_summary}

## Detected PII (Total: {pii_count})
{pii_list}

## Entity-Specific Masking Rules (Pre-defined by Organization)
{masking_rules}

## Relevant Guidelines from VectorDB
{guidelines}

## Instructions
For EACH PII item above, provide a JSON decision with:
- `should_mask`: true/false
- `masking_method`: "full" | "partial" | "custom" | "hash" | "redact" | "none"
- `masking_char`: The character to use for masking (default: "*")
- `masking_pattern`: Custom pattern if masking_method is "custom" (e.g., "###-##-*****")
- `reason`: Brief explanation (1-2 sentences, reference guideline if applicable)
- `risk_level`: "critical" | "high" | "medium" | "low"
- `confidence`: 0.0 ~ 1.0

**IMPORTANT:** If an entity has a pre-defined masking rule listed above, use that configuration unless security concerns require stricter masking.

**Output Format** (respond ONLY with valid JSON, no markdown):
{{
  "decisions": {{
    "pii_0": {{
      "should_mask": true,
      "masking_method": "partial",
      "masking_char": "*",
      "masking_pattern": null,
      "reason": "외부 전송 시 이메일 부분 마스킹 권장 (PIPA 제17조)",
      "risk_level": "medium",
      "confidence": 0.9
    }},
    ...
  }},
  "summary": "Overall analysis summary in Korean (1-2 sentences)"
}}"""

    @classmethod
    def build_prompt(
        cls,
        email_subject: str,
        detected_pii: List[Dict[str, str]],
        context: Dict[str, Any],
        guidelines: List[Dict[str, Any]],
        entity_masking_rules: Dict[str, Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """
        LLM 프롬프트 생성

        Args:
            email_subject: 이메일 제목
            detected_pii: 탐지된 PII 목록
            context: 이메일 컨텍스트
            guidelines: VectorDB 가이드라인
            entity_masking_rules: 엔티티별 마스킹 규칙 (MongoDB에서 로드)
                예: {"PHONE": {"masking_type": "partial", "masking_char": "*", "masking_pattern": "###-****-####"}}

        Returns:
            (system_prompt, user_prompt)
        """
        # 컨텍스트 요약
        context_summary = f"{context.get('sender_type', 'unknown')} → {context.get('receiver_type', 'unknown')}"
        purpose = context.get('purpose', [])
        if purpose:
            context_summary += f" | Purpose: {', '.join(purpose)}"

        # PII 목록 포맷
        pii_list = []
        for i, pii in enumerate(detected_pii):
            pii_list.append(
                f"  [{i}] pii_{i}: {pii.get('type', 'unknown')} = \"{pii.get('value', 'N/A')}\""
            )
        pii_list_str = "\n".join(pii_list) if pii_list else "  (No PII detected)"

        # 엔티티별 마스킹 규칙 포맷
        masking_rules_strs = []
        if entity_masking_rules:
            for entity_type, rules in entity_masking_rules.items():
                masking_type = rules.get('masking_type', 'full')
                masking_char = rules.get('masking_char', '*')
                masking_pattern = rules.get('masking_pattern', '')

                rule_desc = f"  - **{entity_type}**: type={masking_type}, char='{masking_char}'"
                if masking_pattern:
                    rule_desc += f", pattern='{masking_pattern}'"
                masking_rules_strs.append(rule_desc)

        masking_rules_str = "\n".join(masking_rules_strs) if masking_rules_strs else "  (No custom rules defined - use default full masking)"

        # 가이드라인 포맷
        guideline_strs = []
        for i, guide in enumerate(guidelines[:5], 1):  # 상위 5개만
            scenario = guide.get('scenario', '')
            directive = guide.get('directive', '')
            score = guide.get('distance', 1.0)
            relevance = (1.0 - score) * 100  # distance → relevance %

            guideline_strs.append(
                f"  [{i}] (Relevance: {relevance:.1f}%)\n"
                f"      Scenario: {scenario[:150]}...\n"
                f"      Directive: {directive[:150]}..."
            )

        guidelines_str = "\n".join(guideline_strs) if guideline_strs else "  (No guidelines found)"

        user_prompt = cls.USER_PROMPT_TEMPLATE.format(
            email_subject=email_subject,
            context_summary=context_summary,
            pii_count=len(detected_pii),
            pii_list=pii_list_str,
            masking_rules=masking_rules_str,
            guidelines=guidelines_str
        )

        return cls.SYSTEM_PROMPT, user_prompt

    @classmethod
    def parse_llm_response(
        cls,
        response_text: str,
        detected_pii: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        LLM 응답 파싱 및 검증

        Args:
            response_text: LLM이 반환한 JSON 문자열
            detected_pii: 원본 PII 목록

        Returns:
            파싱된 마스킹 결정
        """
        try:
            # JSON 추출 (마크다운 코드 블록 제거)
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # ```json ... ``` 형태 제거
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])

            data = json.loads(response_text)

            decisions = data.get("decisions", {})
            summary = data.get("summary", "마스킹 분석 완료")

            # 원본 PII 정보 병합
            for i, pii in enumerate(detected_pii):
                pii_id = f"pii_{i}"
                if pii_id in decisions:
                    decisions[pii_id]["pii_id"] = pii_id
                    decisions[pii_id]["type"] = pii.get("type")
                    decisions[pii_id]["value"] = pii.get("value")

                    # 마스킹 미리보기 생성
                    if decisions[pii_id].get("should_mask", False):
                        masked = cls._generate_masked_preview(
                            pii.get("value", ""),
                            pii.get("type", ""),
                            decisions[pii_id].get("masking_method", "full"),
                            decisions[pii_id].get("masking_char", "*"),
                            decisions[pii_id].get("masking_pattern")
                        )
                        decisions[pii_id]["masked_value"] = masked

            return {
                "decisions": decisions,
                "summary": summary
            }

        except json.JSONDecodeError as e:
            print(f"⚠️ LLM 응답 JSON 파싱 실패: {e}")
            print(f"응답 내용: {response_text[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

    @classmethod
    def _generate_masked_preview(
        cls,
        value: str,
        pii_type: str,
        method: str,
        masking_char: str = "*",
        masking_pattern: str = None
    ) -> str:
        """
        마스킹 미리보기 생성

        Args:
            value: 원본 값
            pii_type: PII 타입
            method: 마스킹 방식 (full, partial, custom, hash, redact, none)
            masking_char: 마스킹 문자 (기본값: *)
            masking_pattern: 커스텀 패턴 (# = 원본 유지, masking_char = 마스킹)
        """
        if method == "full":
            return masking_char * 3
        elif method == "custom" and masking_pattern:
            # 커스텀 패턴 적용
            return cls._apply_custom_pattern(value, masking_pattern, masking_char)
        elif method == "partial":
            if pii_type.lower() in ["email", "이메일"]:
                parts = value.split("@")
                if len(parts) == 2:
                    return parts[0][:2] + masking_char * 3 + "@" + parts[1]
            elif pii_type.lower() in ["phone", "전화번호", "휴대전화"]:
                clean = value.replace("-", "")
                if len(clean) >= 7:
                    return clean[:3] + "-" + masking_char * 4 + "-" + clean[-4:]
            elif pii_type.lower() in ["jumin", "주민등록번호", "resident_id"]:
                clean = value.replace("-", "")
                if len(clean) >= 6:
                    return clean[:6] + "-" + masking_char * 7
            elif pii_type.lower() in ["account", "계좌번호", "bank_account"]:
                parts = value.split("-")
                if len(parts) >= 2:
                    return parts[0] + "-" + masking_char * 4 + "-" + masking_char * 4
            # 기본 부분 마스킹: 앞 3자리 유지
            if len(value) > 3:
                return value[:3] + masking_char * 3
            return masking_char * 3
        elif method == "redact":
            return "[REDACTED]"
        elif method == "hash":
            return "[HASHED]"
        else:
            return value

    @classmethod
    def _apply_custom_pattern(cls, value: str, pattern: str, masking_char: str) -> str:
        """
        커스텀 패턴을 적용하여 마스킹

        패턴 규칙:
        - # : 원본 문자 유지
        - masking_char와 동일한 문자 : 마스킹 처리
        - 그 외 문자(-, 공백 등) : 그대로 유지 (구분자)

        예: pattern="###-##-*****", value="123-45-67890", masking_char="*"
            결과: "123-45-*****"
        """
        result = []
        value_idx = 0
        clean_value = ''.join(c for c in value if c.isalnum())  # 숫자/문자만 추출

        for pattern_char in pattern:
            if pattern_char == '#':
                # 원본 유지
                if value_idx < len(clean_value):
                    result.append(clean_value[value_idx])
                    value_idx += 1
                else:
                    result.append('#')
            elif pattern_char == masking_char or pattern_char == '*':
                # 마스킹 처리
                result.append(masking_char)
                value_idx += 1
            else:
                # 구분자 등 그대로 유지
                result.append(pattern_char)

        return ''.join(result)
