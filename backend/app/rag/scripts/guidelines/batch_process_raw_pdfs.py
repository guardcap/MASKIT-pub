#!/usr/bin/env python3
"""
raw_guidelines 디렉토리의 모든 PDF를 배치 처리하는 스크립트
- 자동으로 발행 기관 감지
- 큰 파일(>10MB)은 분할 처리
- 진행 상황 추적 및 에러 로깅
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import logging

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.guidelines.process_guidelines import GuidelineProcessor
from scripts.guidelines.build_guides_vectordb import GuidesVectorDBBuilder
from dotenv import load_dotenv
from tqdm import tqdm

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AuthorityDetector:
    """파일명에서 발행 기관 감지"""

    AUTHORITY_KEYWORDS = {
        "개인정보보호위원회": ["개인정보", "보호"],
        "금융보안원": ["금융", "보안"],
        "KISA": ["KISA", "정보보호"],
        "공정거래위원회": ["공정거래"],
        "금융위원회": ["금융위"],
        "과학기술정보통신부": ["과학기술", "통신"],
        "행정안전부": ["행정안전", "정보보호"],
    }

    @staticmethod
    def detect(filename: str) -> str:
        """파일명에서 발행 기관 감지"""
        filename_lower = filename.lower()

        # 정확한 매칭
        for authority, keywords in AuthorityDetector.AUTHORITY_KEYWORDS.items():
            if all(kw.lower() in filename_lower for kw in keywords):
                return authority

        # 부분 매칭
        for authority, keywords in AuthorityDetector.AUTHORITY_KEYWORDS.items():
            if any(kw.lower() in filename_lower for kw in keywords):
                return authority

        # 기본값
        return "개인정보보호위원회"


class RawPDFBatchProcessor:
    """raw_guidelines 디렉토리의 PDF 배치 처리"""

    def __init__(self, raw_dir: str = "data/raw_guidelines"):
        self.raw_dir = Path(raw_dir)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.vision_model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
        self.batch_delay = int(os.getenv("PDF_BATCH_DELAY", "3"))

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

        # 결과 저장 디렉토리
        self.output_dir = Path("data/staging")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 타임스탐프 (모든 파일에 동일하게 사용)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"Initialized batch processor")
        logger.info(f"Raw directory: {self.raw_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Vision model: {self.vision_model}")

    def get_pdf_files(self) -> List[Tuple[Path, int]]:
        """raw_guidelines 디렉토리의 모든 PDF 파일 목록"""
        if not self.raw_dir.exists():
            logger.error(f"Directory not found: {self.raw_dir}")
            return []

        pdf_files = []
        for pdf_file in sorted(self.raw_dir.glob("*.pdf")):
            file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
            pdf_files.append((pdf_file, file_size_mb))

        return pdf_files

    async def process_single_pdf(
        self,
        pdf_path: Path,
        file_size_mb: float,
        file_index: int,
        total_files: int
    ) -> Dict:
        """단일 PDF 처리"""
        logger.info(
            f"\n[{file_index}/{total_files}] Processing: {pdf_path.name} ({file_size_mb:.2f}MB)"
        )

        try:
            # 발행 기관 감지
            authority = AuthorityDetector.detect(pdf_path.name)
            logger.info(f"  Detected authority: {authority}")

            # GuidelineProcessor 생성
            processor = GuidelineProcessor(
                openai_api_key=self.api_key,
                vision_model=self.vision_model,
                output_dir=str(self.output_dir)
            )

            # PDF 처리
            guides = await processor.process_pdf(str(pdf_path), authority)

            if not guides:
                logger.warning(f"  ⚠️  No guides extracted from {pdf_path.name}")
                return {
                    "file": pdf_path.name,
                    "status": "no_data",
                    "guides_count": 0
                }

            logger.info(f"  ✅ Extracted {len(guides)} guides")

            # JSONL 저장 (고유 파일명)
            async def save():
                return await processor.save_guides(
                    guides,
                    suffix=f"batch_{file_index:02d}"
                )

            output_file = await save()
            logger.info(f"  💾 Saved to: {Path(output_file).name}")

            return {
                "file": pdf_path.name,
                "status": "success",
                "guides_count": len(guides),
                "output_file": Path(output_file).name,
                "authority": authority,
                "file_size_mb": file_size_mb
            }

        except Exception as e:
            logger.error(f"  ❌ Error processing {pdf_path.name}: {str(e)}")
            return {
                "file": pdf_path.name,
                "status": "error",
                "error": str(e)
            }

    async def process_all_pdfs(self) -> List[Dict]:
        """모든 PDF 배치 처리"""
        pdf_files = self.get_pdf_files()

        if not pdf_files:
            logger.warning("No PDF files found in raw_guidelines directory")
            return []

        # 병렬 처리를 위한 프로세스 ID와 총 프로세스 수 설정
        process_id = int(os.getenv("PROCESS_ID", "1"))
        total_processes = int(os.getenv("TOTAL_PROCESSES", "1"))

        # 이 프로세스가 처리할 파일 필터링 (라운드 로빈 방식)
        filtered_files = [
            (pdf_path, file_size_mb)
            for idx, (pdf_path, file_size_mb) in enumerate(pdf_files)
            if idx % total_processes == (process_id - 1)
        ]

        logger.info(f"\nProcess {process_id}/{total_processes}: Starting batch processing of {len(filtered_files)} PDF files...")
        logger.info(f"Total files in directory: {len(pdf_files)}")
        logger.info("=" * 80)

        results = []

        for file_idx, (pdf_path, file_size_mb) in enumerate(filtered_files, 1):
            # 전체 파일 목록에서의 실제 인덱스 계산
            actual_idx = pdf_files.index((pdf_path, file_size_mb)) + 1

            # Rate Limit 방지 (첫 파일 제외)
            if file_idx > 1:
                logger.info(f"Waiting {self.batch_delay} seconds before next file...")
                await asyncio.sleep(self.batch_delay)

            # 처리
            result = await self.process_single_pdf(pdf_path, file_size_mb, actual_idx, len(pdf_files))
            results.append(result)

        return results

    def build_vectordb(self) -> Dict:
        """처리된 모든 가이드를 VectorDB에 추가"""
        logger.info("\n" + "=" * 80)
        logger.info("Building VectorDB from all processed guides...")

        try:
            builder = GuidesVectorDBBuilder(
                openai_api_key=self.api_key,
                db_path="data/chromadb/application_guides"
            )

            # staging 폴더의 모든 파일 로드
            staging_dir = Path("data/staging")
            all_guides = builder.load_all_guides_from_directory(
                str(staging_dir),
                pattern="application_guides_*.jsonl"
            )

            if not all_guides:
                logger.warning("No guides found in staging directory")
                return {
                    "status": "no_data",
                    "total_guides": 0
                }

            logger.info(f"Loading {len(all_guides)} guides from staging files")

            # VectorDB 추가
            builder.add_guides_to_db(all_guides, batch_size=50)

            logger.info(f"✅ VectorDB updated with {len(all_guides)} guides")

            return {
                "status": "success",
                "total_guides": len(all_guides)
            }

        except Exception as e:
            logger.error(f"❌ Error building VectorDB: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def save_results(self, results: List[Dict], vectordb_result: Dict):
        """처리 결과를 JSON 파일로 저장"""
        summary = {
            "timestamp": self.timestamp,
            "total_files": len(results),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "error"),
            "no_data": sum(1 for r in results if r["status"] == "no_data"),
            "total_guides_extracted": sum(r.get("guides_count", 0) for r in results),
            "vectordb": vectordb_result,
            "files": results
        }

        output_file = self.output_dir / f"batch_processing_report_{self.timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📊 Processing report saved to: {output_file.name}")

        return summary

    def print_summary(self, summary: Dict):
        """처리 결과 요약 출력"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 BATCH PROCESSING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total files processed: {summary['total_files']}")
        logger.info(f"✅ Successful: {summary['successful']}")
        logger.info(f"❌ Failed: {summary['failed']}")
        logger.info(f"⚠️  No data: {summary['no_data']}")
        logger.info(f"Total guides extracted: {summary['total_guides_extracted']}")
        logger.info(f"VectorDB status: {summary['vectordb']['status']}")

        if summary['vectordb']['status'] == 'success':
            logger.info(f"Total guides in VectorDB: {summary['vectordb']['total_guides']}")

        logger.info("=" * 80)

        # 파일별 결과
        logger.info("\n📋 FILE-BY-FILE RESULTS:")
        for file_result in summary['files']:
            status_emoji = "✅" if file_result['status'] == 'success' else "❌"
            logger.info(
                f"{status_emoji} {file_result['file']}: {file_result['status']} "
                f"({file_result.get('guides_count', 0)} guides)"
            )


async def main():
    """메인 함수"""
    try:
        processor = RawPDFBatchProcessor()

        # 모든 PDF 처리
        results = await processor.process_all_pdfs()

        # VectorDB 빌드
        vectordb_result = processor.build_vectordb()

        # 결과 저장 및 출력
        summary = processor.save_results(results, vectordb_result)
        processor.print_summary(summary)

        logger.info("\n🎉 Batch processing completed!")

    except KeyboardInterrupt:
        logger.info("\n⚠️  Processing interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
