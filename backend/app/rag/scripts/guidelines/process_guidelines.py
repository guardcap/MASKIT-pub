"""
실무 가이드라인 PDF → 구조화된 VectorDB 파이프라인
OpenAI API + Zerox 기반, 대용량(50MB+) PDF 지원
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import re
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# PDF 처리
import fitz  # PyMuPDF for large PDFs
from pyzerox import zerox
from openai import AsyncOpenAI

# 검증 및 유틸리티
from pydantic import BaseModel, ValidationError, Field
from tqdm import tqdm
import hashlib


class GuideContext(BaseModel):
    """이메일 컨텍스트"""
    sender_type: Optional[str] = Field(None, description="internal, external_customer, partner, regulatory")
    receiver_type: Optional[str] = Field(None, description="internal, external_customer, partner, regulatory")
    email_purpose: Optional[str] = Field(None, description="견적서, 문의, 보고 등")
    pii_types: Optional[List[str]] = Field(default_factory=list, description="phone, ssn, account, address, email, name")


class GuideExample(BaseModel):
    """가이드 예시"""
    case_description: str
    masking_decision: str  # mask, no_mask, partial_mask
    reasoning: str


class ApplicationGuide(BaseModel):
    """실무 가이드라인 스키마"""
    guide_id: str
    source_authority: str  # 개인정보보호위원회, 공정거래위원회, KISA 등
    source_document: str
    publish_date: Optional[str] = None
    document_url: Optional[str] = None
    scenario: str
    context: Optional[GuideContext] = None
    interpretation: str
    actionable_directive: str
    keywords: List[str]
    related_law_ids: List[str] = Field(default_factory=list)
    examples: List[GuideExample] = Field(default_factory=list)
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    reviewed: bool = False
    reviewer_notes: Optional[str] = None


class LargePDFProcessor:
    """대용량 PDF 최적화 처리기"""

    def __init__(self, max_pages_per_batch: int = 10):
        self.max_pages_per_batch = max_pages_per_batch

    def get_pdf_info(self, pdf_path: str) -> Dict:
        """PDF 메타데이터 추출"""
        doc = fitz.open(pdf_path)
        info = {
            "page_count": len(doc),
            "file_size_mb": Path(pdf_path).stat().st_size / (1024 * 1024),
            "metadata": doc.metadata,
        }
        doc.close()
        return info

    def split_pdf_by_pages(self, pdf_path: str, output_dir: Path) -> List[Path]:
        """대용량 PDF를 작은 배치로 분할"""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        output_dir.mkdir(parents=True, exist_ok=True)
        split_files = []

        for i in range(0, total_pages, self.max_pages_per_batch):
            end_page = min(i + self.max_pages_per_batch, total_pages)

            # 새 PDF 생성
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=end_page - 1)

            output_path = output_dir / f"batch_{i:04d}_{end_page:04d}.pdf"
            new_doc.save(output_path)
            new_doc.close()

            split_files.append(output_path)

        doc.close()
        return split_files

    def extract_text_fallback(self, pdf_path: str) -> str:
        """OCR 실패 시 PyMuPDF로 텍스트 추출"""
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text


class GuidelineProcessor:
    """OpenAI 기반 가이드라인 프로세서"""

    def __init__(
        self,
        openai_api_key: str = None,
        model: str = None,
        vision_model: str = None,
        output_dir: str = "data/staging",  # 변경: application_guides 제거
        temp_dir: str = "data/temp/pdf_batches"
    ):
        # .env에서 기본값 로드
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or .env file")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.vision_model = vision_model or os.getenv("OPENAI_VISION_MODEL", "gpt-4o")
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)

        batch_size = int(os.getenv("PDF_BATCH_SIZE", "10"))
        self.pdf_processor = LargePDFProcessor(max_pages_per_batch=batch_size)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # 타임스탬프 생성 (파일명 고유성 보장)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def process_pdf(self, pdf_path: str, authority: str = "개인정보보호위원회") -> List[ApplicationGuide]:
        """PDF 파일을 가이드라인 객체로 변환"""
        pdf_path_obj = Path(pdf_path)
        print(f"\n{'='*60}")
        print(f"Processing: {pdf_path_obj.name}")

        # PDF 정보 확인
        pdf_info = self.pdf_processor.get_pdf_info(pdf_path)
        print(f"Pages: {pdf_info['page_count']}, Size: {pdf_info['file_size_mb']:.2f} MB")

        # 대용량 PDF 처리 전략
        if pdf_info['file_size_mb'] > 20 or pdf_info['page_count'] > 50:
            print("⚠️  Large PDF detected - using batch processing")
            return await self._process_large_pdf(pdf_path, pdf_path_obj, authority)
        else:
            return await self._process_standard_pdf(pdf_path, pdf_path_obj, authority)

    async def _process_standard_pdf(
        self,
        pdf_path: str,
        pdf_path_obj: Path,
        authority: str
    ) -> List[ApplicationGuide]:
        """표준 크기 PDF 처리 (Zerox 사용)"""
        print("📄 Using Zerox for OCR + Vision processing...")

        try:
            # Zerox로 PDF → Markdown 변환
            result = await zerox(
                file_path=pdf_path,
                model=self.vision_model,
                output_dir=str(self.temp_dir),
                cleanup=True,  # 임시 이미지 자동 삭제
            )

            markdown = result.get("content", "") if isinstance(result, dict) else str(result)

        except Exception as e:
            print(f"❌ Zerox failed: {e}")
            print("🔄 Falling back to PyMuPDF text extraction...")
            markdown = self.pdf_processor.extract_text_fallback(pdf_path)

        # 가이드라인 구조화
        guides = await self._structure_document(
            markdown,
            source_document=pdf_path_obj.name,
            authority=authority
        )

        return guides

    async def _process_large_pdf(
        self,
        pdf_path: str,
        pdf_path_obj: Path,
        authority: str
    ) -> List[ApplicationGuide]:
        """대용량 PDF 배치 처리"""
        print("🔪 Splitting PDF into smaller batches...")

        batch_dir = self.temp_dir / f"batches_{pdf_path_obj.stem}"
        batch_files = self.pdf_processor.split_pdf_by_pages(pdf_path, batch_dir)

        print(f"✅ Created {len(batch_files)} batches")

        all_guides = []

        # 배치별 처리 (Rate Limit 방지를 위한 딜레이 추가)
        batch_delay = int(os.getenv("PDF_BATCH_DELAY", "3"))

        for i, batch_file in enumerate(tqdm(batch_files, desc="Processing batches")):
            try:
                # Rate Limit 방지: 각 배치 사이에 딜레이
                if i > 0:
                    print(f"⏸️  Waiting {batch_delay} seconds to avoid rate limit...")
                    await asyncio.sleep(batch_delay)

                # Zerox 처리
                result = await zerox(
                    file_path=str(batch_file),
                    model=self.vision_model,
                    output_dir=str(self.temp_dir / f"batch_{i}"),
                    cleanup=True,
                )

                markdown = result.get("content", "") if isinstance(result, dict) else str(result)

                # 구조화
                guides = await self._structure_document(
                    markdown,
                    source_document=f"{pdf_path_obj.name} (batch {i+1}/{len(batch_files)})",
                    authority=authority
                )

                all_guides.extend(guides)

            except Exception as e:
                print(f"⚠️  Batch {i+1} failed: {e}")
                continue

        # 임시 파일 정리
        import shutil
        shutil.rmtree(batch_dir, ignore_errors=True)

        return all_guides

    async def _structure_document(
        self,
        markdown: str,
        source_document: str,
        authority: str
    ) -> List[ApplicationGuide]:
        """마크다운 문서를 가이드라인으로 구조화"""

        # Step 1: 섹션 분할
        sections = await self._extract_sections(markdown)
        print(f"📑 Extracted {len(sections)} sections")

        # Step 2: 각 섹션 구조화
        guides = []
        for i, section in enumerate(sections):
            guide_data = await self._structure_section(section, source_document, authority)

            if guide_data:
                # guide_id 생성
                guide_data["guide_id"] = self._generate_guide_id(
                    authority,
                    source_document,
                    i
                )

                try:
                    guide = ApplicationGuide(**guide_data)
                    guides.append(guide)
                except ValidationError as e:
                    print(f"⚠️  Validation error for section {i}: {e}")
                    continue

        return guides

    async def _extract_sections(self, markdown: str) -> List[str]:
        """마크다운을 논리적 섹션으로 분할"""

        # 간단한 규칙: 헤더(#, ##)로 분할
        # 더 정교한 방법: LLM에게 의미적 분할 요청

        if len(markdown) < 500:
            return [markdown]

        # LLM으로 섹션 분할
        prompt = f"""
