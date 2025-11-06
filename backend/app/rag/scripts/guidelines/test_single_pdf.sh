#!/bin/bash

# Single PDF Test Script
# 특정 PDF 파일 하나만 테스트하는 스크립트

set -e  # 에러 발생 시 중단

echo "================================================"
echo "Single PDF Test - 금융보안 거버넌스 가이드"
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

# Python 실행 파일 결정 (가상환경 우선)
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
    echo "🐍 Using virtual environment: $PYTHON"
elif [ -f "../venv/bin/python" ]; then
    PYTHON="../venv/bin/python"
    echo "🐍 Using virtual environment: $PYTHON"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
    echo "🐍 Using system python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
    echo "🐍 Using system python"
else
    echo "❌ Error: Python not found!"
    exit 1
fi
echo ""

# 테스트할 PDF 파일 경로
TEST_PDF="data/raw_guidelines/(금융보안원) 금융보안 거버넌스 가이드.pdf"

# Step 1: PDF 파일 확인
echo "Step 1: Checking target PDF file..."

if [ ! -f "$TEST_PDF" ]; then
    echo "❌ PDF file not found: $TEST_PDF"
    echo ""
    echo "Available PDF files:"
    ls -lh data/raw_guidelines/*.pdf 2>/dev/null || echo "  (none)"
    exit 1
fi

PDF_SIZE=$(du -h "$TEST_PDF" | cut -f1)
echo "✅ Found: $(basename "$TEST_PDF") ($PDF_SIZE)"
echo ""

# Step 2: 기존 파일들 백업
echo "Step 2: Backing up existing PDF files..."
BACKUP_DIR="data/raw_guidelines_backup_$(date +%s)"
mkdir -p "$BACKUP_DIR"

# raw_guidelines에서 테스트 대상 제외한 모든 파일 임시 이동
for pdf in data/raw_guidelines/*.pdf; do
    if [ "$(basename "$pdf")" != "$(basename "$TEST_PDF")" ]; then
        mv "$pdf" "$BACKUP_DIR/" 2>/dev/null || true
    fi
done

MOVED_COUNT=$(find "$BACKUP_DIR" -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
echo "✅ Backed up $MOVED_COUNT PDF file(s) to $BACKUP_DIR"
echo "   Only testing: $(basename "$TEST_PDF")"
echo ""

# Step 3: PDF 처리 (구조화)
echo "Step 3: Processing PDF with Zerox + OpenAI..."
echo "⏳ This may take several minutes for large PDFs..."
echo ""

# MAX_PDF_FILES=1로 제한하여 하나만 처리
MAX_PDF_FILES=1 $PYTHON scripts/guidelines/process_guidelines.py

PROCESS_EXIT_CODE=$?

# Step 3.5: 백업 파일 복원
echo ""
echo "Restoring backed up files..."
if [ "$MOVED_COUNT" -gt 0 ]; then
    mv "$BACKUP_DIR"/*.pdf data/raw_guidelines/ 2>/dev/null || true
fi
rm -rf "$BACKUP_DIR"
echo "✅ Restored $MOVED_COUNT PDF file(s)"
echo ""

if [ $PROCESS_EXIT_CODE -ne 0 ]; then
    echo "❌ PDF processing failed!"
    exit 1
fi

# Step 4: 결과 확인
echo "Step 4: Checking results..."
OUTPUT_FILE="data/staging/application_guides/application_guides.jsonl"

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "❌ Output file not found: $OUTPUT_FILE"
    exit 1
fi

LINE_COUNT=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')
echo "✅ Generated $LINE_COUNT application guide(s)"
echo ""

# Step 5: 샘플 출력 표시
echo "Step 5: Sample output (first 2 guides)..."
echo "----------------------------------------"
head -n 2 "$OUTPUT_FILE" | $PYTHON -m json.tool 2>/dev/null || head -n 2 "$OUTPUT_FILE"
echo "----------------------------------------"
echo ""

# 완료
echo "================================================"
echo "✨ Test Complete!"
echo "================================================"
echo ""
echo "📊 Output Files:"
echo "  - $OUTPUT_FILE"
if [ -f "data/staging/application_guides/application_guides_review.jsonl" ]; then
    REVIEW_COUNT=$(wc -l < "data/staging/application_guides/application_guides_review.jsonl" | tr -d ' ')
    echo "  - data/staging/application_guides/application_guides_review.jsonl ($REVIEW_COUNT items)"
fi
echo ""
echo "Next steps:"
echo "  1. Review the output: cat $OUTPUT_FILE | $PYTHON -m json.tool"
echo "  2. Run validation: $PYTHON scripts/guidelines/validate_and_dedup.py"
echo "  3. Build VectorDB: $PYTHON scripts/guidelines/build_guides_vectordb.py"
echo "  4. Or run full pipeline: ./scripts/guidelines/run_pipeline.sh"
echo ""
