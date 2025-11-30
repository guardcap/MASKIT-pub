from __future__ import annotations
import json
from typing import List, Dict, Callable, Optional, Any
import os
from .models import Meta, RuleChunk, ContextPack, MaskingAction
from ..entity import Entity, EntityGroup
from .config import SOURCE_ORDER, DEFAULT_WEIGHTS, CONSERVATIVE_ORDER, OLLAMA_MODEL, HEURISTICS

def heuristic_complete_json(prompt: str, schema: Dict[str, Any]) -> List[Dict]:
    """
    모델이 없거나 JSON 스키마가 어긋날 때 쓰는 간단 폴백.
    audience=external이면 PHONE/NATIONAL_ID는 keep 금지, ACCOUNT_NUMBER는 partial, 그 외 keep.
    """
    import re, json as _json
    aud = re.search(r"audience=([a-zA-Z_]+)", prompt)
    audience = aud.group(1) if aud else "internal_limited"
    m = re.search(r"spans=(\[.*?\])", prompt, re.S)
    spans = _json.loads(m.group(1)) if m else []

    forbid = {"PERSONAL_PHONE","PHONE_NUMBER","MOBILE","NATIONAL_ID"}
    out = []
    for s in spans:
        sid, stype = s.get("id",""), str(s.get("type","")).upper()
        if "ACCOUNT" in stype:
            out.append({"id": sid, "decision":"mask_partial", "reason":"heuristic", "citations":[], "format":{"keep_last":4,"separator":"-"}})
        elif audience == "external" and (stype in forbid or "PHONE" in stype):
            out.append({"id": sid, "decision":"mask_full", "reason":"heuristic(external)", "citations":[], "format":{}})
        else:
            out.append({"id": sid, "decision":"keep", "reason":"heuristic", "citations":[], "format":{}})
    return out


# ====== 유틸: pydantic v1/v2 호환 dump ======
def _dump(obj: Any) -> Dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj

def _dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False)
    except TypeError:
        # pydantic model list 지원
        if isinstance(obj, list):
            return json.dumps([_dump(x) for x in obj], ensure_ascii=False)
        return json.dumps(_dump(obj), ensure_ascii=False)

# ====== 1) 라우팅 & 쿼리 생성 ======
def select_source_order(audience: str) -> List[str]:
    return SOURCE_ORDER.get(audience, SOURCE_ORDER["internal_limited"])

def build_closed_queries(meta: Meta, spans: List[Span]) -> List[str]:
    """
    span 유형 + audience + 목적 기반의 '닫힌 질문' 생성 (RAG 검색 품질↑)
    """
    types = sorted({s.type for s in spans})
    qs: List[str] = []
    for t in types:
        qs.append(f"{meta.jurisdiction} 관할에서 {meta.audience} 공개 시 {t} 제공 허용/금지 및 예외는?")
        qs.append(f"{t} 부분 마스킹 표준(자리수/구분자/가명/토큰화)은?")
    qs.append(f"{meta.purpose} 목적에서 최소 공개 원칙과 예외는?")
    return qs[:6]

# ====== 2) 청크 우선순위 ======
def _match(value: str, options: List[str]) -> bool:
    return (value in options) or ("any" in options)

def score_chunk(ch: RuleChunk, meta: Meta) -> float:
    w = DEFAULT_WEIGHTS
    s = w["priority_base"].get(ch.source_type, 0.0)
    if _match(meta.audience, ch.audience): s += w["audience_match"]
    if (not ch.role_scope) or ("all" in ch.role_scope) or (meta.recipient_role and meta.recipient_role in ch.role_scope):
        s += w["role_match"]
    if meta.jurisdiction == ch.jurisdiction: s += w["jurisdiction_match"]
    # (옵션) 최신성/클러스터 일관성 가중치는 필요 시 추가
    return s

def rank_chunks(chunks: List[RuleChunk], meta: Meta) -> List[RuleChunk]:
    return sorted(chunks, key=lambda c: score_chunk(c, meta), reverse=True)

# ====== 3) LLM 플래너 프롬프트 & 호출 ======
PLANNER_JSON_SCHEMA: Dict[str, Any] = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["entity_type", "word", "decision", "format"],
        "properties": {
            "entity_type": {"type": "string"},
            "word": {"type": "string"},
            "decision": {"enum": ["keep", "mask_partial", "mask_full", "generalize", "pseudonymize", "tokenize", "hash"]},
            "format": {"type": "object"}
        }
    }
}

