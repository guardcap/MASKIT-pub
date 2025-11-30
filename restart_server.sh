#!/bin/bash
cd backend
source venv/bin/activate
echo "환경변수 확인:"
echo "SMTP_HOST: $SMTP_HOST"
echo "SMTP_PORT: $SMTP_PORT"
echo "SMTP_USER: $SMTP_USER"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
