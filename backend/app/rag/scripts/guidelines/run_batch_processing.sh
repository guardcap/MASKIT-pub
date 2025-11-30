#!/bin/bash

# raw_guidelines 디렉토리의 모든 PDF를 배치 처리하는 스크립트

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  Raw Guidelines Batch Processing${NC}"
echo -e "${BLUE}============================================================${NC}"

# 디렉토리 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RAW_DIR="$PROJECT_ROOT/data/raw_guidelines"

echo -e "${GREEN}✓${NC} Project root: $PROJECT_ROOT"
echo -e "${GREEN}✓${NC} Raw guidelines dir: $RAW_DIR"

# raw_guidelines 디렉토리 확인
if [ ! -d "$RAW_DIR" ]; then
    echo -e "${RED}✗ Error: raw_guidelines directory not found${NC}"
    exit 1
fi

# PDF 파일 개수 확인
PDF_COUNT=$(find "$RAW_DIR" -name "*.pdf" -type f | wc -l)
echo -e "${GREEN}✓${NC} Found $PDF_COUNT PDF files"

if [ $PDF_COUNT -eq 0 ]; then
    echo -e "${RED}✗ No PDF files found in $RAW_DIR${NC}"
    exit 1
fi

# .env 파일 확인
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠ Warning: .env file not found${NC}"
    echo -e "${YELLOW}  Please create .env file with OPENAI_API_KEY${NC}"
    exit 1
fi

# OPENAI_API_KEY 확인
if ! grep -q "OPENAI_API_KEY" "$ENV_FILE"; then
    echo -e "${RED}✗ Error: OPENAI_API_KEY not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} .env file found with OPENAI_API_KEY"

# 처리 시작
echo -e "\n${BLUE}Starting batch processing...${NC}"
echo -e "${YELLOW}This will process all $PDF_COUNT PDF files${NC}"
echo -e "${YELLOW}Processing time: ~${PDF_COUNT} minutes (with rate limiting)${NC}"

cd "$PROJECT_ROOT"

# Python 스크립트 실행
python scripts/guidelines/batch_process_raw_pdfs.py

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Batch processing completed successfully!${NC}"
    echo -e "${GREEN}✓ Check batch_processing.log for details${NC}"
else
    echo -e "\n${RED}✗ Batch processing failed${NC}"
    exit 1
fi
