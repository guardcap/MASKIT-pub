import torch
from sentence_transformers import SentenceTransformer, util
import numpy as np
import pandas as pd
import json

# --- 1. 데이터 로드 및 전처리 함수들 ---

def load_A_cases(filepath="../data/seed/A_cases.csv"):
    """A_cases.csv를 로드하여 쿼리와 코퍼스 문서 생성"""
    df = pd.read_csv(filepath)
    queries, corpus_docs, entities = [], [], []
    for _, row in df.iterrows():
        try:
            entity_type_str = json.loads(row["entity_rules"])[0]['entity_type']
        except:
            entity_type_str = "개인정보"
            
        queries.append(f'{row["category"]} {row["channel"]} 채널의 "{row["task_type"]}" 작업에서 {entity_type_str} 처리 방법')
        corpus_docs.append(
            f'처리 사례 ID: {row["case_id"]}. 상황: {row["category"]}/{row["channel"]}/{row["task_type"]}. 원본 텍스트: "{row["before_text"]}". 적용 규칙: {row["entity_rules"]}'
        )
        entities.append(entity_type_str)
    return queries, corpus_docs, entities, df

def load_B_policies(filepath="../data/seed/B_cases.csv"):
    """B_cases.csv(정책)를 로드하여 코퍼스 문서 생성"""
    df = pd.read_csv(filepath)
    corpus_docs, entities = [], []
    for _, row in df.iterrows():
        paraphrases = " ".join(json.loads(row.get("paraphrases", "[]")))
        corpus_docs.append(f'내부 정책: {row["statement"]} 유사 표현: {paraphrases}')
        entities.append(row["entity_type"])
    return corpus_docs, entities, df

def load_C_laws(filepath="../data/seed/C_laws.csv"):
    """C_laws.csv(법률)를 로드하여 코퍼스 문서 생성"""
    df = pd.read_csv(filepath)
    corpus_docs, entities = [], []
    for _, row in df.iterrows():
        entity_types_str = " ".join(json.loads(row.get("entity_types", "[]")))
        corpus_docs.append(f'법적 근거: {row["title"]} ({row["snippet"]}) 관련 엔티티: {entity_types_str}')
        entities.append(json.loads(row.get("entity_types", "[]")))
    return corpus_docs, entities, df
    
# --- 2. 모델 평가 함수 ---

# model_name 파라미터를 받도록 수정된 함수
def evaluate_scenario(model, model_name, scenario_name, queries, corpus_docs, relevant_docs_map):
    """주어진 시나리오에 대해 모델 성능을 평가"""
    print(f"\n--- Running Scenario: {scenario_name} ---")
    
    # model.model_name_or_path 대신 전달받은 model_name 사용
    queries_with_prefix = [f"query: {q}" for q in queries] if "e5" in model_name else queries
    query_embeddings = model.encode(queries_with_prefix, convert_to_tensor=True, show_progress_bar=True)
    corpus_embeddings = model.encode(corpus_docs, convert_to_tensor=True, show_progress_bar=True)

    search_results = util.semantic_search(query_embeddings, corpus_embeddings, top_k=20)
    
    reciprocal_ranks, recall_at_1, recall_at_5 = [], 0, 0
    for i in range(len(queries)):
        true_answer_corpus_ids = relevant_docs_map.get(i, [])
        if not true_answer_corpus_ids: continue

        result_ids = [hit['corpus_id'] for hit in search_results[i]]
        
        found_ranks = [result_ids.index(ans_id) + 1 for ans_id in true_answer_corpus_ids if ans_id in result_ids]
        if not found_ranks:
            reciprocal_ranks.append(0)
            continue
            
        best_rank = min(found_ranks)
        reciprocal_ranks.append(1 / best_rank)
        if best_rank <= 1: recall_at_1 += 1
        if best_rank <= 5: recall_at_5 += 1

    query_count_with_answers = sum(1 for i in range(len(queries)) if i in relevant_docs_map and relevant_docs_map[i])
    if query_count_with_answers == 0: return {"scenario": scenario_name, "MRR": 0, "Recall@1": 0, "Recall@5": 0}

    return {
        "scenario": scenario_name,
        "MRR": np.mean(reciprocal_ranks),
        "Recall@1": recall_at_1 / query_count_with_answers,
        "Recall@5": recall_at_5 / query_count_with_answers
    }

# --- 3. 메인 실행 로직 ---
if __name__ == "__main__":
    a_queries, a_corpus, a_entities, _ = load_A_cases()
    b_corpus, b_entities, _ = load_B_policies()
    c_corpus, c_entities_list, _ = load_C_laws()

    relevant_A_to_A = {i: [i] for i in range(len(a_queries))}
    relevant_A_to_B = {i: [j for j, b_entity in enumerate(b_entities) if a_entities[i] == b_entity] for i in range(len(a_queries))}
    relevant_A_to_C = {i: [j for j, c_entity_list in enumerate(c_entities_list) if a_entities[i] in c_entity_list] for i in range(len(a_queries))}

    models_to_test = [
        "jhgan/ko-sroberta-multitask",
        "snunlp/KR-SBERT-V40K-klueNLI-augSTS",
        "upskyy/e5-base-korean",
    ]
    
    final_results = []
    device = "cuda" if torch.cuda.is_available() else "cpu"

    for model_name in models_to_test:
        print(f"\n{'='*20}\nEvaluating Model: {model_name}\n{'='*20}")
        model = SentenceTransformer(model_name, device=device)
        model_results = {"model": model_name}
        
        scenarios = [
            ("Case-to-Case (A->A)", a_queries, a_corpus, relevant_A_to_A),
            ("Case-to-Policy (A->B)", a_queries, b_corpus, relevant_A_to_B),
            ("Case-to-Law (A->C)", a_queries, c_corpus, relevant_A_to_C),
        ]
        
        for name, queries, corpus, rel_docs in scenarios:
            try:
                # 함수 호출 시 model_name 전달
                eval_res = evaluate_scenario(model, model_name, name, queries, corpus, rel_docs)
                model_results.update({f"{name}_MRR": eval_res["MRR"], f"{name}_R@5": eval_res["Recall@5"]})
            except Exception as e:
                print(f"Error in scenario {name}: {e}")
                model_results.update({f"{name}_MRR": 0, f"{name}_R@5": 0})
        
        final_results.append(model_results)

    results_df = pd.DataFrame(final_results)
    print("\n\n--- Final Comprehensive Evaluation Results ---")
    print(results_df.round(4).to_string(index=False))