def build_planner_prompt(meta: Meta, entity_group: EntityGroup, pack: ContextPack) -> str:
    cited = [c.chunk_id for c in pack.chunks][:10]
    rules = (
        "아래 규칙에 따라 각 민감정보의 처리 방식을 결정하세요:\n"
        "\n"
        "1. 기본 원칙:\n"
        "- audience=external이면 LAW/GOV 가중치가 INTERNAL보다 우선\n"
        "- need-to-know 원칙: 목적/수신자 역할에 필요한 최소 정보만 공개\n"
        "- 불확실하면 보수적으로 상향(keep→mask_partial→mask_full)\n"
        "- 연락처/이메일은 '업무 연락 필수'일 때만 keep\n"
        "\n"
        "2. 응답 형식 (각 줄을 아래 형식으로 작성):\n"
        "entity_type|decision|format\n"
        "예시:\n"
        "PHONE_NUMBER|mask_full|{\"mask_char\":\"*\"}\n"
        "EMAIL|mask_partial|{\"keep_domain\":true}\n"
        "ACCOUNT_NUMBER|mask_partial|{\"keep_last\":4,\"separator\":\"-\"}\n"
        "\n"
        "3. 가능한 결정:\n"
        "- keep: 원본 유지\n"
        "- mask_partial: 부분 마스킹\n"
        "- mask_full: 전체 마스킹\n"
        "- generalize: 일반화\n"
        "- pseudonymize: 가명화\n"
        "- tokenize: 토큰화\n"
        "- hash: 해시처리\n"
    )

    # 처리할 민감정보 목록
    entities_list = "\n".join(
        f"대상 {i+1}: {e.entity} 유형 (값: {e.word})"
        for i, e in enumerate(entity_group.entities)
    )

    return (
        "개인정보 '최소 공개' 원칙을 집행하는 보안 책임자로서,\n"
        f"다음 상황에서 민감정보 처리 방식을 결정하세요:\n"
        f"\n"
        f"[상황]\n"
        f"- 공개 범위: {meta.audience}\n"
        f"- 사용 목적: {meta.purpose}\n"
        f"- 관할 지역: {meta.jurisdiction}\n"
        f"- 관련 규정: {', '.join(cited)}\n"
        f"\n"
        f"[처리할 민감정보]\n"
        f"{entities_list}\n"
        f"\n"
        f"[결정 규칙]\n"
        f"{rules}\n"
        f"\n"
        f"각 민감정보에 대해 한 줄씩 결정을 응답하세요.\n"
        f"다른 설명이나 부가 텍스트를 포함하지 마세요."
    )

# --- Ollama JSON 호출기(선택 사용) ---
def ollama_complete_json(prompt: str, schema: Dict[str, Any], model: str = OLLAMA_MODEL) -> List[Dict]:
    try:
        import ollama  # noqa
    except Exception as e:
        raise RuntimeError("ollama 패키지가 설치되어 있지 않습니다. pip install ollama") from e

    # 문자열 형태로 응답을 요청하는 프롬프트
    format_guide = """응답 형식:
entity_type|decision|format
PHONE_NUMBER|mask_full|{"mask_char":"*"}
EMAIL|mask_partial|{"keep_domain":true}
ACCOUNT_NUMBER|mask_partial|{"keep_last":4,"separator":"-"}

각 엔티티를 위 형식대로 한 줄씩 응답하세요.
다른 설명이나 텍스트를 포함하지 마세요."""

    resp = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": format_guide},
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0}
    )

    content = (resp.get("message", {}) or {}).get("content", "")
    if not content:
        raise ValueError("빈 응답")

    # 줄 단위로 파싱하여 JSON 객체 리스트 생성
    result = []
    for line in content.strip().split('\n'):
        line = line.strip()
        if not line or '|' not in line:
            continue
            
        try:
            entity_type, decision, format_str = line.split('|')
            # 마스킹 포맷 파싱
            try:
                format_dict = json.loads(format_str)
            except json.JSONDecodeError:
                format_dict = {}
                
            result.append({
                "entity_type": entity_type.strip(),
                "decision": decision.strip(),
                "format": format_dict
            })
        except ValueError:
            continue

    if not result:
        raise ValueError("유효한 응답을 파싱할 수 없습니다.")
        
    return result


    # 2) 최상위가 배열이 아니면 배열로 보정
    if isinstance(data, dict):
        for k in ("decisions", "items", "output", "data", "result"):
            if k in data and isinstance(data[k], list):
                data = data[k]
                break
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            pass
    if not isinstance(data, list):
        raise ValueError("스키마 위반: 최상위는 배열이어야 합니다. (수신형={})".format(type(data).__name__))

    return data


