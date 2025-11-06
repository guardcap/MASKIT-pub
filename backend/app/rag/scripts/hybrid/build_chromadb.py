import os
import json
import torch
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from collections import defaultdict

# --- 설정 (Configuration) ---

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '../..'))  # 상위 디렉토리로 이동
STAGING_DIR = os.path.join(ROOT_DIR, 'data', 'staging')
CHROMA_DB_DIR = os.path.join(STAGING_DIR, 'chroma_db')

MODEL_NAME = 'upskyy/e5-base-korean'


CONFIG = {
    'B_policies_hierarchical.jsonl': {
        'id_field': 'policy_id',
        'text_fields': ['hierarchical_text'],  # 계층적 텍스트 사용
        'meta_fields': ['entity_type','CRITICAL_score', 'OPEN_score'],
        'CRITICAL_score_field': 'CRITICAL_score',
        'OPEN_score_field': 'OPEN_score'
    },
    'C_laws_hierarchical.jsonl': {
        'id_field': 'law_id',
        'text_fields': ['hierarchical_text']  # 계층적 텍스트 사용
    }
}

def make_unique_ids(ids):
    """ID 리스트를 받아서 중복된 ID에 순번을 붙여 고유한 ID 리스트를 반환"""
    id_count = defaultdict(int)
    unique_ids = []
    
    for id_str in ids:
        id_count[id_str] += 1
        if id_count[id_str] > 1:
            unique_ids.append(f"{id_str}_{id_count[id_str]}")
        else:
            unique_ids.append(id_str)
            
    return unique_ids

def check_duplicate_ids(ids):
    """ID 리스트에서 중복된 ID들을 찾아 반환"""
    seen = set()
    duplicates = set(id_str for id_str in ids if id_str in seen or seen.add(id_str))
    return list(duplicates)

# --- 스크립트 본문 ---

def main():
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=CHROMA_DB_DIR,
        settings=Settings(anonymized_telemetry=False)
    )
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"임베딩 모델 '{MODEL_NAME}'을 로드합니다... (Device: {device})")
    model = SentenceTransformer(MODEL_NAME, device=device)

    for doc_file, doc_config in CONFIG.items():
        filepath = os.path.join(STAGING_DIR, doc_file)
        if not os.path.exists(filepath):
            print(f"err : {filepath} 파일을 찾을 수 없습니다.")
            continue

        print(f"\n'{doc_file}' 파일 처리 중...")
        
        try:
            documents = [json.loads(line) for line in open(filepath, 'r', encoding='utf-8')]
            if not documents:
                print(f"파일이 비어있어 건너뜁니다.")
                continue

            doc_texts = []
            for doc in documents:
                combined_parts = []
                for field in doc_config['text_fields']:
                    if field in doc and doc[field]:
                        content = doc[field]
                        if isinstance(content, list):
                            combined_parts.extend(content) # 리스트는 요소들을 추가
                        else:
                            combined_parts.append(str(content)) # 문자열은 그대로 추가
                # ". "으로 합쳐서 하나의 문장으로 만듬
                doc_texts.append(". ".join(part for part in combined_parts if part))

            original_ids = [str(doc[doc_config['id_field']]) for doc in documents]
            
            # 중복 ID 확인 및 처리
            duplicates = check_duplicate_ids(original_ids)
            if duplicates:
                print(f"  - {len(duplicates)}개의 중복 ID를 발견했습니다. 고유 ID로 변환합니다...")
                print(f"    중복 ID 예시: {', '.join(duplicates[:5])}{'...' if len(duplicates) > 5 else ''}")
                doc_ids = make_unique_ids(original_ids)
            else:
                doc_ids = original_ids
                
            # 메타데이터에서 모든 텍스트 필드를 제외
            doc_metadatas = []
            fields_to_exclude = doc_config['text_fields'] + [doc_config['id_field']]
            for doc in documents:
                meta = {k: v for k, v in doc.items() if k not in fields_to_exclude}
                # 원본 ID를 메타데이터에 저장
                meta['original_id'] = str(doc[doc_config['id_field']])
                for k, v in meta.items():
                    if not isinstance(v, (str, int, float, bool)):
                        meta[k] = str(v)
                doc_metadatas.append(meta)

            print(f"  - {len(documents)}개 문서에 대한 임베딩을 생성합니다...")
            embeddings = model.encode(
                doc_texts, 
                show_progress_bar=True, 
                batch_size=64
            )
            
            # Remove "_hierarchical" suffix from collection name
            collection_name = os.path.splitext(doc_file)[0].replace('_hierarchical', '')
            if collection_name in [c.name for c in client.list_collections()]:
                client.delete_collection(name=collection_name)
            
            collection = client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            collection.add(
                embeddings=embeddings.tolist(),
                documents=doc_texts, # 조합된 텍스트를 저장
                metadatas=doc_metadatas,
                ids=doc_ids
            )
            print(f"  - ✅ '{collection_name}' 컬렉션에 {len(doc_ids)}개 문서 저장 완료.")
            
        except KeyError as e:
            print(f"err: JSON 데이터에 '{e}' 필드가 없습니다. CONFIG나 데이터 파일을 확인하세요.")
        except Exception as e:
            print(f"err: {e}")
            import traceback
            traceback.print_exc()

    print("\nChromaDB 인덱스 구축 전체 완료.")
    print(f"   - DB 위치: {CHROMA_DB_DIR}")

if __name__ == '__main__':
    main()