"""
Application Guides VectorDB 빌드
ChromaDB + OpenAI Embeddings
"""

import json
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import os
from tqdm import tqdm
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class GuidesVectorDBBuilder:
    """Application Guides VectorDB 빌더"""

    def __init__(
        self,
        openai_api_key: str = None,
        db_path: str = "data/chromadb/application_guides",
        collection_name: str = "application_guides"
    ):
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or .env file")

        self.client = OpenAI(api_key=api_key)
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.db_path = Path(db_path)
        self.collection_name = collection_name

        # ChromaDB 초기화
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.db_path)
        )

        # 기존 컬렉션 삭제 후 재생성
        try:
            self.chroma_client.delete_collection(name=collection_name)
            print(f"🗑️  Deleted existing collection: {collection_name}")
        except:
            pass

        self.collection = self.chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def load_guides(self, jsonl_path: str) -> List[Dict]:
        """단일 JSONL 파일 로드"""
        guides = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():  # 빈 줄 무시
                    guides.append(json.loads(line))
        return guides

    def load_all_guides_from_directory(self, directory: str, pattern: str = "application_guides_*_unique.jsonl") -> List[Dict]:
        """
        디렉토리에서 패턴에 맞는 모든 JSONL 파일 로드

        Args:
            directory: 검색할 디렉토리
            pattern: 파일명 패턴 (glob)

        Returns:
            모든 파일의 가이드를 합친 리스트
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []

        all_guides = []
        jsonl_files = sorted(dir_path.glob(pattern))

        if not jsonl_files:
            # Fallback: 모든 application_guides_*.jsonl 파일 (review 제외)
            jsonl_files = [
                f for f in sorted(dir_path.glob("application_guides_*.jsonl"))
                if "review" not in f.name.lower()
            ]

        print(f"📂 Found {len(jsonl_files)} guide files in {directory}")

        for jsonl_file in jsonl_files:
            print(f"  - Loading: {jsonl_file.name}")
            guides = self.load_guides(str(jsonl_file))
            all_guides.extend(guides)
            print(f"    → {len(guides)} guides")

        return all_guides

    def get_embedding(self, text: str) -> List[float]:
        """OpenAI Embedding 생성"""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    def build_search_text(self, guide: Dict) -> str:
        """검색용 텍스트 구성"""
        parts = [
            f"Scenario: {guide.get('scenario', '')}",
            f"Directive: {guide.get('actionable_directive', '')}",
            f"Interpretation: {guide.get('interpretation', '')}",
            f"Keywords: {', '.join(guide.get('keywords', []))}",
        ]

        # 예시 추가
        for example in guide.get('examples', []):
            parts.append(f"Example: {example.get('case_description', '')}")

        return "\n".join(parts)

    def build_metadata(self, guide: Dict) -> Dict:
        """메타데이터 구성"""
        context = guide.get('context', {}) or {}

        return {
            "guide_id": guide.get("guide_id", ""),
            "authority": guide.get("source_authority", ""),
            "source_document": guide.get("source_document", ""),
            "scenario": guide.get("scenario", "")[:500],  # 길이 제한
            "sender_type": context.get("sender_type", ""),
            "receiver_type": context.get("receiver_type", ""),
            "email_purpose": context.get("email_purpose", ""),
            "pii_types": ",".join(context.get("pii_types", [])),
            "publish_date": guide.get("publish_date", ""),
            "confidence_score": str(guide.get("confidence_score", 0.8)),
            "reviewed": str(guide.get("reviewed", False)),
        }

    def add_guides_to_db(self, guides: List[Dict], batch_size: int = 100):
        """가이드를 VectorDB에 추가"""
        print(f"\n📊 Adding {len(guides)} guides to ChromaDB...")

        # 배치 처리
        for i in tqdm(range(0, len(guides), batch_size), desc="Building VectorDB"):
            batch = guides[i:i + batch_size]

            ids = []
            documents = []
            embeddings = []
            metadatas = []

            for guide in batch:
                guide_id = guide.get("guide_id")
                if not guide_id:
                    continue

                # 검색 텍스트
                search_text = self.build_search_text(guide)

                # Embedding 생성
                embedding = self.get_embedding(search_text)

                # 메타데이터
                metadata = self.build_metadata(guide)

                ids.append(guide_id)
                documents.append(search_text)
                embeddings.append(embedding)
                metadatas.append(metadata)

            # ChromaDB에 추가
            if ids:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )

        print(f"✅ Successfully added {len(guides)} guides to VectorDB")

    def test_search(self, query: str, top_k: int = 3):
        """검색 테스트"""
        print(f"\n🔍 Testing search: '{query}'")

        # 쿼리 임베딩
        query_embedding = self.get_embedding(query)

        # 검색
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        # 결과 출력
        for i, (doc, meta, dist) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"\n--- Result {i+1} (distance: {dist:.4f}) ---")
            print(f"Guide ID: {meta.get('guide_id')}")
            print(f"Scenario: {meta.get('scenario')}")
            print(f"Authority: {meta.get('authority')}")
            print(f"Document: {doc[:200]}...")

    def get_stats(self) -> Dict:
        """VectorDB 통계"""
        count = self.collection.count()

        return {
            "total_guides": count,
            "collection_name": self.collection_name,
            "db_path": str(self.db_path),
        }


def main():
    """메인 실행"""

    # 빌더 초기화 (.env에서 자동 로드)
    try:
        builder = GuidesVectorDBBuilder(
            db_path="guardcap-rag/data/chromadb/application_guides",
            collection_name="application_guides"
        )
        print(f"✅ Using embedding model: {builder.embedding_model}")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease ensure:")
        print("1. .env file exists in the project root")
        print("2. OPENAI_API_KEY is set in .env")
        return

    # staging 디렉토리의 모든 unique 가이드 로드
    staging_dirs = [
        "guardcap-rag/data/staging",
        "data/staging"
    ]

    guides = []
    for staging_dir in staging_dirs:
        if Path(staging_dir).exists():
            guides = builder.load_all_guides_from_directory(
                staging_dir,
                pattern="application_guides_*_unique.jsonl"
            )
            if guides:
                print(f"\n📊 Total loaded: {len(guides)} guides")
                break

    if not guides:
        print("❌ No guide files found in staging directory!")
        print("\nPlease run:")
        print("  1. process_guidelines.py - to generate guides")
        print("  2. validate_and_dedup.py - to create unique guides")
        return

    # VectorDB 빌드
    builder.add_guides_to_db(guides, batch_size=50)

    # 통계
    stats = builder.get_stats()
    print(f"\n📊 VectorDB Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 검색 테스트
    test_queries = [
        "고객이 먼저 문의한 경우 개인정보 마스킹",
        "이메일 주소 수집 동의",
        "마케팅 목적 개인정보 활용",
    ]

    for query in test_queries:
        builder.test_search(query, top_k=2)

    print("\n✨ VectorDB build complete!")
    print(f"📍 Location: {builder.db_path}")


if __name__ == "__main__":
    main()
