from __future__ import annotations

# 소스 우선순위 (Audience에 따라 RAG 소스 가중)
SOURCE_ORDER = {
    "external":        ["LAW", "GOV_GUIDE", "CONTRACT", "INTERNAL_POLICY"],
    "internal_public": ["INTERNAL_POLICY", "LAW", "GOV_GUIDE", "CONTRACT"],
    "internal_limited":["INTERNAL_POLICY", "LAW", "GOV_GUIDE", "CONTRACT"],
}

# 우선순위 스코어 가중치
DEFAULT_WEIGHTS = {
    "priority_base": {"LAW": 1.0, "GOV_GUIDE": 0.9, "CONTRACT": 0.85, "INTERNAL_POLICY": 0.8},
    "audience_match": 0.20,
    "role_match": 0.15,
    "jurisdiction_match": 0.15,
    "recency": 0.10,             # (옵션) 최신 문서 가중치 넣고 싶으면 사용
    "cluster_consistency": 0.10, # (옵션) 같은 클러스터 다수 일치 가중
}

# 보수적 상향 순서 (검증단계에서 사용)
CONSERVATIVE_ORDER = ["keep", "mask_partial", "mask_full"]

# 기본 Ollama 모델 (환경에 맞게 변경 가능)
# - json 출력 강제 시 최신 instruct 모델 권장
OLLAMA_MODEL = "llama3"

# 검증 휴리스틱: 특정 데이터유형은 external에서 keep 금지 등
HEURISTICS = {
    "external_forbid_keep_types": {"PERSONAL_PHONE", "PHONE_NUMBER", "MOBILE", "NATIONAL_ID"},
    "partial_mask_defaults": {
        "ACCOUNT_NUMBER": {"keep_last": 4, "separator": "-"},
        "PHONE_NUMBER":   {"middle_mask": 3},
    }
}
