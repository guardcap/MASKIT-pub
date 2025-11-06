"""
VectorDB 검색 페이지
"""

import streamlit as st
from pathlib import Path
import json
import sys
import os
from typing import List, Dict

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Search Guidelines - Guardcap RAG",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Search Application Guidelines")
st.markdown("---")


class GuidelinesSearcher:
    """가이드라인 검색 클래스"""

    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

        # ChromaDB 연결
        db_path = Path("data/chromadb/application_guides")
        if not db_path.exists():
            raise FileNotFoundError(f"VectorDB not found at {db_path}")

        self.chroma_client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.chroma_client.get_collection("application_guides")

    def get_embedding(self, text: str) -> List[float]:
        """텍스트를 임베딩 벡터로 변환"""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    def search(
        self,
        query: str,
        top_k: int = 5,
        sender_type: str = None,
        receiver_type: str = None,
        authority: str = None
    ) -> List[Dict]:
        """가이드라인 검색"""

        # 쿼리 임베딩
        query_embedding = self.get_embedding(query)

        # 메타데이터 필터 구성
        where_filters = {}
        if sender_type:
            where_filters["context.sender_type"] = sender_type
        if receiver_type:
            where_filters["context.receiver_type"] = receiver_type
        if authority:
            where_filters["source_authority"] = authority

        # ChromaDB 검색
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filters if where_filters else None,
            include=["documents", "metadatas", "distances"]
        )

        # 결과 포맷팅
        formatted_results = []
        if results and results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i],
                    "similarity": 1 - results['distances'][0][i]  # cosine distance to similarity
                })

        return formatted_results


# 사이드바 필터
with st.sidebar:
    st.header("🔧 Search Filters")

    sender_type_filter = st.selectbox(
        "발신자 유형",
        ["전체", "internal", "external_customer", "partner", "regulatory"],
        help="이메일 발신자의 유형"
    )

    receiver_type_filter = st.selectbox(
        "수신자 유형",
        ["전체", "internal", "external_customer", "partner", "regulatory"],
        help="이메일 수신자의 유형"
    )

    authority_filter = st.selectbox(
        "발행 기관",
        ["전체", "개인정보보호위원회", "금융보안원", "금융위원회", "공정거래위원회", "KISA (한국인터넷진흥원)"]
    )

    st.markdown("---")

    top_k = st.slider(
        "검색 결과 수",
        min_value=1,
        max_value=20,
        value=5,
        help="표시할 검색 결과 개수"
    )

    st.markdown("---")

    # VectorDB 상태
    st.subheader("📊 VectorDB Stats")
    try:
        db_path = Path("data/chromadb/application_guides")
        if db_path.exists():
            client = chromadb.PersistentClient(path=str(db_path))
            collection = client.get_collection("application_guides")
            st.metric("Total Guides", collection.count())
        else:
            st.warning("VectorDB not found")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# 메인 검색 UI
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("❌ OPENAI_API_KEY not set. Please configure `.env` file.")
    st.stop()

# 검색 입력
st.subheader("💬 검색어 입력")

col1, col2 = st.columns([4, 1])

with col1:
    query = st.text_input(
        "검색어",
        placeholder="예: 고객에게 견적서 발송 시 개인정보 처리 방법",
        label_visibility="collapsed"
    )

with col2:
    search_button = st.button("🔍 Search", type="primary", use_container_width=True)

# 예시 쿼리
st.markdown("**예시 쿼리:**")
example_queries = [
    "고객이 먼저 문의한 경우 개인정보 수집",
    "마케팅 이메일 발송 시 동의 필요 여부",
    "외부 협력사에게 고객 정보 전달",
    "금융 거래 정보 제3자 제공"
]

cols = st.columns(4)
for i, example in enumerate(example_queries):
    if cols[i].button(example, key=f"example_{i}"):
        query = example
        search_button = True

st.markdown("---")

