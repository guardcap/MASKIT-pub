# 📁 run_rag_mistral.py
# pip install langchain langchain-community faiss-cpu sentence-transformers

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
import json

# -----------------------------
# 0) 입력 예시
# -----------------------------
PII_LIST = [
    {"text": "정지윤", "type": "NAME"},
    {"text": "박철수", "type": "NAME"},
    {"text": "010-1111-2222", "type": "PHONE_NUMBER"},
    {"text": "020122-4111111", "type": "RRN"},
]
USER_ROLE = "대리"       # 직급
USER_NETWORK = "외부망"  # 내부망 / 외부망
USER_HAS_CPO_APPROVAL = False  # CPO 승인 여부

# -----------------------------
# 1) 벡터 저장소 로드
# -----------------------------
embedding_model = HuggingFaceEmbeddings(
    model_name="upskyy/e5-base-korean",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

vectorstore = FAISS.load_local("faiss_policy_db", embedding_model, allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# -----------------------------
# 2) LLM (Ollama Mistral)
# -----------------------------
llm = Ollama(model="mistral")

# -----------------------------
# 3) RAG 체인
# -----------------------------
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
    chain_type="stuff",
)

# -----------------------------
# 4) 프롬프트 생성
# -----------------------------
def build_query(pii_list, role, network, cpo_approval):
    pii_lines = "\n".join([f'- text: "{x["text"]}", type: {x["type"]}' for x in pii_list])
    approval_str = "승인받음" if cpo_approval else "승인없음"


    prompt = f"""
다음은 회사의 '내부 정보보안 및 개인정보 처리 정책'(제5조, 제10조) 기반으로 판단하는 작업이다.

[사용자 전송 컨텍스트]
- 직급: {role}
- 전송망: {network}
- CPO 승인 여부: {approval_str}

[PII 리스트]
{pii_lines}

요구사항:
1) 제5조(등급별 처리 기준)와 제10조(전송 권한 및 허용 범위)에 반드시 근거하여 판단할 것.
2) 정책에 없는 해석이나 추측은 금지.
3) 각 항목별로 decision 값은 'mask' 또는 'keep' 중 하나.
4) reason은 한 줄로 핵심 근거만 작성.
5) policy_citation에는 실제 정책 문구 일부를 발췌.
6) 아래 JSON 스키마 형태로만 출력.

JSON 스키마:
{{
  "results": [
    {{
      "text": "<원문>",
      "type": "<PII 타입>",
      "decision": "mask|keep",
      "reason": "<한 줄 근거>",
      "policy_citation": "<정책 인용 일부>"
    }}
  ]
}}
"""
    return prompt.strip()

# -----------------------------
# 5) LLM 응답 JSON 파서
# -----------------------------
def safe_parse_json(raw: str, fallback_items):
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        data = json.loads(raw[start:end+1])
        if isinstance(data, dict) and "results" in data:
            return data
    except Exception:
        pass
    return {
        "results": [
            {
                "text": x["text"],
                "type": x["type"],
                "decision": "mask",
                "reason": "LLM 응답 파싱 실패로 보수적 마스킹",
                "policy_citation": ""
            } for x in fallback_items
        ]
    }

# -----------------------------
# 7) 실행
# -----------------------------
if __name__ == "__main__":
    query = build_query(PII_LIST, USER_ROLE, USER_NETWORK, USER_HAS_CPO_APPROVAL)
    rag_result = qa_chain.invoke({"query": query})
    raw_answer = rag_result["result"]
    parsed = safe_parse_json(raw_answer, PII_LIST)

    print("\n🧮 [마스킹 판단 결과 - LLM RAG]")
    for r in parsed["results"]:
        print(f'- "{r["text"]}" ({r["type"]}) → {r["decision"].upper()} | {r["reason"]}')

    print("\n📄 [참조된 정책 청크]")
    for doc in rag_result.get("source_documents", []):
        meta = doc.metadata
        preview = doc.page_content[:160].replace("\n", " ")
        print(f"- 청크ID: {meta.get('chunk_id')} / 장: {meta.get('chapter')} / 조문: {meta.get('section')}\n  내용 일부: {preview}...")
