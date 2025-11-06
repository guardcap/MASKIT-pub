import os
import json
import pickle
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from konlpy.tag import Okt
import torch
import numpy as np
from collections import defaultdict

class GuardcapRetriever:
    """
    Guardcap 프로젝트의 검색 요구사항에 맞춰 특수화된 검색기.
    - A(사례): 메타데이터 필터링이 적용된 BM25 검색
    - B(규정), C(법률): 순수 벡터 검색
    """

    @staticmethod
    def _nested_defaultdict_factory():
        return defaultdict(list)
    
    def __init__(self, index_base_path='./data/staging'):
        print("✅ Guardcap 검색기 초기화 중...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   - 사용할 디바이스: {device}")

        # 1. 임베딩 모델 및 토크나이저 초기화
        self.model = SentenceTransformer('upskyy/e5-base-korean', device=device)
        self.tokenizer = Okt()
        print("   - 임베딩 모델 및 Okt 토크나이저 로드 완료.")

        # 2. ChromaDB 클라이언트 초기화
        chroma_db_path = os.path.join(index_base_path, 'chroma_db')
        self.client = chromadb.PersistentClient(
            path=chroma_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        print("   - ChromaDB 클라이언트 초기화 완료.")
        
        # 3. A(사례) 데이터 및 BM25 인덱스 로드
        self.bm25_model_A = None
        self.documents_A = []
        self.meta_index_A = {}
        self._load_a_cases_index(index_base_path)
        print("🎉 검색기 초기화 완료.")

    def _load_a_cases_index(self, index_base_path):
        """A_cases의 통합 인덱스 파일(.pkl)을 로드합니다."""
        index_path = os.path.join(index_base_path, 'bm25/A_cases_bm25.pkl')
        try:
            with open(index_path, 'rb') as f:
                data = pickle.load(f)
                self.bm25_model_A = data['bm25']
                self.documents_A = data['documents']
                self.meta_index_A = data['meta_index']
            print(f"   - A_cases 통합 인덱스 로드 완료 ({len(self.documents_A)}개 문서).")
        except FileNotFoundError:
            print(f"   - ⚠️ 경고: A_cases BM25 인덱스를 찾을 수 없습니다: {index_path}")
        except Exception as e:
            print(f"   - 🚨 에러: A_cases 인덱스 로드 실패: {e}")

    # scripts/hybrid/retriever.py 파일 내부

    def search_A_cases(self, query: str, filters: dict = None, top_k: int = 3) -> list:
        """
        A(사례)에 대해 메타데이터 필터링 후 BM25 검색을 수행합니다.
        """
        if not self.bm25_model_A:
            print("경고: A_cases BM25 인덱스가 로드되지 않아 검색을 건너뜁니다.")
            return []

        # 1. 필터링을 통해 검색 대상 문서 ID 목록(후보군) 선정
        candidate_indices = set(range(len(self.documents_A)))
        if filters:
            for field, value in filters.items():
                if field in self.meta_index_A and value in self.meta_index_A[field]:
                    candidate_indices.intersection_update(self.meta_index_A[field][value])
                else:
                    return []
        
        if not candidate_indices:
            return []

        # 2. BM25 검색 (후보군 내에서만)
        tokenized_query = self.tokenizer.morphs(query)
        doc_scores = self.bm25_model_A.get_scores(tokenized_query)
        
        candidate_scores = {idx: doc_scores[idx] for idx in candidate_indices}

        # 3. 점수 기준으로 상위 K개 정렬
        sorted_indices = sorted(candidate_scores, key=candidate_scores.get, reverse=True)[:top_k]
        
        # 4. 결과 포맷팅
        results = []
        for idx in sorted_indices:
            doc = self.documents_A[idx]
            results.append({
                "id": doc.get('case_id', 'N/A'),
                "score": candidate_scores[idx],
                "source": "A_cases",
                # ✨ 여기가 수정된 부분입니다.
                "snippet": (doc.get('before_text') or doc.get('after_text') or '')[:200],
                "meta": doc
            })
        return results

    def _search_vector_db(self, collection_name: str, query: str, top_k: int = 8) -> list:
        """ChromaDB 컬렉션에서 벡터 검색을 수행하는 내부 메서드."""
        try:
            collection = self.client.get_collection(collection_name)
            query_embedding = self.model.encode(query).tolist()
            
            results_raw = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["metadatas", "documents", "distances"]
            )

            # 결과 포맷팅
            results = []
            ids = results_raw['ids'][0]
            for i, doc_id in enumerate(ids):
                distance = results_raw['distances'][0][i]
                results.append({
                    "id": doc_id,
                    "score": 1 - distance,  # 코사인 거리(0~2)를 유사도(0~1)로 변환
                    "source": collection_name,
                    "snippet": results_raw['documents'][0][i],
                    "meta": results_raw['metadatas'][0][i]
                })
            return results

        except Exception as e:
            # list_collections() 결과가 비어있을 때 발생하는 ValueError 포함
            print(f"경고: ChromaDB '{collection_name}' 컬렉션 검색 중 오류: {e}")
            return []

    def search_B_policies(self, query: str, top_k: int = 8) -> list:
        """B(규정)에 대해 벡터 검색을 수행합니다."""
        return self._search_vector_db('B_policies', query, top_k)

    def search_C_laws(self, query: str, top_k: int = 8) -> list:
        """C(법률)에 대해 벡터 검색을 수행합니다."""
        return self._search_vector_db('C_laws', query, top_k)


# --- 사용 예시 ---
if __name__ == '__main__':
    retriever = GuardcapRetriever()
    print("\n--- 검색 시나리오 테스트 ---")

    # 1. A(사례) 검색: 필터링 적용
    print("\n[A] '파트너 포털'에서 '좌표' 유출 사례 검색 (필터 적용)")
    query_a = "파트너 포털에서 현장 좌표가 유출됨"
    filters_a = {'category': '사외', 'channel': 'WEB'}
    results_a = retriever.search_A_cases(query_a, filters=filters_a, top_k=3)
    if results_a:
        for res in results_a:
            print(f"  - ID: {res['id']}, Score: {res['score']:.4f}, Snippet: {res['snippet'][:50]}...")
    else:
        print("  - 검색 결과 없음")

    # 2. B(규정) 검색: 순수 벡터 검색
    print("\n[B] '주소 공개' 관련 규정 검색")
    query_b = "외부 파트너에게 주소를 공개해도 되나요?"
    results_b = retriever.search_B_policies(query_b, top_k=5)
    if results_b:
        for res in results_b:
            print(f"  - ID: {res['id']}, Score: {res['score']:.4f}, Snippet: {res['snippet'][:50]}...")
    else:
        print("  - 검색 결과 없음")