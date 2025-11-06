import sys
import os
import unittest

# ❗ [수정] OpenMP 라이브러리 중복 로딩으로 인한 충돌 방지
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# 상위 디렉터리의 모듈을 가져올 수 있도록 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from retriever_chromadb import HybridRetrieverChromaDB

class TestHybridRetrieverChromaDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """테스트 시작 전, 전체 테스트에 사용될 Retriever를 한 번만 초기화합니다."""
        print("\n" + "="*50)
        print("ChromaDB HybridRetriever 초기화를 시작합니다. 시간이 다소 걸릴 수 있습니다...")
        
        # 프로젝트 루트 디렉터리 기준으로 'data/staging'을 가리키도록 경로 수정
        index_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'staging'))
        
        # 테스트 실행 전, 인덱스 파일들이 존재하는지 확인
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"테스트를 위한 인덱스 경로를 찾을 수 없습니다: {index_path}\n"
                                  "먼저 데이터 준비 및 인덱스 빌드 스크립트를 실행해주세요.")

        cls.retriever = HybridRetrieverChromaDB(index_base_path=index_path)
        print("ChromaDB Retriever 초기화 완료.")
        print("="*50)

    def test_retrieval_performance(self):
        """
        정의된 테스트 쿼리들을 실행하고 결과를 확인합니다.
        """
        # --- 테스트할 쿼리 목록 ---
        test_queries = {
            "case_query": "마케팅 이메일 발송 시 개인정보 처리 방법",
            "policy_query": "외부 협력사와 데이터 공유 규정",
            "law_query": "개인정보 파기 절차에 대한 법적 근거",
            "specific_entity_query": "주민등록번호 마스킹 처리 사례",
            "vague_query": "정보 유출"
        }

        for name, query in test_queries.items():
            with self.subTest(name=name, query=query):
                print(f"\n--- [테스트] {name}: '{query}' ---")
                
                # Retriever를 사용해 검색 실행
                results = self.retriever.retrieve(query, top_k=5)
                
                # 결과가 비어있지 않은지 확인
                self.assertTrue(results, msg=f"'{query}'에 대한 검색 결과가 없습니다.")
                
                print(f"✅ 상위 {len(results)}개 결과:")
                for doc_id, score in results:
                    print(f"  - Doc ID: {doc_id:<35} | Score: {score:.4f}")
                    
                    # 원본 문서 내용도 출력
                    doc = self.retriever.get_document_by_id(doc_id)
                    if doc:
                        text_preview = doc.get('text_column', 'N/A')[:80]
                        print(f"    내용: {text_preview}...")
                
                # 최소 1개 이상의 결과가 있는지 단언(assert)
                self.assertGreater(len(results), 0)

    def test_document_retrieval(self):
        """문서 ID로 개별 문서 조회 테스트"""
        print("\n--- [테스트] 문서 ID로 개별 문서 조회 ---")
        
        # 첫 번째 검색 결과에서 문서 ID 가져오기
        results = self.retriever.retrieve("개인정보", top_k=1)
        if results:
            doc_id = results[0][0]
            doc = self.retriever.get_document_by_id(doc_id)
            
            self.assertIsNotNone(doc, f"문서 ID '{doc_id}'에 대한 문서를 찾을 수 없습니다.")
            self.assertIn('text_column', doc, "문서에 'text_column' 필드가 없습니다.")
            self.assertIn('id_column', doc, "문서에 'id_column' 필드가 없습니다.")
            
            print(f"✅ 문서 조회 성공: {doc_id}")
            print(f"   내용: {doc.get('text_column', 'N/A')[:100]}...")
        else:
            self.fail("검색 결과가 없어 문서 조회 테스트를 수행할 수 없습니다.")

# 이 파일을 직접 실행할 경우 unittest를 실행합니다.
if __name__ == '__main__':
    unittest.main()
