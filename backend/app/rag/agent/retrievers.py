"""
개선된 Hybrid Retriever
- 애플리케이션 가이드 우선 검색
- BM25 + Vector 하이브리드 검색
- 계층적 청킹을 고려한 검색
"""
import os
import json
import pickle
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from konlpy.tag import Okt
from rank_bm25 import BM25Okapi
import torch
from typing import List, Dict, Any, Optional
from collections import defaultdict


class HybridRetriever:
    """하이브리드 검색기 - BM25 + Vector Search"""

    def __init__(self, index_base_path='./data/staging'):
        print("✅ Hybrid Retriever 초기화 중...")
        self.index_base_path = index_base_path
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # 임베딩 모델 및 토크나이저
        self.model = SentenceTransformer('upskyy/e5-base-korean', device=device)
        self.tokenizer = Okt()

        # ChromaDB 클라이언트
        chroma_db_path = os.path.join(index_base_path, 'chroma_db')
        self.client = chromadb.PersistentClient(
            path=chroma_db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Application Guides 로드 (JSONL)
        self.guides = []
        self.guides_corpus = []
        self.guides_bm25 = None
        self._load_application_guides()

        # A_cases BM25 인덱스 로드
        self.bm25_A = None
        self.documents_A = []
        self.meta_index_A = {}
        self._load_a_cases_index()

        print("🎉 Hybrid Retriever 초기화 완료.")

    def _load_application_guides(self):
        """애플리케이션 가이드 로드 및 BM25 인덱스 생성"""
        guides_path = os.path.join(self.index_base_path, 'application_guides.jsonl')

        if not os.path.exists(guides_path):
            print(f"⚠️ 애플리케이션 가이드를 찾을 수 없습니다: {guides_path}")
            return

        try:
            with open(guides_path, 'r', encoding='utf-8') as f:
                for line in f:
                    guide = json.loads(line.strip())
                    self.guides.append(guide)

                    # 검색용 텍스트 생성: scenario + interpretation + keywords
                    search_text = f"{guide['scenario']} {guide['interpretation']} {' '.join(guide['keywords'])}"
                    self.guides_corpus.append(search_text)

            # BM25 인덱스 생성
            if self.guides_corpus:
                tokenized_corpus = [self.tokenizer.morphs(text) for text in self.guides_corpus]
                self.guides_bm25 = BM25Okapi(tokenized_corpus)
                print(f"   - 애플리케이션 가이드 {len(self.guides)}개 로드 및 BM25 인덱스 생성 완료.")
        except Exception as e:
            print(f"   - 🚨 애플리케이션 가이드 로드 실패: {e}")

    def _load_a_cases_index(self):
        """A_cases BM25 인덱스 로드"""
        index_path = os.path.join(self.index_base_path, 'bm25/A_cases_bm25.pkl')
        try:
            with open(index_path, 'rb') as f:
                data = pickle.load(f)
                self.bm25_A = data['bm25']
                self.documents_A = data['documents']
                self.meta_index_A = data['meta_index']
            print(f"   - A_cases 인덱스 로드 완료 ({len(self.documents_A)}개 문서).")
        except FileNotFoundError:
            print(f"   - ⚠️ A_cases BM25 인덱스를 찾을 수 없습니다: {index_path}")
        except Exception as e:
            print(f"   - 🚨 A_cases 인덱스 로드 실패: {e}")

    def search_application_guides(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        애플리케이션 가이드 검색 (최우선)
        - BM25와 Vector 검색을 결합한 하이브리드 검색
        """
        if not self.guides:
            return []

        results = []

        # 1. BM25 검색
        bm25_scores = {}
        if self.guides_bm25 and use_hybrid:
            tokenized_query = self.tokenizer.morphs(query)
            bm25_raw_scores = self.guides_bm25.get_scores(tokenized_query)
            bm25_scores = {i: score for i, score in enumerate(bm25_raw_scores)}

        # 2. Vector 검색 (의미 기반)
        query_embedding = self.model.encode(query)
        guide_embeddings = self.model.encode(self.guides_corpus)

        # 코사인 유사도 계산
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        vector_scores = cosine_similarity([query_embedding], guide_embeddings)[0]

        # 3. 하이브리드 스코어 계산 (RRF - Reciprocal Rank Fusion 간소화 버전)
        combined_scores = {}
        for i in range(len(self.guides)):
            bm25_score = bm25_scores.get(i, 0) if use_hybrid else 0
            vector_score = vector_scores[i]

            # 가중치 조합 (Vector에 더 높은 가중치)
            combined_scores[i] = 0.3 * bm25_score + 0.7 * vector_score

            # Context 필터링 (옵션)
            if context:
                guide = self.guides[i]
                guide_context = guide.get('context', {})

                # 발신자/수신자 타입 일치 시 보너스
                if context.get('sender_type') == guide_context.get('sender_type'):
                    combined_scores[i] *= 1.2
                if context.get('receiver_type') == guide_context.get('receiver_type'):
                    combined_scores[i] *= 1.2

        # 4. 상위 K개 선택
        sorted_indices = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)[:top_k]

        for idx in sorted_indices:
            results.append({
                'guide_id': self.guides[idx]['guide_id'],
                'score': combined_scores[idx],
                'source': 'application_guides',
                'content': self.guides[idx],
                'metadata': {
                    'scenario': self.guides[idx]['scenario'],
                    'actionable_directive': self.guides[idx]['actionable_directive']
                }
            })

        return results

    def search_laws_and_policies(self, query: str, top_k: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        법률 및 정책 검색 (Vector Search)
        """
        results = {'laws': [], 'policies': []}

        try:
            query_embedding = self.model.encode(query).tolist()

            # C_laws 검색
            try:
                collection_laws = self.client.get_collection('C_laws')
                laws_results = collection_laws.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["metadatas", "documents", "distances"]
                )

                for i, doc_id in enumerate(laws_results['ids'][0]):
                    results['laws'].append({
                        'id': doc_id,
                        'score': 1 - laws_results['distances'][0][i],
                        'source': 'C_laws',
                        'content': laws_results['documents'][0][i],
                        'metadata': laws_results['metadatas'][0][i]
                    })
            except Exception as e:
                print(f"⚠️ C_laws 검색 실패: {e}")

            # B_policies 검색
            try:
                collection_policies = self.client.get_collection('B_policies')
                policies_results = collection_policies.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["metadatas", "documents", "distances"]
                )

                for i, doc_id in enumerate(policies_results['ids'][0]):
                    results['policies'].append({
                        'id': doc_id,
                        'score': 1 - policies_results['distances'][0][i],
                        'source': 'B_policies',
                        'content': policies_results['documents'][0][i],
                        'metadata': policies_results['metadatas'][0][i]
                    })
            except Exception as e:
                print(f"⚠️ B_policies 검색 실패: {e}")

        except Exception as e:
            print(f"🚨 법률/정책 검색 실패: {e}")

        return results

    def search_cases(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        A_cases 검색 (BM25 with metadata filtering)
        """
        if not self.bm25_A:
            return []

        # 필터링
        candidate_indices = set(range(len(self.documents_A)))
        if filters:
            for field, value in filters.items():
                if field in self.meta_index_A and value in self.meta_index_A[field]:
                    candidate_indices.intersection_update(self.meta_index_A[field][value])
                else:
                    return []

        if not candidate_indices:
            return []

        # BM25 검색
        tokenized_query = self.tokenizer.morphs(query)
        doc_scores = self.bm25_A.get_scores(tokenized_query)

        candidate_scores = {idx: doc_scores[idx] for idx in candidate_indices}
        sorted_indices = sorted(candidate_scores, key=candidate_scores.get, reverse=True)[:top_k]

        results = []
        for idx in sorted_indices:
            doc = self.documents_A[idx]
            results.append({
                'id': doc.get('case_id', 'N/A'),
                'score': candidate_scores[idx],
                'source': 'A_cases',
                'content': doc.get('before_text', '') + ' -> ' + doc.get('after_text', ''),
                'metadata': doc
            })

        return results
