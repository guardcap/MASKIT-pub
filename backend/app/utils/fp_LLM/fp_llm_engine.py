# fp_llm_engine.py
from app.utils.fp_LLM.pre import pre_filter
from app.utils.fp_LLM.llm import llm_check
from typing import List, Dict

def process_entities(sentence: str, entities: List[Dict]) -> List[Dict]:
    print(f"\n[PROCESS] Sentence: {sentence}")
    print(f"[INPUT] Entities: {entities}")

    llm_targets = pre_filter(entities)
    print(f"[Pre-filter] LLM Targets: {[t[0] for t in llm_targets]}")

    results = []
    for text, ent_list in llm_targets:
        result = llm_check(text, sentence, ent_list)
        results.append({
            "text": text,
            "selected_entity": result["selected_entity"],
            "candidates": result["candidate_types"]
        })

    return results