다음 가이드라인 문서를 독립적인 실무 가이드 섹션으로 분할하세요.
각 섹션은 하나의 구체적인 상황/지침을 다루어야 합니다.

문서:
{markdown[:8000]}  # 토큰 제한

JSON 배열로 반환:
["섹션 1 전체 텍스트", "섹션 2 전체 텍스트", ...]

반드시 유효한 JSON만 반환하세요. 설명 없이 JSON만 출력하세요.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()

            # JSON 추출 (코드 블록 제거)
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

            sections = json.loads(content)
            return sections if isinstance(sections, list) else [markdown]

        except Exception as e:
            print(f"⚠️  Section splitting failed: {e}")
            # Fallback: 헤더 기반 분할
            return self._split_by_headers(markdown)

    def _split_by_headers(self, markdown: str) -> List[str]:
        """헤더 기반 단순 분할"""
        sections = re.split(r'\n#{1,3}\s+', markdown)
        return [s.strip() for s in sections if len(s.strip()) > 100]

    async def _structure_section(
        self,
        section: str,
        source_document: str,
        authority: str
    ) -> Optional[Dict]:
        """섹션을 스키마에 맞춰 구조화"""

        prompt = f"""
다음 가이드라인 섹션을 JSON으로 구조화하세요.

섹션 텍스트:
{section[:4000]}

다음 필드를 추출하세요:
- scenario: 적용 상황 (100자 이내, 예: "외부 고객이 제품 문의를 위해 이메일을 보낸 경우")
- context: {{
    "sender_type": "internal/external_customer/partner/regulatory 중 하나",
    "receiver_type": "internal/external_customer/partner/regulatory 중 하나",
    "email_purpose": "견적서/문의/보고 등",
    "pii_types": ["phone", "ssn", "email", "name" 등 배열]
  }}
- interpretation: 법적 해석 및 배경 설명
- actionable_directive: 실행 지침 (마스킹 예외/마스킹 필수 등 명확하게)
- keywords: 검색 키워드 배열 (5-10개)
- related_law_ids: 관련 법률 조항 ID 배열 (예: ["개인정보보호법_제15조_1항"])
- examples: [{{
    "case_description": "사례 설명",
    "masking_decision": "mask/no_mask/partial_mask",
    "reasoning": "판단 근거"
  }}] (선택사항)

JSON 포맷 (설명 없이 JSON만):
{{
  "scenario": "...",
  "context": {{}},
  "interpretation": "...",
  "actionable_directive": "...",
  "keywords": [],
  "related_law_ids": [],
  "examples": []
}}

반드시 유효한 JSON만 반환하세요. 마크다운 코드 블록 없이 순수 JSON만 출력하세요.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()

            # JSON 추출
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

            guide_data = json.loads(content)

            # 메타데이터 추가
            guide_data["source_authority"] = authority
            guide_data["source_document"] = source_document
            guide_data["confidence_score"] = 0.8
            guide_data["reviewed"] = False

            return guide_data

        except Exception as e:
            print(f"⚠️  Section structuring failed: {e}")
            return None

    def _generate_guide_id(self, authority: str, source_doc: str, index: int) -> str:
        """고유 guide_id 생성"""
        # 기관명 약어
        authority_map = {
            "개인정보보호위원회": "PIPC",
            "공정거래위원회": "FTC",
            "KISA": "KISA",
            "금융감독원": "FSS",
            "방송통신위원회": "KCC",
        }

        authority_code = authority_map.get(authority, "UNK")

        # 문서명 해시
        doc_hash = hashlib.md5(source_doc.encode()).hexdigest()[:6]

        # 날짜
        date_str = datetime.now().strftime("%Y%m")

        return f"GUIDE-{authority_code}-{date_str}-{doc_hash}-{index:03d}"

    async def save_guides(self, guides: List[ApplicationGuide], suffix: str = "raw"):
        """
        가이드를 JSONL 형식으로 저장 (타임스탬프 기반 고유 파일명)

        Args:
            guides: 저장할 가이드 리스트
            suffix: 파일명 접미사 (raw, unique, review 등)

        Returns:
            저장된 파일 경로
        """
        # 타임스탬프 기반 고유 파일명 생성
        filename = f"application_guides_{self.timestamp}_{suffix}.jsonl"
        output_file = self.output_dir / filename

        with open(output_file, "w", encoding="utf-8") as f:
            for guide in guides:
                f.write(guide.model_dump_json(exclude_none=True) + "\n")

        print(f"\n✅ Saved {len(guides)} guides to {output_file}")
        return output_file

    def validate_guides(self, guides: List[ApplicationGuide]) -> Dict[str, List[ApplicationGuide]]:
        """가이드 검증 및 분류"""
        valid = []
        needs_review = []

        for guide in guides:
            if guide.confidence_score < 0.7:
                needs_review.append(guide)
            elif not guide.scenario or not guide.actionable_directive:
                needs_review.append(guide)
            else:
                valid.append(guide)

        return {
            "valid": valid,
            "needs_review": needs_review,
        }


async def main():
    """메인 실행"""

    # 프로세서 초기화 (.env에서 자동 로드)
    try:
        processor = GuidelineProcessor()
        print(f"✅ Using model: {processor.model}")
        print(f"✅ Using vision model: {processor.vision_model}")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease ensure:")
        print("1. .env file exists in the project root")
        print("2. OPENAI_API_KEY is set in .env")
        print("\nOr run: export OPENAI_API_KEY='sk-...'")
        return

    # PDF 파일 찾기
    pdf_dir = Path("guardcap-rag/data/raw_guidelines")
    if not pdf_dir.exists():
        pdf_dir = Path("data/raw_guidelines")

    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"❌ No PDF files found in {pdf_dir}")
        print("Please add PDF files to data/raw_guidelines/")
        return

    print(f"\n🔍 Found {len(pdf_files)} PDF files")

    # 처리할 파일 개수 제한 (테스트용)
    max_files = int(os.getenv("MAX_PDF_FILES", "5"))
    pdf_files = pdf_files[:max_files]

    all_guides = []

    # PDF 처리
    for pdf_file in pdf_files:
        try:
            guides = await processor.process_pdf(
                str(pdf_file),
                authority="개인정보보호위원회"  # 기본값, 파일명으로 자동 감지 가능
            )
            all_guides.extend(guides)

        except Exception as e:
            print(f"❌ Failed to process {pdf_file.name}: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"📊 Total guides extracted: {len(all_guides)}")

    # 검증
    validation_result = processor.validate_guides(all_guides)
    valid = validation_result["valid"]
    needs_review = validation_result["needs_review"]

    print(f"✅ Valid: {len(valid)}")
    print(f"⚠️  Needs review: {len(needs_review)}")

    # 저장 (타임스탬프 기반 고유 파일명)
    saved_files = []

    if valid:
        file_path = await processor.save_guides(valid, "raw")
        saved_files.append(str(file_path))

    if needs_review:
        file_path = await processor.save_guides(needs_review, "review")
        saved_files.append(str(file_path))

    print("\n✨ Processing complete!")
    print(f"\n📁 Saved files:")
    for file in saved_files:
        print(f"  - {file}")


if __name__ == "__main__":
    asyncio.run(main())