# 검색 실행
if search_button and query:
    try:
        searcher = GuidelinesSearcher(openai_api_key=api_key)

        # 필터 처리
        sender = sender_type_filter if sender_type_filter != "전체" else None
        receiver = receiver_type_filter if receiver_type_filter != "전체" else None
        auth = authority_filter if authority_filter != "전체" else None

        with st.spinner("🔍 Searching..."):
            results = searcher.search(
                query=query,
                top_k=top_k,
                sender_type=sender,
                receiver_type=receiver,
                authority=auth
            )

        # 검색 결과 표시
        if not results:
            st.warning("검색 결과가 없습니다.")
        else:
            st.success(f"✅ {len(results)}개의 가이드라인을 찾았습니다.")

            for i, result in enumerate(results):
                metadata = result['metadata']
                similarity_score = result['similarity']

                # 유사도에 따른 색상
                if similarity_score > 0.8:
                    badge_color = "🟢"
                elif similarity_score > 0.6:
                    badge_color = "🟡"
                else:
                    badge_color = "🔴"

                with st.expander(
                    f"{badge_color} **Result {i+1}** | Similarity: {similarity_score:.2%} | {metadata.get('scenario', 'N/A')[:100]}...",
                    expanded=(i == 0)
                ):
                    # 기본 정보
                    col1, col2, col3 = st.columns(3)
                    col1.metric("발행 기관", metadata.get('source_authority', 'N/A'))
                    col2.metric("문서", metadata.get('source_document', 'N/A'))
                    col3.metric("유사도", f"{similarity_score:.2%}")

                    st.markdown("---")

                    # 시나리오
                    st.markdown("### 📋 시나리오")
                    st.markdown(metadata.get('scenario', 'N/A'))

                    # 컨텍스트
                    if 'context' in metadata and metadata['context']:
                        st.markdown("### 🔍 컨텍스트")
                        context = metadata['context']
                        if isinstance(context, str):
                            try:
                                context = json.loads(context)
                            except:
                                pass

                        if isinstance(context, dict):
                            ctx_cols = st.columns(4)
                            ctx_cols[0].metric("발신자", context.get('sender_type', 'N/A'))
                            ctx_cols[1].metric("수신자", context.get('receiver_type', 'N/A'))
                            ctx_cols[2].metric("목적", context.get('email_purpose', 'N/A'))
                            if 'pii_types' in context and context['pii_types']:
                                ctx_cols[3].metric("PII 유형", len(context['pii_types']))

                    # 해석
                    st.markdown("### 📖 해석")
                    st.markdown(metadata.get('interpretation', 'N/A'))

                    # 실행 지침
                    st.markdown("### ✅ 실행 지침")
                    directive = metadata.get('actionable_directive', 'N/A')
                    if "마스킹" in directive.lower() or "mask" in directive.lower():
                        st.warning(directive)
                    else:
                        st.info(directive)

                    # 관련 법령
                    if 'related_law_ids' in metadata and metadata['related_law_ids']:
                        st.markdown("### ⚖️ 관련 법령")
                        laws = metadata['related_law_ids']
                        if isinstance(laws, str):
                            try:
                                laws = json.loads(laws)
                            except:
                                laws = [laws]
                        st.write(", ".join(laws))

                    # 키워드
                    if 'keywords' in metadata and metadata['keywords']:
                        st.markdown("### 🏷️ 키워드")
                        keywords = metadata['keywords']
                        if isinstance(keywords, str):
                            try:
                                keywords = json.loads(keywords)
                            except:
                                keywords = [keywords]
                        st.write(" • ".join(keywords))

                    # 예시
                    if 'examples' in metadata and metadata['examples']:
                        st.markdown("### 💡 예시")
                        examples = metadata['examples']
                        if isinstance(examples, str):
                            try:
                                examples = json.loads(examples)
                            except:
                                examples = []

                        if isinstance(examples, list) and examples:
                            for j, example in enumerate(examples[:3]):
                                if isinstance(example, dict):
                                    st.markdown(f"**예시 {j+1}**: {example.get('case_description', 'N/A')}")
                                    st.markdown(f"- 결정: `{example.get('masking_decision', 'N/A')}`")
                                    st.markdown(f"- 근거: {example.get('reasoning', 'N/A')}")

                    # 원본 JSON (접기)
                    with st.expander("🔍 원본 JSON"):
                        st.json(metadata)

    except FileNotFoundError as e:
        st.error(f"❌ VectorDB를 찾을 수 없습니다: {str(e)}")
        st.info("""
        ### VectorDB 생성 방법

        1. PDF 업로드 페이지에서 PDF 처리
        2. 또는 CLI에서 직접 빌드:
           ```bash
           python scripts/guidelines/build_guides_vectordb.py
           ```
        """)

    except Exception as e:
        st.error(f"❌ 검색 중 오류 발생: {str(e)}")
        st.exception(e)

elif search_button and not query:
    st.warning("검색어를 입력해주세요.")

# 통계 및 인사이트
st.markdown("---")
st.subheader("📊 검색 통계 및 팁")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🎯 효과적인 검색 팁

    1. **구체적인 시나리오 입력**
       - ❌ "개인정보"
       - ✅ "고객에게 견적서 이메일 발송 시 개인정보 처리"

    2. **컨텍스트 필터 활용**
       - 발신자/수신자 유형 필터로 정확도 향상
       - 특정 기관의 가이드라인만 검색

    3. **여러 검색어 시도**
       - 동의어 활용 (예: "수집" ↔ "취득")
       - 법령명 포함 (예: "개인정보보호법 제15조")
    """)

with col2:
    st.markdown("""
    ### 📈 유사도 점수 해석

    - **🟢 80% 이상**: 매우 관련성 높음
    - **🟡 60-80%**: 관련성 있음
    - **🔴 60% 미만**: 참고용

    ### 🔗 관련 기능

    - [📄 Upload PDF](/Upload_PDF): 새 가이드라인 추가
    - [🏠 Home](/): 시스템 개요
    """)
