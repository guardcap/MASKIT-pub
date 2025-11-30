import argparse
import json
import pickle
from sentence_transformers import SentenceTransformer, util
from difflib import SequenceMatcher
import os

def is_match(answer, text, threshold=0.7):
    if answer in text:
        return True
    ratio = SequenceMatcher(None, answer, text).ratio()
    return ratio >= threshold

def evaluate(args):
    model = SentenceTransformer(args.embedding)

    # chunks.pkl 경로 결정
    chunks_path = args.chunks
    if args.vectorstore:  # vectorstore 디렉토리 있으면 그 안에서 chunks.pkl 찾기
        candidate = os.path.join(args.vectorstore, "chunks_tagged.pkl")
        if os.path.exists(candidate):
            chunks_path = candidate

    with open(chunks_path, "rb") as f:
        chunk_docs = pickle.load(f)

    corpus = [doc.page_content for doc in chunk_docs]
    corpus_embeddings = model.encode(corpus, convert_to_tensor=True, normalize_embeddings=True)

    with open(args.queries, "r", encoding="utf-8") as f:
        queries = json.load(f)

    correct = 0
    total = len(queries)

    for q in queries:
        query, answer = q["query"], q["answer"]
        q_emb = model.encode(query, convert_to_tensor=True, normalize_embeddings=True)
        hits = util.semantic_search(q_emb, corpus_embeddings, top_k=3)[0]
        retrieved = [corpus[hit["corpus_id"]] for hit in hits]
        matched = any(is_match(answer, chunk) for chunk in retrieved)
        if matched:
            correct += 1

    recall_at3 = correct / total if total > 0 else 0
    print(f"📊 Recall@3: {recall_at3:.2f}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data/policy.md")
    parser.add_argument("--embedding", type=str, default="upskyy/e5-base-korean")
    parser.add_argument("--queries", type=str, default="test/data/queries.json")
    parser.add_argument("--chunks", type=str, default="chunks_tagged.pkl")
    parser.add_argument("--vectorstore", type=str, default=None)  # 🔥 추가
    args = parser.parse_args()
    evaluate(args)

if __name__ == "__main__":
    main()
