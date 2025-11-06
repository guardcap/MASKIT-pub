"""
Guardcap RAG - Application Guidelines Management
Streamlit App 메인 페이지
"""

import streamlit as st
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="Guardcap RAG - Guidelines Manager",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 메인 페이지
st.title("🛡️ Guardcap RAG - Application Guidelines Manager")
st.markdown("---")

# 소개
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## 📚 Overview

    **Guardcap RAG**는 개인정보보호 실무 가이드라인을 자동으로 구조화하고 검색할 수 있는 시스템입니다.

    ### 주요 기능

    1. **📄 PDF Upload & Processing**
       - 실무 가이드라인 PDF 업로드 (최대 100MB)
       - OpenAI GPT-4o Vision으로 자동 OCR 및 구조화
       - 타임스탬프 기반 고유 파일명으로 안전 저장 (`data/staging/`)
       - VectorDB에 자동 통합 (여러 소스 병합 가능)

    2. **🔍 Intelligent Search**
       - 자연어 질의로 관련 가이드라인 검색
       - Vector Similarity Search (OpenAI Embeddings)
       - 컨텍스트 필터링 (sender/receiver type, authority)

    ### 시작하기

    왼쪽 사이드바에서 원하는 페이지를 선택하세요:
    - **📄 Upload PDF**: 새로운 가이드라인 PDF 업로드 및 처리
    - **🔍 Search Guidelines**: 가이드라인 검색 및 조회
    """)

with col2:
    st.info("""
    ### 📊 시스템 상태

    - **VectorDB**: ChromaDB (Local)
    - **LLM**: OpenAI GPT-4o
    - **Embedding**: text-embedding-3-small
    """)

    # VectorDB 통계 표시
    try:
        import chromadb
        import os

        db_path = Path("data/chromadb/application_guides")
        if db_path.exists():
            client = chromadb.PersistentClient(path=str(db_path))
            try:
                collection = client.get_collection("application_guides")
                count = collection.count()
                st.success(f"✅ VectorDB: {count} guides")
            except:
                st.warning("⚠️ VectorDB: Collection not found")
        else:
            st.warning("⚠️ VectorDB: Not initialized")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

st.markdown("---")

# 사용 가이드
with st.expander("📖 사용 가이드"):
    st.markdown("""
    ### 1. PDF 업로드 및 처리

    1. 왼쪽 사이드바에서 **📄 Upload PDF** 클릭
    2. PDF 파일 업로드 (금융보안원, 개인정보보호위원회 등의 실무 가이드)
    3. 발행 기관 선택
    4. **Process PDF** 버튼 클릭
    5. 처리 완료 후 결과 확인

    #### 지원 형식
    - PDF 파일 (스캔 이미지 PDF 포함)
    - 최대 100MB
    - 한글/영문 지원

    ### 2. 가이드라인 검색

    1. 왼쪽 사이드바에서 **🔍 Search Guidelines** 클릭
    2. 검색어 입력 (예: "고객에게 견적서 발송 시 개인정보 처리")
    3. 필터 옵션 설정 (선택사항)
    4. 검색 결과 확인

    #### 검색 팁
    - 구체적인 시나리오로 검색하면 더 정확한 결과
    - 발신자/수신자 타입 필터 활용
    - 관련 법령 ID로 필터링 가능
    """)

with st.expander("⚙️ 시스템 요구사항"):
    st.markdown("""
    ### 환경 변수 설정

    `.env` 파일에 다음 설정 필요:

    ```bash
    # OpenAI API Key (필수)
    OPENAI_API_KEY=sk-proj-...

    # 모델 설정
    OPENAI_VISION_MODEL=gpt-4o-mini  # 빠른 처리
    OPENAI_EMBEDDING_MODEL=text-embedding-3-small

    # PDF 처리 설정
    PDF_BATCH_SIZE=20
    MAX_PDF_FILES=5
    ```

    ### 의존성

    ```bash
    pip install -r requirements.txt
    ```

    ### 실행

    ```bash
    cd guardcap-rag
    streamlit run streamlit_app/Home.py
    ```
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Guardcap RAG v2.0 | Built with LangGraph, ChromaDB, OpenAI</p>
</div>
""", unsafe_allow_html=True)
