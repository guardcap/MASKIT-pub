# 📁 RAG 테스트 코드
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
import pickle

# ✔ 벡터 저장소 로드
embedding_model = HuggingFaceEmbeddings(
    model_name="upskyy/e5-base-korean",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

vectorstore = FAISS.load_local("faiss_policy_db", embedding_model, allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# ✔ LLM 로드 (Mistral via Ollama)
llm = Ollama(model="mistral")

# ✔ RAG 체인 구성
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# ✔ 사용자 질문
query = input("❓ 질문 입력: ")
result = qa_chain.invoke({"query": query})

# ✔ 답변 출력
print("\n📝 [LLM 답변]\n" + result["result"])

# ✔ 참조된 청크 출력
source_docs = result["source_documents"]
print("\n📄 [참조된 청크]")
for doc in source_docs:
    meta = doc.metadata
    preview = doc.page_content[:150].replace("\n", " ")
    print(f"- 청크ID: {meta.get('chunk_id')} / 장: {meta.get('chapter')} / 조문: {meta.get('section')}\n  내용 일부: {preview}...")
