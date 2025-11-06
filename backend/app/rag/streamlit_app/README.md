# Guardcap RAG - Streamlit App

실무 가이드라인 PDF 업로드 및 검색을 위한 웹 인터페이스

## 특징

- **📄 PDF Upload**: 실무 가이드라인 PDF를 드래그 앤 드롭으로 업로드 및 자동 처리
- **🔍 Smart Search**: 자연어 질의로 관련 가이드라인을 빠르게 검색
- **🎯 Context-Aware**: 발신자/수신자 타입, 발행 기관 등으로 필터링
- **📊 Real-time Stats**: VectorDB 통계 및 처리 진행 상황 실시간 표시

## 설치 및 실행

### 1. 의존성 설치

```bash
cd guardcap-rag

# Streamlit 포함 모든 의존성 설치
pip install -r requirements.txt

# 또는 Streamlit만 추가 설치
pip install streamlit>=1.30.0
```

### 2. 환경 변수 설정

`.env` 파일에 OpenAI API 키 설정 필요:

```bash
# .env
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_VISION_MODEL=gpt-4o-mini  # 빠른 처리
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# PDF 처리 설정
PDF_BATCH_SIZE=20
MAX_PDF_FILES=5
```

### 3. Streamlit 앱 실행

```bash
cd guardcap-rag
streamlit run streamlit_app/Home.py
```

브라우저에서 자동으로 `http://localhost:8501` 열림

### 4. 포트 변경 (선택사항)

```bash
streamlit run streamlit_app/Home.py --server.port 8080
```

## 페이지 구조

```
streamlit_app/
├── Home.py                          # 메인 페이지 (시스템 개요)
└── pages/
    ├── 1_📄_Upload_PDF.py          # PDF 업로드 및 처리
    └── 2_🔍_Search_Guidelines.py   # 가이드라인 검색
```

## 사용법

### 📄 Page 1: Upload PDF

1. **PDF 파일 업로드**
   - 드래그 앤 드롭 또는 파일 선택
   - 최대 100MB 지원

2. **발행 기관 선택**
   - 개인정보보호위원회, 금융보안원, 금융위원회 등
   - 기타 선택 시 직접 입력 가능

3. **Processing Options**
   - Vision Model: `gpt-4o-mini` (빠름) vs `gpt-4o` (정확)
   - 배치 크기: 5-30 페이지 (기본 20)

4. **Process PDF 버튼 클릭**
   - 자동으로 OCR → 구조화 → VectorDB 저장
   - 진행 상황 실시간 표시

5. **결과 확인**
   - 추출된 가이드라인 샘플 표시
   - JSONL 파일 경로 확인
   - 필요 시 review_queue 검토

### 🔍 Page 2: Search Guidelines

1. **검색어 입력**
   - 자연어 질의 (예: "고객에게 견적서 발송 시 개인정보 처리")
   - 또는 예시 쿼리 버튼 클릭

2. **필터 설정 (선택사항)**
   - **발신자 유형**: internal, external_customer, partner, regulatory
   - **수신자 유형**: 동일
   - **발행 기관**: 특정 기관 가이드라인만 검색
   - **검색 결과 수**: 1-20개

3. **검색 실행**
   - 유사도 점수와 함께 결과 표시
   - 🟢 80%+ : 매우 관련성 높음
   - 🟡 60-80% : 관련성 있음
   - 🔴 60%- : 참고용

4. **결과 상세 확인**
   - 시나리오, 해석, 실행 지침
   - 관련 법령, 키워드, 예시
   - 원본 JSON 데이터

## 예시 워크플로우

### 시나리오 1: 새 가이드라인 추가

```bash
# 1. Streamlit 앱 실행
streamlit run streamlit_app/Home.py

# 2. 📄 Upload PDF 페이지로 이동

# 3. "개인정보보호_실무가이드_2024.pdf" 업로드

# 4. 발행 기관: "개인정보보호위원회" 선택

# 5. Vision Model: "gpt-4o-mini" 선택 (빠른 처리)

# 6. Process PDF 클릭

# 7. 완료 후 🔍 Search Guidelines에서 테스트
```

### 시나리오 2: 기존 가이드라인 검색