def plan(
    complete_json: Callable[[str, Dict[str, Any]], List[Dict]],
    meta: Meta,
    entity_group: EntityGroup,
    pack: ContextPack
) -> EntityGroup:
    entities_data = [
        {
            "entity_type": e.entity,
            "word": e.word,
            "start": e.start,
            "end": e.end,
            "page": e.pageIndex
        } for e in entity_group.entities
    ]
    
    prompt = build_planner_prompt(meta, entities_data, pack)
    decisions = complete_json(prompt, PLANNER_JSON_SCHEMA)
    
    # 결정사항을 새로운 EntityGroup으로 변환
    masked_entities = []
    for entity, decision in zip(entity_group.entities, decisions):
        masked_entity = MaskingAction.apply_decision(
            entity=entity,
            decision=decision["decision"],
            format_options=decision.get("format", {})
        )
        masked_entities.append(masked_entity)
    
    return EntityGroup(masked_entities)

# ====== 4) 검증 & 보수적 상향 ======
def _lift(decision: str) -> str:
    if decision not in CONSERVATIVE_ORDER:
        return decision
    i = CONSERVATIVE_ORDER.index(decision)
    return CONSERVATIVE_ORDER[min(i + 1, len(CONSERVATIVE_ORDER) - 1)]

def verify_and_harden(entity_group: EntityGroup, meta: Meta, decisions: List[Dict[str, Any]]) -> EntityGroup:
    """
    간단 휴리스틱 검증:
    - external + 특정 유형(PERSONAL_PHONE 등) 의 keep 금지 → 상향
    - 동일 유형인데 의사결정이 뒤섞이면 더 보수적인 쪽으로 통일(선택)
    """
    forbid_types = HEURISTICS.get("external_forbid_keep_types", set())
    
    # 1) 개별 엔티티 검증
    verified_entities = []
    for entity, decision in zip(entity_group.entities, decisions):
        masking = decision.get("decision", "keep")
        
        # External + 금지 유형은 강제 마스킹
        if meta.audience == "external" and masking == "keep" and entity.entity in forbid_types:
            masking = _lift("keep")
            
        # 마스킹 메타데이터 추가
        masked_entity = MaskingAction.apply_decision(
            entity=entity,
            decision=masking,
            format_options=decision.get("format", {})
        )
        verified_entities.append(masked_entity)

    # 2) 유형별 일관성 강제
    by_type: Dict[str, List[Entity]] = {}
    for entity in verified_entities:
        by_type.setdefault(entity.entity, []).append(entity)

    final_entities = []
    order = {k: i for i, k in enumerate(CONSERVATIVE_ORDER)}
    
    for etype, entities in by_type.items():
        # 동일 유형 중 가장 보수적인 마스킹 결정 찾기
        worst = max(
            (getattr(e, "masking_method", "keep") for e in entities),
            key=lambda x: order.get(x, len(CONSERVATIVE_ORDER)-1)
        )
        
        # 모든 동일 유형 엔티티에 적용
        for entity in entities:
            if (
                hasattr(entity, "masking_method") and
                order.get(entity.masking_method, 0) < order.get(worst, 0)
            ):
                entity.masking_method = worst  # type: ignore
            final_entities.append(entity)

    return EntityGroup(final_entities)

# ====== 5) 마스킹 명령으로 변환 ======
def to_mask_commands(spans: List[Span], decisions: List[PlanDecision]) -> List[Dict[str, Any]]:
    idx = {s.id: s for s in spans}
    cmds: List[Dict[str, Any]] = []
    for d in decisions:
        s = idx.get(d.id)
        if not s:
            continue
        cmd = {
            "span_id": s.id,
            "method": d.decision,
            "format": d.format,
            "page": s.page,
            "bbox": s.bbox,
            "start": s.start,
            "end": s.end,
            "citations": d.citations
        }
        # 기본 포맷 보강(휴리스틱)
        if d.decision == "mask_partial":
            defaults = HEURISTICS.get("partial_mask_defaults", {}).get(s.type)
            if defaults:
                # 사용자가 이미 지정 안 했으면 기본값 채우기
                for k, v in defaults.items():
                    cmd["format"].setdefault(k, v)
        cmds.append(cmd)
    return cmds

