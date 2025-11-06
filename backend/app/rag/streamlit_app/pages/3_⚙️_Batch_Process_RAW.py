"""
Raw Guidelines 배치 처리 페이지
raw_guidelines 디렉토리의 모든 PDF를 자동으로 처리하여 VectorDB에 추가
"""

import streamlit as st
from pathlib import Path
import asyncio
import json
import sys
import os
from datetime import datetime
import tempfile
import logging

# litellm 로깅 비활성화
import litellm
litellm.disable_logging = True

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.guidelines.process_guidelines import GuidelineProcessor
from scripts.guidelines.build_guides_vectordb import GuidesVectorDBBuilder
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Batch Process - Guardcap RAG",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Batch Process Raw Guidelines")
st.markdown("---")
st.markdown("`raw_guidelines` 디렉토리의 모든 PDF를 자동으로 처리하여 VectorDB에 추가합니다.")

# 로깅 설정
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


# 사이드바 설정
with st.sidebar:
    st.header("⚙️ Processing Settings")

    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        st.success("✅ OpenAI API Key 설정됨")
    else:
        st.error("❌ OPENAI_API_KEY 필요")
        st.info("`.env` 파일에 API 키를 설정하세요")

    st.markdown("---")

    # 처리 옵션
    st.subheader("Processing Options")
    vision_model = st.selectbox(
        "Vision Model",
        ["gpt-4o-mini", "gpt-4o"],
        help="gpt-4o-mini: 빠름 (2-3배), gpt-4o: 정확함"
    )

    batch_delay = st.slider(
        "배치 간 딜레이 (초)",
        min_value=1,
        max_value=10,
        value=3,
        help="Rate Limit 방지를 위한 PDF 간 대기 시간"
    )

# 메인 컨텐츠
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📂 Raw Guidelines Directory")

    raw_dir = Path("data/raw_guidelines")

    if not raw_dir.exists():
        st.error(f"❌ Directory not found: {raw_dir}")
    else:
        # PDF 파일 목록
        pdf_files = list(raw_dir.glob("*.pdf"))
        pdf_files.sort()

        st.info(f"📁 Found **{len(pdf_files)}** PDF files")

        if pdf_files:
            # 파일 목록 표시
            with st.expander(f"📋 File List ({len(pdf_files)} files)", expanded=False):
                file_data = []
                for pdf_file in pdf_files:
                    file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
                    authority = AuthorityDetector.detect(pdf_file.name)
                    file_data.append({
                        "파일명": pdf_file.name[:60] + ("..." if len(pdf_file.name) > 60 else ""),
                        "크기 (MB)": f"{file_size_mb:.2f}",
                        "기관": authority
                    })

                st.dataframe(file_data, use_container_width=True, hide_index=True)

with col2:
    st.subheader("📊 처리 정보")

    if pdf_files:
        total_size = sum(p.stat().st_size for p in pdf_files) / (1024 * 1024)
        avg_size = total_size / len(pdf_files)

        st.metric("총 파일 수", len(pdf_files))
        st.metric("총 크기", f"{total_size:.1f} MB")
        st.metric("평균 파일 크기", f"{avg_size:.1f} MB")

        # 처리 시간 추정
        est_time_min = (len(pdf_files) * 45) / 60  # 대략 PDF당 45초
        est_time_max = (len(pdf_files) * 90) / 60
        st.metric("예상 처리 시간", f"{est_time_min:.0f}-{est_time_max:.0f}분")
    else:
        st.warning("처리할 PDF 파일이 없습니다")

st.markdown("---")