```bash
# 1. 🔍 Search Guidelines 페이지

# 2. 검색어 입력: "외부 협력사에게 고객 정보 전달"

# 3. 필터 설정:
#    - 발신자: internal
#    - 수신자: partner

# 4. Search 버튼 클릭

# 5. 결과 확인 및 관련 법령/지침 검토
```

## 성능 최적화

### PDF 처리 속도 향상

**.env 설정 조정**:
```bash
# 빠른 처리 우선
OPENAI_VISION_MODEL=gpt-4o-mini
PDF_BATCH_SIZE=20

# 품질 우선
OPENAI_VISION_MODEL=gpt-4o
PDF_BATCH_SIZE=15
```

**예상 처리 시간**:
- 30페이지 PDF: 2-3분 (mini), 5-7분 (gpt-4o)
- 100페이지 PDF: 7-12분 (mini), 15-20분 (gpt-4o)

### 검색 속도

- ChromaDB는 로컬 디스크 기반으로 빠름
- 첫 검색은 약간 느릴 수 있음 (인덱스 로딩)
- 이후 검색은 밀리초 단위

## 트러블슈팅

### 1. "OPENAI_API_KEY not set" 에러

```bash
# .env 파일 확인
cat guardcap-rag/.env

# 또는 직접 설정
export OPENAI_API_KEY=sk-proj-...
```

### 2. "VectorDB not found" 에러

```bash
# CLI로 VectorDB 빌드
cd guardcap-rag
python scripts/guidelines/build_guides_vectordb.py

# 또는 Streamlit에서 PDF 업로드하여 자동 생성
```

### 3. PDF 처리 실패

**원인**: Vision API timeout, 메모리 부족

**해결책**:
```bash
# 배치 크기 줄이기
PDF_BATCH_SIZE=10  # .env에 추가

# 또는 CLI로 직접 처리
python scripts/guidelines/process_guidelines.py
```

### 4. Import 에러

```bash
# 전체 의존성 재설치
pip install -r requirements.txt --upgrade

# Streamlit 재설치
pip install streamlit --upgrade
```

### 5. 포트 이미 사용 중

```bash
# 다른 포트로 실행
streamlit run streamlit_app/Home.py --server.port 8080
```

## 커스터마이징

### 새 페이지 추가

```python
# streamlit_app/pages/3_📊_Analytics.py
import streamlit as st

st.set_page_config(page_title="Analytics", page_icon="📊")
st.title("📊 Analytics Dashboard")

# 커스텀 로직...
```

### 테마 변경

`.streamlit/config.toml` 생성:
```toml
[theme]
primaryColor="#FF4B4B"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F0F2F6"
textColor="#262730"
font="sans serif"
```

### 인증 추가

```python
# streamlit_app/Home.py 상단에 추가
import streamlit_authenticator as stauth

# 인증 로직
authenticator = stauth.Authenticate(...)
name, authentication_status, username = authenticator.login('Login', 'main')

if not authentication_status:
    st.stop()
```

## 배포

### Streamlit Cloud

1. GitHub에 푸시
2. [share.streamlit.io](https://share.streamlit.io) 접속
3. 레포지토리 연결
4. Secrets 설정 (OPENAI_API_KEY)
5. 배포

### Docker

```dockerfile
FROM python:3.11

WORKDIR /app
COPY guardcap-rag/ /app/

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app/Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# 빌드 및 실행
docker build -t guardcap-rag .
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... guardcap-rag
```

## API vs Streamlit

**Streamlit (현재)**:
- ✅ 빠른 프로토타이핑
- ✅ 비개발자도 사용 가능
- ✅ 실시간 시각화
- ❌ REST API 미지원

**FastAPI** (기존):
```bash
# API 서버 실행
uvicorn api.main:app --port 8000

# Streamlit과 병행 사용 가능
```

둘 다 실행하여 Streamlit은 UI, FastAPI는 프로그래밍 인터페이스로 활용 가능

## 참고 자료

- [Streamlit Documentation](https://docs.streamlit.io)
- [ChromaDB Documentation](https://docs.trychroma.com)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [프로젝트 README](../README.md)

## 라이선스

본 프로젝트 라이선스 참조
