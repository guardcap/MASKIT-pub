"""
가이드라인 검증 및 중복 제거 유틸리티
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
import os
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class GuideValidator:
    """가이드라인 검증 및 중복 제거"""

    def __init__(self, openai_api_key: str = None):
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or .env file")
        self.client = OpenAI(api_key=api_key)
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def load_guides(self, jsonl_path: str) -> List[Dict]:
        """단일 JSONL 파일 로드"""
        guides = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():  # 빈 줄 무시
                    guides.append(json.loads(line))
        return guides

    def load_all_guides_from_directory(self, directory: str, pattern: str = "application_guides_*_raw.jsonl") -> List[Dict]:
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
            # Fallback: 모든 application_guides_*.jsonl 파일
            jsonl_files = sorted(dir_path.glob("application_guides_*.jsonl"))

        print(f"📂 Found {len(jsonl_files)} JSONL files in {directory}")

        for jsonl_file in jsonl_files:
            print(f"  - Loading: {jsonl_file.name}")
            guides = self.load_guides(str(jsonl_file))
            all_guides.extend(guides)

        return all_guides

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """OpenAI Embedding 생성"""
        embeddings = []

        # 배치 처리 (최대 2048개)
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=batch
            )

            embeddings.extend([e.embedding for e in response.data])

        return np.array(embeddings)

    def remove_duplicates(
        self,
        guides: List[Dict],
        similarity_threshold: float = 0.85
    ) -> Tuple[List[Dict], List[Tuple[int, int, float]]]:
        """
        Embedding 유사도 기반 중복 제거

        Returns:
            - unique_guides: 중복 제거된 가이드
            - duplicates: (index1, index2, similarity) 튜플 리스트
        """
        print(f"\n🔍 Checking {len(guides)} guides for duplicates...")

        # 검색 텍스트 생성
        texts = [
            f"{g.get('scenario', '')} {g.get('actionable_directive', '')}"
            for g in guides
        ]

        # Embedding 생성
        print("📊 Generating embeddings...")
        embeddings = self.get_embeddings(texts)

        # 유사도 계산
        print("🔢 Computing similarity matrix...")
        similarity_matrix = cosine_similarity(embeddings)

        # 중복 감지
        to_remove = set()
        duplicate_pairs = []

        for i in range(len(guides)):
            for j in range(i + 1, len(guides)):
                sim = similarity_matrix[i][j]

                if sim > similarity_threshold:
                    duplicate_pairs.append((i, j, sim))
                    to_remove.add(j)  # 나중 것 제거

        # 중복 제거
        unique_guides = [g for i, g in enumerate(guides) if i not in to_remove]

        print(f"✅ Found {len(duplicate_pairs)} duplicate pairs")
        print(f"✅ Removed {len(to_remove)} duplicates")
        print(f"✅ Remaining: {len(unique_guides)} unique guides")

        return unique_guides, duplicate_pairs

    def create_review_queue(
        self,
        guides: List[Dict],
        min_confidence: float = 0.7
    ) -> List[Dict]:
        """휴먼 리뷰가 필요한 가이드 추출"""

        review_needed = []

        for guide in guides:
            needs_review = False
            reasons = []

            # 신뢰도 낮음
            if guide.get("confidence_score", 1.0) < min_confidence:
                needs_review = True
                reasons.append(f"Low confidence: {guide.get('confidence_score'):.2f}")

            # 필수 필드 누락
            if not guide.get("scenario"):
                needs_review = True
                reasons.append("Missing scenario")

            if not guide.get("actionable_directive"):
                needs_review = True
                reasons.append("Missing actionable_directive")

            # 키워드 부족
            if len(guide.get("keywords", [])) < 3:
                needs_review = True
                reasons.append(f"Few keywords: {len(guide.get('keywords', []))}")

            if needs_review:
                review_item = guide.copy()
                review_item["review_reasons"] = reasons
                review_needed.append(review_item)

        return review_needed

    def save_review_queue(self, review_items: List[Dict], output_path: str):
        """리뷰 큐를 CSV로 저장"""
        import pandas as pd

        rows = []
        for item in review_items:
            rows.append({
                "guide_id": item.get("guide_id"),
                "scenario": item.get("scenario", "")[:100],
                "actionable_directive": item.get("actionable_directive", "")[:100],
                "confidence": item.get("confidence_score", "N/A"),
                "reasons": ", ".join(item.get("review_reasons", [])),
                "source": item.get("source_document", ""),
            })

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✅ Review queue saved to {output_path}")

    def save_guides(self, guides: List[Dict], output_dir: str, suffix: str):
        """
        JSONL 저장 (타임스탬프 기반 고유 파일명)

        Args:
            guides: 저장할 가이드 리스트
            output_dir: 출력 디렉토리
            suffix: 파일명 접미사 (unique, review 등)

        Returns:
            저장된 파일 경로
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filename = f"application_guides_{self.timestamp}_{suffix}.jsonl"
        output_path = Path(output_dir) / filename

        with open(output_path, "w", encoding="utf-8") as f:
            for guide in guides:
                f.write(json.dumps(guide, ensure_ascii=False) + "\n")

        print(f"✅ Saved {len(guides)} guides to {output_path}")
        return output_path


