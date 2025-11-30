#!/bin/bash

# Guardcap RAG Streamlit App 실행 스크립트

set -e

echo "================================================"
echo "Guardcap RAG - Streamlit UI"
echo "================================================"
echo ""

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo ""

    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ Error: OPENAI_API_KEY not set!"
        echo ""
        echo "Please either:"
        echo "1. Create .env file: cp .env.example .env"
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

# Python 실행 파일 결정
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
    echo "🐍 Using virtual environment: $PYTHON"
elif [ -f "../venv/bin/python" ]; then
    PYTHON="../venv/bin/python"
    echo "🐍 Using virtual environment: $PYTHON"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
    echo "🐍 Using system python3"
else
    echo "❌ Error: Python not found!"
    exit 1
fi

# Streamlit 설치 확인
echo ""
echo "Checking Streamlit installation..."
if ! $PYTHON -c "import streamlit" 2>/dev/null; then
    echo "⚠️  Streamlit not installed"
    echo "Installing Streamlit..."
    $PYTHON -m pip install "streamlit>=1.30.0"
else
    echo "✅ Streamlit installed"
fi

# VectorDB 확인
echo ""
echo "Checking VectorDB..."
if [ -d "data/chromadb/application_guides" ]; then
    echo "✅ VectorDB found"
else
    echo "⚠️  VectorDB not found"
    echo "   Upload a PDF in the Streamlit app to create it"
fi

echo ""
echo "================================================"
echo "🚀 Starting Streamlit App..."
echo "================================================"
echo ""
echo "Access the app at: http://localhost:8501"
echo "Press Ctrl+C to stop"
echo ""

# Streamlit 실행
$PYTHON -m streamlit run streamlit_app/Home.py
