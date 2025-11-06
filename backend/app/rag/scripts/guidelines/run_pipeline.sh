#!/bin/bash

# Application Guidelines Processing Pipeline
# 전체 파이프라인 자동 실행 스크립트

set -e  # 에러 발생 시 중단

echo "================================================"
echo "Application Guidelines Processing Pipeline"
echo "================================================"
echo ""

# .env 파일 확인
if [ ! -f "guardcap-rag/.env" ] && [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo ""

    # 환경변수 확인
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ Error: OPENAI_API_KEY not set!"
        echo ""
        echo "Please either:"
        echo "1. Create .env file: cp guardcap-rag/.env.example guardcap-rag/.env"
        echo "   Then edit .env and set OPENAI_API_KEY"
        echo ""
        echo "2. Or export environment variable:"
        echo "   export OPENAI_API_KEY='sk-proj-...'"
        exit 1
    else
        echo "✅ Using OPENAI_API_KEY from environment"
    fi
else
    echo "✅ Found .env file"
fi

# 프로젝트 루트로 이동
cd "$(dirname "$0")/../.."

echo "📂 Working directory: $(pwd)"
echo ""

# Step 1: PDF 파일 확인
echo "Step 1: Checking PDF files..."
PDF_COUNT=$(find data/raw_guidelines -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')

if [ "$PDF_COUNT" -eq 0 ]; then
    echo "❌ No PDF files found in data/raw_guidelines/"
    echo "Please add PDF files to data/raw_guidelines/"
    exit 1
fi

echo "✅ Found $PDF_COUNT PDF file(s)"
echo ""

# Step 2: PDF 처리 (구조화)
echo "Step 2: Processing PDFs with Zerox + OpenAI..."
python scripts/guidelines/process_guidelines.py

if [ $? -ne 0 ]; then
    echo "❌ PDF processing failed!"
    exit 1
fi
echo ""

# Step 3: 중복 제거 및 검증
echo "Step 3: Validating and removing duplicates..."
python scripts/guidelines/validate_and_dedup.py

if [ $? -ne 0 ]; then
    echo "⚠️  Validation failed, but continuing..."
fi
echo ""

# Step 4: VectorDB 빌드
echo "Step 4: Building VectorDB with ChromaDB..."
python scripts/guidelines/build_guides_vectordb.py

if [ $? -ne 0 ]; then
    echo "❌ VectorDB build failed!"
    exit 1
fi
echo ""

# 완료
echo "================================================"
echo "✨ Pipeline Complete!"
echo "================================================"
echo ""
echo "📊 Output Files:"
echo "  - data/staging/application_guides/application_guides_unique.jsonl"
echo "  - data/staging/application_guides/review_queue.csv"
echo "  - data/chromadb/application_guides/"
echo ""
echo "Next steps:"
echo "  1. Review data/staging/application_guides/review_queue.csv"
echo "  2. Integrate VectorDB with agent/retrievers.py"
echo "  3. Test with: python main_agent.py"
echo ""
