# Streamlit UI - Quick Start Guide

## 🚀 빠른 시작

### 1. Streamlit 설치

```bash
cd guardcap-rag

# 의존성 설치 (Streamlit 포함)
pip install -r requirements.txt

# 또는 Streamlit만 설치
pip install streamlit>=1.30.0
```

### 2. 환경 설정

`.env` 파일에 OpenAI API 키 설정:

```bash
# .env 파일 생성 (없다면)
cp .env.example .env

# .env 편집하여 API 키 추가
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### 3. Streamlit 앱 실행

```bash
streamlit run streamlit_app/Home.py
```

브라우저가 자동으로 `http://localhost:8501` 열림

## 📱 사용법

### PDF 업로드 및 처리

1. **📄 Upload PDF** 페이지로 이동
2. PDF 파일 드래그 앤 드롭
3. 발행 기관 선택 (개인정보보호위원회, 금융보안원 등)
4. **Process PDF** 버튼 클릭
5. 처리 완료까지 대기 (63페이지 기준 2-5분)

### 가이드라인 검색

1. **🔍 Search Guidelines** 페이지로 이동
2. 검색어 입력:
   - "고객에게 견적서 발송 시 개인정보 처리"
   - "마케팅 이메일 동의 필요 여부"
3. 필터 설정 (선택사항):
   - 발신자/수신자 유형
   - 발행 기관
4. **Search** 버튼 클릭
5. 결과 확인 및 상세 정보 열람

## 🎨 주요 기능

### 📄 Upload PDF 페이지

- **자동 OCR**: OpenAI GPT-4o Vision으로 스캔 PDF도 처리
- **배치 처리**: 대용량 PDF 자동 분할 처리
- **실시간 진행**: 처리 단계별 진행률 표시
- **자동 VectorDB 추가**: 처리 완료 즉시 검색 가능

### 🔍 Search Guidelines 페이지

- **자연어 검색**: 복잡한 쿼리 문법 불필요
- **컨텍스트 필터**: 발신자/수신자 타입으로 정확도 향상
- **유사도 점수**: 🟢🟡🔴 색상으로 관련성 표시
- **상세 정보**: 시나리오, 해석, 실행 지침, 관련 법령 모두 표시

## ⚡ 성능 최적화

### 빠른 처리 (품질 타협 가능)

`.env` 파일:
```bash
OPENAI_VISION_MODEL=gpt-4o-mini
PDF_BATCH_SIZE=20
```

**효과**: 63페이지 PDF → 2-3분

### 고품질 처리 (시간 여유)

```bash
OPENAI_VISION_MODEL=gpt-4o
PDF_BATCH_SIZE=15
```

**효과**: 63페이지 PDF → 5-7분 (정확도 높음)

## 🐛 트러블슈팅

### "OPENAI_API_KEY not set"

```bash
# .env 파일 확인
cat .env | grep OPENAI_API_KEY

# 없으면 추가
echo "OPENAI_API_KEY=sk-proj-..." >> .env
```

### "VectorDB not found"

**방법 1**: Streamlit에서 PDF 업로드 (자동 생성)

**방법 2**: CLI로 직접 빌드
```bash
python scripts/guidelines/build_guides_vectordb.py
```

### 포트 충돌

```bash
# 다른 포트로 실행
streamlit run streamlit_app/Home.py --server.port 8080
```

### PDF 처리 실패

```bash
# 배치 크기 줄이기
PDF_BATCH_SIZE=10  # .env에 추가

# 재시도
```

## 📊 파일 구조

```
guardcap-rag/
├── streamlit_app/
│   ├── Home.py                     # 메인 페이지
│   ├── pages/
│   │   ├── 1_📄_Upload_PDF.py     # PDF 업로드
│   │   └── 2_🔍_Search_Guidelines.py  # 검색
│   └── README.md                   # 상세 문서
│
├── data/
│   ├── raw_guidelines/             # 원본 PDF
│   ├── staging/application_guides/ # 처리된 JSONL
│   └── chromadb/application_guides/  # VectorDB
│
└── scripts/guidelines/             # 백엔드 스크립트
```

## 🔗 관련 문서

- **상세 사용법**: [streamlit_app/README.md](streamlit_app/README.md)
- **PDF 처리 파이프라인**: [scripts/guidelines/README.md](scripts/guidelines/README.md)
- **프로젝트 개요**: [CLAUDE.md](CLAUDE.md)

## 💡 사용 예시

### 예시 1: 새 가이드 추가

```
1. Streamlit 실행: streamlit run streamlit_app/Home.py
2. 📄 Upload PDF 클릭
3. "금융보안원_클라우드컴퓨팅_가이드.pdf" 업로드
4. 발행 기관: "금융보안원" 선택
5. Process PDF 클릭 → 3-5분 대기
6. 완료 후 🔍 Search에서 "클라우드 개인정보" 검색
```

### 예시 2: 실무 상황 검색

```
1. 🔍 Search Guidelines 클릭
2. 검색어: "외부 협력사에게 고객 계좌번호 전송"
3. 필터:
   - 발신자: internal
   - 수신자: partner
4. Search → 관련 가이드라인 3-5개 표시
5. 유사도 80% 이상 결과 위주로 검토
6. 관련 법령 확인 (예: 개인정보보호법 제17조)
```

## 🎯 다음 단계

Streamlit 앱이 잘 작동하면:

1. **더 많은 PDF 추가**: 실무 가이드라인 계속 업로드
2. **중복 제거**: `python scripts/guidelines/validate_and_dedup.py` 실행
3. **API 활용**: FastAPI 서버와 병행 사용
4. **프로덕션 배포**: Docker 또는 Streamlit Cloud

---

**문제 발생 시**: [streamlit_app/README.md](streamlit_app/README.md) 참조 또는 이슈 등록
