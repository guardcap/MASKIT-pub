#!/bin/bash

# 전체 이메일 플로우 테스트 스크립트
# 1. 메일 작성 데이터 준비
# 2. RAG 분석 요청
# 3. 마스킹 적용 확인

echo "===== 전체 이메일 마스킹 플로우 테스트 ====="
echo ""

# Step 1: PII 탐지된 이메일 데이터
echo "Step 1: PII 자동 탐지"
echo "-------------------------------"

EMAIL_DATA='{
  "email_body": "안녕하세요,\n\n신규 고객 계약 건으로 연락드립니다.\n\n고객 정보:\n- 이름: 홍길동\n- 이메일: hong@customer.com\n- 전화번호: 010-1234-5678\n- 주민등록번호: 850101-1234567\n- 계좌번호: 110-123-456789\n\n위 정보로 계약서 작성 부탁드립니다.\n\n감사합니다.",
  "email_subject": "신규 고객 계약 정보 전달",
  "context": {
    "sender_type": "internal",
    "receiver_type": "external",
    "purpose": ["contract"],
    "regulations": ["PIPA"]
  },
  "detected_pii": [
    {"type": "email", "value": "hong@customer.com"},
    {"type": "phone", "value": "010-1234-5678"},
    {"type": "jumin", "value": "850101-1234567"},
    {"type": "account", "value": "110-123-456789"}
  ],
  "query": "외부 고객에게 이메일을 보낼 때 개인정보 마스킹 규정"
}'

echo "탐지된 PII:"
echo "  - 이메일: hong@customer.com"
echo "  - 전화번호: 010-1234-5678"
echo "  - 주민등록번호: 850101-1234567"
echo "  - 계좌번호: 110-123-456789"
echo ""

# Step 2: RAG 분석 요청
echo "Step 2: RAG 분석 및 마스킹 결정"
echo "-------------------------------"

RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/vectordb/analyze \
  -H "Content-Type: application/json" \
  -d "$EMAIL_DATA" \
  --max-time 10)

echo "API 응답:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Step 3: 마스킹 결정 파싱
echo "Step 3: 마스킹 결정 추출"
echo "-------------------------------"

SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])" 2>/dev/null)

if [ "$SUCCESS" = "True" ]; then
  echo "✅ RAG 분석 성공"

  # 마스킹 결정 개수 확인
  DECISION_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['data']['masking_decisions']))" 2>/dev/null)
  echo "마스킹 결정: ${DECISION_COUNT}개"

  # 각 PII별 마스킹 결정 출력
  echo ""
  echo "PII별 마스킹 결정:"
  for i in 0 1 2 3; do
    PII_TYPE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['masking_decisions'].get('pii_$i', {}).get('type', 'N/A'))" 2>/dev/null)
    PII_VALUE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['masking_decisions'].get('pii_$i', {}).get('value', 'N/A'))" 2>/dev/null)
    SHOULD_MASK=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['masking_decisions'].get('pii_$i', {}).get('should_mask', False))" 2>/dev/null)
    MASKED_VALUE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['masking_decisions'].get('pii_$i', {}).get('masked_value', 'N/A'))" 2>/dev/null)
    REASON=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['masking_decisions'].get('pii_$i', {}).get('reason', 'N/A'))" 2>/dev/null)

    if [ "$SHOULD_MASK" = "True" ]; then
      echo "  [$i] ${PII_TYPE}: ${PII_VALUE} → ${MASKED_VALUE}"
      echo "      이유: ${REASON}"
    else
      echo "  [$i] ${PII_TYPE}: ${PII_VALUE} (마스킹 불필요)"
    fi
  done

  echo ""
  echo "요약:"
  SUMMARY=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['summary'])" 2>/dev/null)
  echo "  ${SUMMARY}"

else
  echo "❌ RAG 분석 실패"
fi

echo ""
echo "===== 테스트 완료 ====="
