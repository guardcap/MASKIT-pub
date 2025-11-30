import os
import json
import pickle
from collections import defaultdict
from konlpy.tag import Okt
from tqdm import tqdm
from rank_bm25 import BM25Okapi

# 💡 수정된 부분: 프로젝트 최상위 폴더 기준으로 retriever를 import 합니다.
from scripts.hybrid.retriever import GuardcapRetriever

# --- 설정 (Configuration) ---
STAGING_DIR = './data/staging'
BM25_INDEX_DIR = './data/staging/bm25'
CONFIG = {
    'A_cases.jsonl': {
        'id_field': 'case_id',
        'text_field': ['before_text', 'after_text'],
        'meta_fields': ['category', 'channel', 'task_type'],
        'CRITICAL_score_field': 'CRITICAL_score',
        'OPEN_score_field': 'OPEN_score'
    }
}

# 💡 삭제된 부분: 불필요한 중복 함수 정의를 제거했습니다.

# --- 스크립트 본문 ---
def main():
    print("✅ BM25 통합 인덱스 구축을 시작합니다...")
    os.makedirs(BM25_INDEX_DIR, exist_ok=True)
    
    print("Okt 형태소 분석기를 초기화합니다...")
    tokenizer = Okt()
    print("초기화 완료.")

    for doc_file, doc_config in CONFIG.items():
        filepath = os.path.join(STAGING_DIR, doc_file)
        if not os.path.exists(filepath):
            # 상대 경로가 프로젝트 루트에서 시작하도록 수정
            root_filepath = os.path.join('../..', filepath)
            if not os.path.exists(root_filepath):
                print(f"⚠️ 파일을 찾을 수 없습니다: {filepath} 또는 {root_filepath}")
                continue
            filepath = root_filepath

        print(f"\n📄 '{doc_file}' 파일 처리 중...")
        
        documents = []
        corpus = []
        
        # GuardcapRetriever 클래스에 정의된 정적 메서드를 사용 (이 부분은 올바르게 되어 있었습니다)
        meta_index = defaultdict(GuardcapRetriever._nested_defaultdict_factory)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for doc_idx, line in enumerate(f):
                    data = json.loads(line)
                    documents.append(data)
                    
                    text_values = [data.get(field, '') for field in doc_config['text_field']]
                    combined_text = " ".join(filter(None, text_values))
                    corpus.append(combined_text)
                    
                    for field in doc_config['meta_fields']:
                        if field in data and data[field] is not None:
                            value = data[field]
                            meta_index[field][value].append(doc_idx)
                    if doc_config['CRITICAL_score_field'] in data and data[doc_config['CRITICAL_score_field']] is not None:
                        meta_index['CRITICAL_score'][data[doc_config['CRITICAL_score_field']]].append(doc_idx)
                    if doc_config['OPEN_score_field'] in data and data[doc_config['OPEN_score_field']] is not None:
                        meta_index['OPEN_score'][data[doc_config['OPEN_score_field']]].append(doc_idx)
            
            print(f"  - {len(documents)}개 문서 로드 및 메타데이터 역색인 생성 완료.")
        except Exception as e:
            print(f"🚨 파일 처리 중 에러 발생: {e}")
            continue

        print("  - 텍스트 토큰화를 시작합니다...")
        tokenized_corpus = [tokenizer.morphs(doc) for doc in tqdm(corpus, desc="토큰화 진행")]
        
        print("  - BM25 인덱스를 생성합니다...")
        bm25 = BM25Okapi(tokenized_corpus)
        
        print("  - 통합 인덱스를 저장합니다...")
        index_data = {
            'bm25': bm25,
            'documents': documents,
            'meta_index': meta_index
        }
        
        index_filename = f"{doc_file.split('.')[0]}_bm25.pkl"
        index_path = os.path.join(BM25_INDEX_DIR, index_filename)
        
        with open(index_path, 'wb') as f:
            pickle.dump(index_data, f)
            
        print(f"  - 통합 인덱스가 성공적으로 저장되었습니다: {index_path}")

    print("\n🎉 BM25 통합 인덱스 구축 완료.")

if __name__ == '__main__':
    main()