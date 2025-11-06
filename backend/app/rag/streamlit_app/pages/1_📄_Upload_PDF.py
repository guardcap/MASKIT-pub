"""
PDF 업로드 및 VectorDB 추가 페이지
"""

import streamlit as st
from pathlib import Path
import asyncio
import json
import sys
import os
from datetime import datetime
import tempfile
import litellm

# litellm의 백그라운드 로깅 워커를 비활성화합니다.
litellm.disable_logging = True

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.guidelines.process_guidelines import GuidelineProcessor
from scripts.guidelines.build_guides_vectordb import GuidesVectorDBBuilder
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Upload PDF - Guardcap RAG",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Upload & Process Guidelines PDF")
st.markdown("---")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ Processing Settings")

    authority = st.selectbox(
        "발행 기관",
        [
            "개인정보보호위원회",
            "금융보안원",
            "금융위원회",
            "공정거래위원회",
            "KISA (한국인터넷진흥원)",
            "기타"
        ]
    )

    if authority == "기타":
        authority = st.text_input("기관명 입력", "")

    st.markdown("---")

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

    batch_size = st.slider(
        "배치 크기 (페이지)",
        min_value=5,
        max_value=30,
        value=20,
        help="대용량 PDF 분할 시 배치 당 페이지 수"
    )

# 메인 컨텐츠
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 Upload PDF File")

    uploaded_file = st.file_uploader(
        "PDF 파일 선택",
        type=["pdf"],
        help="실무 가이드라인 PDF를 업로드하세요 (최대 100MB)"
    )

    if uploaded_file:
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.info(f"📁 **File**: {uploaded_file.name} ({file_size_mb:.2f} MB)")

        if file_size_mb > 100:
            st.error("❌ 파일 크기가 100MB를 초과합니다.")
        else:
            st.success("✅ 파일 업로드 완료")

with col2:
    st.subheader("📊 예상 처리 시간")

    if uploaded_file:
        # 페이지 수 추정 (대략 1MB = 15-20페이지)
        est_pages = int(file_size_mb * 17)

        if vision_model == "gpt-4o-mini":
            est_time_min = est_pages * 0.05  # ~3초/페이지
            est_time_max = est_pages * 0.08
        else:
            est_time_min = est_pages * 0.1   # ~6초/페이지
            est_time_max = est_pages * 0.15

        st.metric("예상 페이지", f"~{est_pages}p")
        st.metric("예상 시간", f"{est_time_min:.1f}-{est_time_max:.1f}분")
        st.metric("배치 수", f"~{est_pages // batch_size + 1}")
    else:
        st.info("PDF를 업로드하면 예상 정보가 표시됩니다")

st.markdown("---")

