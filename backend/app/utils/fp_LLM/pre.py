# pre.py
from typing import List, Dict, Any, Tuple

Entity = Dict[str, Any]

def pre_filter(entities: List[Entity], low_score_threshold=0.6) -> List[Tuple[str, List[Entity]]]:
    """
    점수 낮거나 동일 텍스트에서 여러 엔티티 타입 검출된 경우 → LLM 검사 대상으로 분류
    반환 형식: (text, 관련 엔티티 목록)
    """
    text_to_entities = {}
    llm_targets = []

    for ent in entities:
        text = ent["text"]
        score = ent.get("score", 1.0)

        if text not in text_to_entities:
            text_to_entities[text] = []
        text_to_entities[text].append(ent)

    for text, ents in text_to_entities.items():
        types = {e["type"] for e in ents}
        low_score_exists = any(e.get("score", 1.0) < low_score_threshold for e in ents)
        if len(types) > 1 or low_score_exists:
            llm_targets.append((text, ents))

    return llm_targets