def main():
    """메인 실행"""

    # 검증자 초기화 (.env에서 자동 로드)
    try:
        validator = GuideValidator()
        print(f"✅ Using embedding model: {validator.embedding_model}")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease ensure:")
        print("1. .env file exists in the project root")
        print("2. OPENAI_API_KEY is set in .env")
        return

    # staging 디렉토리의 모든 가이드 로드
    staging_dirs = [
        "guardcap-rag/data/staging",
        "data/staging"
    ]

    guides = []
    for staging_dir in staging_dirs:
        if Path(staging_dir).exists():
            guides = validator.load_all_guides_from_directory(
                staging_dir,
                pattern="application_guides_*_raw.jsonl"
            )
            if guides:
                break

    if not guides:
        print("❌ No guide files found in staging directory!")
        print("\nPlease run process_guidelines.py first to generate guide files.")
        return

    print(f"\n📊 Total loaded: {len(guides)} guides")

    # 중복 제거 (.env 설정 사용)
    similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))
    unique_guides, duplicates = validator.remove_duplicates(
        guides,
        similarity_threshold=similarity_threshold
    )

    # 리뷰 큐 생성 (.env 설정 사용)
    min_confidence = float(os.getenv("MIN_CONFIDENCE", "0.7"))
    review_needed = validator.create_review_queue(
        unique_guides,
        min_confidence=min_confidence
    )

    print(f"\n📊 Summary:")
    print(f"  Original: {len(guides)}")
    print(f"  Unique: {len(unique_guides)}")
    print(f"  Needs Review: {len(review_needed)}")

    # 저장 (staging 디렉토리에 타임스탬프 기반 파일명)
    output_dir = "data/staging"
    if not Path(output_dir).exists():
        output_dir = "guardcap-rag/data/staging"

    saved_files = []

    # 중복 제거된 가이드 저장
    unique_file = validator.save_guides(unique_guides, output_dir, "unique")
    saved_files.append(str(unique_file))

    # 리뷰 필요 항목 저장
    if review_needed:
        review_file = validator.save_guides(review_needed, output_dir, "review_needed")
        saved_files.append(str(review_file))

        # CSV 리뷰 큐 저장
        csv_path = Path(output_dir) / f"review_queue_{validator.timestamp}.csv"
        validator.save_review_queue(review_needed, str(csv_path))
        saved_files.append(str(csv_path))

    # 중복 쌍 저장
    if duplicates:
        report_path = Path(output_dir) / f"duplicates_report_{validator.timestamp}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "index1": i,
                        "index2": j,
                        "similarity": float(sim),
                        "guide1_id": guides[i].get("guide_id"),
                        "guide2_id": guides[j].get("guide_id"),
                    }
                    for i, j, sim in duplicates
                ],
                f,
                indent=2,
                ensure_ascii=False
            )
        saved_files.append(str(report_path))

    print("\n✨ Validation complete!")
    print(f"\n📁 Saved files:")
    for file in saved_files:
        print(f"  - {file}")


if __name__ == "__main__":
    main()
