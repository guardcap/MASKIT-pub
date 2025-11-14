"""
LLM 마스킹 결정을 위한 프롬프트 생성 및 응답 파싱
"""
import json
from typing import Dict, List, Any
from datetime import datetime


class MaskingPrompter:
    """LLM 프롬프트 생성 및 응답 처리"""

    SYSTEM_PROMPT = """You are an expert data privacy compliance assistant for a Korean enterprise.

Your task is to analyze emails containing personally identifiable information (PII) and determine appropriate masking strategies based on:
- Korean Personal Information Protection Act (PIPA, 개인정보보호법)
- Relevant data protection guidelines
- Company internal policies
- Email context (sender/receiver type, purpose)

**Decision Criteria:**
1. **External transmission**: Most PII should be masked when sending to external parties
2. **Sensitive PII**: 주민등록번호 (jumin), 계좌번호 (account) should ALWAYS be masked
3. **Internal transmission**: Less strict, but sensitive PII still requires masking
4. **Business necessity**: Consider if the PII is essential for the email's purpose

**Masking Methods:**
- `full`: Complete masking (예: hong@example.com → ***@***.com)
- `partial`: Partial masking (예: hong@example.com → ho***@example.com)
- `hash`: One-way hash (for audit trail)
- `redact`: Complete removal
- `none`: No masking (only when clearly safe)

Always err on the side of caution. When in doubt, mask it."""

    USER_PROMPT_TEMPLATE = """# Email Analysis Request

## Email Information
- **Subject**: {email_subject}
- **Context**: {context_summary}

## Detected PII (Total: {pii_count})
{pii_list}

## Relevant Guidelines from VectorDB
{guidelines}

## Instructions
For EACH PII item above, provide a JSON decision with:
- `should_mask`: true/false
- `masking_method`: "full" | "partial" | "hash" | "redact" | "none"
- `reason`: Brief explanation (1-2 sentences, reference guideline if applicable)
- `risk_level`: "critical" | "high" | "medium" | "low"
- `confidence`: 0.0 ~ 1.0

**Output Format** (respond ONLY with valid JSON, no markdown):
{{
  "decisions": {{
    "pii_0": {{
      "should_mask": true,
      "masking_method": "partial",
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
        guidelines: List[Dict[str, Any]]
    ) -> tuple[str, str]:
        """
        LLM 프롬프트 생성

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
                            decisions[pii_id].get("masking_method", "full")
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
    def _generate_masked_preview(cls, value: str, pii_type: str, method: str) -> str:
        """마스킹 미리보기 생성"""
        if method == "full":
            return "***"
        elif method == "partial":
            if pii_type == "email":
                parts = value.split("@")
                if len(parts) == 2:
                    return parts[0][:2] + "***@" + parts[1]
            elif pii_type == "phone":
                return value[:3] + "-***-" + value[-4:]
            elif pii_type == "jumin":
                return value[:6] + "-*******"
            elif pii_type == "account":
                parts = value.split("-")
                if len(parts) == 3:
                    return parts[0] + "-***-" + parts[2]
            return value[:3] + "***"
        elif method == "redact":
            return "[REDACTED]"
        elif method == "hash":
            return "[HASHED]"
        else:
            return value