# 처리 버튼
if api_key and pdf_files:
    if st.button("🚀 Start Batch Processing", type="primary", use_container_width=True):
        st.session_state.processing = True

    if "processing" in st.session_state and st.session_state.processing:
        try:
            # 진행 상황 표시
            progress_bar = st.progress(0)
            status_container = st.container()

            # 환경 변수 설정
            os.environ["PDF_BATCH_DELAY"] = str(batch_delay)
            os.environ["OPENAI_VISION_MODEL"] = vision_model

            # 결과 저장소
            results = []
            all_guides_extracted = 0

            # 1. 모든 PDF 처리
            with status_container:
                st.info("🚀 배치 처리 시작...")

            for file_idx, pdf_file in enumerate(pdf_files):
                file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
                progress = (file_idx / len(pdf_files)) * 90

                with status_container:
                    st.write(
                        f"📄 [{file_idx + 1}/{len(pdf_files)}] "
                        f"{pdf_file.name[:50]}... ({file_size_mb:.2f}MB)"
                    )

                try:
                    # 발행 기관 감지
                    authority = AuthorityDetector.detect(pdf_file.name)

                    # PDF 처리
                    processor = GuidelineProcessor(
                        openai_api_key=api_key,
                        vision_model=vision_model,
                        output_dir="data/staging"
                    )

                    async def process_pdf():
                        return await processor.process_pdf(str(pdf_file), authority)

                    guides = asyncio.run(process_pdf())

                    if guides:
                        # JSONL 저장
                        async def save_guides():
                            return await processor.save_guides(
                                guides,
                                suffix=f"batch_{file_idx:02d}"
                            )

                        output_file = asyncio.run(save_guides())

                        results.append({
                            "파일": pdf_file.name,
                            "상태": "✅ 성공",
                            "가이드 수": len(guides),
                            "파일 크기": f"{file_size_mb:.2f}MB",
                            "기관": authority
                        })

                        all_guides_extracted += len(guides)

                        with status_container:
                            st.success(
                                f"✅ {pdf_file.name}: {len(guides)}개 가이드 추출"
                            )
                    else:
                        results.append({
                            "파일": pdf_file.name,
                            "상태": "⚠️ 데이터 없음",
                            "가이드 수": 0,
                            "파일 크기": f"{file_size_mb:.2f}MB",
                            "기관": authority
                        })

                        with status_container:
                            st.warning(f"⚠️ {pdf_file.name}: 가이드 추출 실패")

                    # Rate Limit 딜레이 (첫 파일 제외)
                    if file_idx < len(pdf_files) - 1:
                        with status_container:
                            st.info(f"⏸️ {batch_delay}초 대기 중... (Rate Limit 방지)")
                        asyncio.run(asyncio.sleep(batch_delay))

                    progress_bar.progress(min(progress + 10, 90))

                except Exception as e:
                    results.append({
                        "파일": pdf_file.name,
                        "상태": "❌ 오류",
                        "가이드 수": 0,
                        "파일 크기": f"{file_size_mb:.2f}MB",
                        "기관": "오류 발생"
                    })

                    with status_container:
                        st.error(f"❌ {pdf_file.name}: {str(e)[:100]}")

            # 2. VectorDB 빌드
            with status_container:
                st.info("🔍 VectorDB 빌드 중...")

            progress_bar.progress(91)

            builder = GuidesVectorDBBuilder(
                openai_api_key=api_key,
                db_path="data/chromadb/application_guides"
            )

            staging_dir = Path("data/staging")
            all_guides = builder.load_all_guides_from_directory(
                str(staging_dir),
                pattern="application_guides_*.jsonl"
            )

            if all_guides:
                builder.add_guides_to_db(all_guides, batch_size=50)

            progress_bar.progress(100)

            # 3. 결과 표시
            st.markdown("---")
            st.success("### ✅ 배치 처리 완료!")

            # 결과 요약
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("처리된 파일", len(results))
            col2.metric("추출된 가이드", all_guides_extracted)
            col3.metric("VectorDB 총계", len(all_guides) if all_guides else 0)
            col4.metric("성공률", f"{sum(1 for r in results if '✅' in r['상태']) / len(results) * 100:.0f}%")

            # 파일별 결과
            st.subheader("📋 File Processing Results")
            st.dataframe(results, use_container_width=True, hide_index=True)

            # 저장된 JSONL 파일 목록
            st.subheader("📁 Saved JSONL Files")
            jsonl_files = list(staging_dir.glob("application_guides_*batch*.jsonl"))
            if jsonl_files:
                jsonl_data = []
                for jsonl_file in sorted(jsonl_files, reverse=True):
                    file_size_kb = jsonl_file.stat().st_size / 1024
                    guide_count = sum(1 for line in open(jsonl_file, encoding="utf-8") if line.strip())
                    jsonl_data.append({
                        "파일명": jsonl_file.name,
                        "가이드 수": guide_count,
                        "크기 (KB)": f"{file_size_kb:.1f}"
                    })

                st.dataframe(jsonl_data, use_container_width=True, hide_index=True)

            st.session_state.processing = False

        except Exception as e:
            st.error(f"❌ 처리 중 오류 발생: {str(e)}")
            st.exception(e)
            st.session_state.processing = False

else:
    if not api_key:
        st.warning("❌ OpenAI API Key가 설정되지 않았습니다")
    if not pdf_files:
        st.warning("❌ raw_guidelines 디렉토리에 PDF 파일이 없습니다")

# 하단 정보
st.markdown("---")
st.info("""
### 📝 사용 방법

1. **API Key 설정**: `.env` 파일에 `OPENAI_API_KEY` 설정
2. **사이드바 옵션**: Vision 모델과 딜레이 조정
3. **버튼 클릭**: "🚀 Start Batch Processing" 버튼 클릭
4. **진행 상황 확인**: 실시간 진행 상황 표시
5. **검색 테스트**: "🔍 Search Guidelines" 페이지에서 검색

### ⚠️ 주의사항

- 처리 중 페이지를 나가지 마세요
- Rate Limit 에러가 발생하면 딜레이를 증가시켜보세요
- 큰 파일은 처리 시간이 오래 걸릴 수 있습니다
- 처리 중단은 다시 실행하면 이어서 처리됩니다
""")