# ====== 6) 엔드투엔드 실행기 ======
def run(
    meta: Meta,
    entity_group: EntityGroup,
    get_context_pack: Callable[[List[str], Dict[str, Any]], ContextPack],
    complete_json: Optional[Callable[[str, Dict[str, Any]], List[Dict]]] = None,
    topk: int = 20
) -> EntityGroup:
    """
    외부에서:
      - get_context_pack(queries, filters) → ContextPack  (RAG 주입)
      - complete_json(prompt, schema) → List[Dict]       (LLM 주입; 미지정 시 Ollama 사용)
    반환:
      - 마스킹 결정이 포함된 새로운 EntityGroup
    """
    # 1) 쿼리/필터
    queries = []
    types = sorted({e.entity for e in entity_group.entities})
    for t in types:
        queries.append(f"{meta.jurisdiction} 관할에서 {meta.audience} 공개 시 {t} 제공 허용/금지 및 예외는?")
        queries.append(f"{t} 부분 마스킹 표준(자리수/구분자/가명/토큰화)은?")
    queries.append(f"{meta.purpose} 목적에서 최소 공개 원칙과 예외는?")
    queries = queries[:6]
    
    filters = {
        "source_order": select_source_order(meta.audience), 
        "jurisdiction": meta.jurisdiction
    }

    # 2) 컨텍스트 팩
    pack = get_context_pack(queries, filters)
    pack.chunks = rank_chunks(pack.chunks, meta)[:topk]

    # 3) 플래너
    if complete_json is None:
        force = os.getenv("FILTERING_LLM_FORCE_HEURISTIC", "0") == "1"
        if not force:
            try:
                # LLM을 통한 판단
                prompt = build_planner_prompt(meta, entity_group, pack)
                decisions = ollama_complete_json(prompt, PLANNER_JSON_SCHEMA, OLLAMA_MODEL)
                # 결과 검증 및 보강
                return verify_and_harden(entity_group, meta, decisions)
            except Exception as e:
                print(f"[info] Ollama JSON 응답 문제로 휴리스틱 폴백 사용: {e}")
                return verify_and_harden(entity_group, meta, heuristic_complete_json(prompt, PLANNER_JSON_SCHEMA))
        else:
            # 강제 휴리스틱 모드
            prompt = build_planner_prompt(meta, entity_group, pack)
            return verify_and_harden(entity_group, meta, heuristic_complete_json(prompt, PLANNER_JSON_SCHEMA))
    else:
        # 외부 제공 LLM 사용
        prompt = build_planner_prompt(meta, entity_group, pack)
        decisions = complete_json(prompt, PLANNER_JSON_SCHEMA)
        return verify_and_harden(entity_group, meta, decisions)
    """
    외부에서:
      - get_context_pack(queries, filters) → ContextPack  (RAG 주입)
      - complete_json(prompt, schema) → List[Dict]       (LLM 주입; 미지정 시 Ollama 사용)
    반환:
      - 마스킹 엔진이 이해할 공통 명령 리스트(List[Dict])
    """
    # 1) 쿼리/필터
    queries = build_closed_queries(meta, spans)
    filters = {"source_order": select_source_order(meta.audience), "jurisdiction": meta.jurisdiction}

    # 2) 컨텍스트 팩
    pack = get_context_pack(queries, filters)
    pack.chunks = rank_chunks(pack.chunks, meta)[:topk]

    # 3) 플래너
    if complete_json is None:
        force = os.getenv("FILTERING_LLM_FORCE_HEURISTIC", "0") == "1"
        if not force:
            try:
                decisions = plan(lambda p, s: ollama_complete_json(p, s, OLLAMA_MODEL), meta, spans, pack)
            except Exception as e:
                print(f"[info] Ollama JSON 응답 문제로 휴리스틱 폴백 사용: {e}")
                decisions = plan(heuristic_complete_json, meta, spans, pack)
        else:
            decisions = plan(heuristic_complete_json, meta, spans, pack)
    else:
        decisions = plan(complete_json, meta, spans, pack)

    # 4) 검증/보수적 상향
    decisions = verify_and_harden(decisions, meta, spans)

    # 5) 명령으로 변환
    return to_mask_commands(spans, decisions)

__all__ = [
    "run",
    "select_source_order", "build_closed_queries",
    "rank_chunks", "plan", "verify_and_harden",
    "to_mask_commands", "ollama_complete_json"
]
