# 📁 chunk_and_save_all.py
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import pickle
import re

# ✔ 문서 로드
FILE_PATH = "policy.md"
loader = TextLoader(FILE_PATH, encoding="utf-8")
docs = loader.load()
print(f"📄 문서 로드 완료: {FILE_PATH} ({len(docs[0].page_content)}자)")

# ✔ 커스텀 청크 함수
def custom_chunk_policy_md(text):
    chunks = []
    current_chapter = ""
    current_chunk = ""
    lines = text.splitlines()

    for line in lines:
        if line.startswith("## 제"):
            if current_chunk:
                chunks.append((current_chapter, current_chunk.strip()))
                current_chunk = ""
            current_chapter = line.strip()
            current_chunk += line + "\n"
        elif line.startswith("### 제"):
            if current_chunk:
                chunks.append((current_chapter, current_chunk.strip()))
                current_chunk = ""
            current_chunk += line + "\n"
        else:
            current_chunk += line + "\n"

    if current_chunk:
        chunks.append((current_chapter, current_chunk.strip()))
    return chunks  # [(chapter_title, chunk_content)]

# ✔ 청크 생성 및 태깅
raw_text = docs[0].page_content
chunk_data = custom_chunk_policy_md(raw_text)
chunk_docs = []

for i, (chapter, content) in enumerate(chunk_data):
    metadata = {
        "source": FILE_PATH,
        "chunk_id": i + 1,
        "chapter": chapter
    }
    match = re.search(r"### (제\d+조)", content)
    metadata["section"] = match.group(1) if match else "기타"

    doc = Document(page_content=content, metadata=metadata)
    chunk_docs.append(doc)

print(f"✅ 커스텀 청크 완료: {len(chunk_docs)}개")

# ✔ 청크 텍스트 저장
OUTPUT_PATH = "chunk_output.txt"
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for doc in chunk_docs:
        meta = doc.metadata
        f.write(f"\n--- 청크 {meta['chunk_id']} ---\n")
        f.write(f"[장: {meta['chapter']}]\n")
        f.write(f"[조문: {meta['section']}]\n")
        f.write(f"[소스: {meta['source']}]\n")
        f.write(doc.page_content.strip())
        f.write("\n")
print(f"🗃 청크 + 태그 저장 완료: {OUTPUT_PATH}")

# ✔ 청크 객체 저장
with open("chunks_tagged.pkl", "wb") as f:
    pickle.dump(chunk_docs, f)
print("📆 청크 객체 저장 완료: chunks_tagged.pkl")

# ✔ 임베딩 모델 로드
embedding_model = HuggingFaceEmbeddings(
    model_name="upskyy/e5-base-korean",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

# ✔ FAISS 벡터 저장소 생성 및 저장
vectorstore = FAISS.from_documents(chunk_docs, embedding_model)
vectorstore.save_local("faiss_policy_db")
print("📆 벡터 저장소 생성 완료: faiss_policy_db")