# 처리 버튼
if uploaded_file and api_key and authority:
    if st.button("🚀 Process PDF", type="primary", use_container_width=True):
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        try:
            # 진행 상황 표시
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Step 1: PDF 처리
            status_text.text("📄 Step 1/3: Processing PDF with Vision OCR...")
            status_text.text(f"⚙️  Settings: {vision_model}, 배치={batch_size}페이지")
            progress_bar.progress(10)

            # 배치 크기를 환경 변수로 설정 (GuidelineProcessor 생성 전에!)
            os.environ["PDF_BATCH_SIZE"] = str(batch_size)

            processor = GuidelineProcessor(
                openai_api_key=api_key,
                vision_model=vision_model
            )

            # 비동기 처리 실행
            async def process():
                return await processor.process_pdf(tmp_path, authority)

            guides = asyncio.run(process())
            progress_bar.progress(50)

            if not guides:
                st.error("❌ PDF 처리 실패: 가이드라인을 추출할 수 없습니다.")
            else:
                status_text.text(f"✅ Step 1 완료: {len(guides)}개 가이드라인 추출됨")

                # Step 2: JSONL 저장 (타임스탬프 기반 고유 파일명)
                status_text.text("💾 Step 2/3: Saving to JSONL...")
                progress_bar.progress(60)

                # save_guides 메서드 사용
                async def save():
                    return await processor.save_guides(guides, suffix="uploaded")

                output_file = asyncio.run(save())

                progress_bar.progress(70)
                status_text.text(f"✅ Step 2 완료: {Path(output_file).name}")

                # Step 3: VectorDB에 추가
                status_text.text("🔍 Step 3/3: Adding to VectorDB...")
                progress_bar.progress(80)

                builder = GuidesVectorDBBuilder(
                    openai_api_key=api_key,
                    db_path="data/chromadb/application_guides"
                )

                # staging 폴더의 모든 unique/uploaded 파일 로드
                staging_dir = Path("data/staging")
                all_guides = builder.load_all_guides_from_directory(
                    str(staging_dir),
                    pattern="application_guides_*_{uploaded,unique}.jsonl"
                )

                if not all_guides:
                    # Fallback: 모든 파일 (review 제외)
                    all_guides = []
                    for jsonl_file in staging_dir.glob("application_guides_*.jsonl"):
                        if "review" not in jsonl_file.name.lower():
                            with open(jsonl_file, "r", encoding="utf-8") as f:
                                for line in f:
                                    if line.strip():
                                        all_guides.append(json.loads(line))

                # VectorDB 재빌드
                builder.add_guides_to_db(all_guides, batch_size=50)

                progress_bar.progress(100)
                status_text.text("✅ All steps completed!")

                # 결과 표시
                st.success(f"""
                ### ✅ 처리 완료!

                - **추출된 가이드라인**: {len(guides)}개
                - **저장 위치**: `{Path(output_file).name}`
                - **VectorDB**: 업데이트 완료 (총 {len(all_guides)}개)
                """)

                # 샘플 표시
                st.markdown("---")
                st.subheader("📋 추출된 가이드라인 샘플")

                for i, guide in enumerate(guides[:3]):
                    with st.expander(f"Guide {i+1}: {guide.scenario[:100]}..."):
                        st.json(guide.dict())

                # 다음 단계 안내
                st.info("""
                ### 🎯 다음 단계

                1. **🔍 Search Guidelines** 페이지에서 검색 테스트
                2. 필요시 `review_queue.csv` 확인하여 낮은 신뢰도 항목 검토
                3. 중복 제거: `python scripts/guidelines/validate_and_dedup.py` 실행
                """)

        except Exception as e:
            st.error(f"❌ 처리 중 오류 발생: {str(e)}")
            st.exception(e)

        finally:
            # 임시 파일 삭제
            try:
                os.unlink(tmp_path)
            except:
                pass

else:
    st.warning("""
    ### ⚠️ 처리 전 확인 사항

    - ✅ PDF 파일 업로드
    - ✅ 발행 기관 선택
    - ✅ OpenAI API Key 설정 (`.env` 파일)
    """)

# 기존 파일 목록
st.markdown("---")
st.subheader("📂 Existing Guidelines Files")

staging_dir = Path("data/staging")
if staging_dir.exists():
    jsonl_files = [f for f in staging_dir.glob("application_guides_*.jsonl")
                   if "review" not in f.name.lower() and "duplicates" not in f.name.lower()]

    if jsonl_files:
        st.info(f"총 {len(jsonl_files)}개 파일 (타임스탬프 기반 고유 파일명)")

        for jsonl_file in sorted(jsonl_files, reverse=True)[:10]:  # 최근 10개만
            file_size = jsonl_file.stat().st_size / 1024  # KB
            line_count = sum(1 for line in open(jsonl_file, encoding="utf-8") if line.strip())

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            col1.text(f"📄 {jsonl_file.name}")
            col2.text(f"{line_count} guides")
            col3.text(f"{file_size:.1f} KB")

            # 미리보기 버튼
            if col4.button("Preview", key=f"preview_{jsonl_file.name}"):
                with st.expander(f"Preview: {jsonl_file.name}", expanded=True):
                    with open(jsonl_file, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f):
                            if i >= 3:
                                break
                            if line.strip():
                                st.json(json.loads(line))
    else:
        st.info("아직 처리된 파일이 없습니다.")
else:
    st.info("staging 디렉토리가 생성되지 않았습니다.")
