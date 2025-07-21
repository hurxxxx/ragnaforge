#!/bin/bash

# Ragnaforge RAG 시스템 UI 실행 스크립트

echo "🔍 Ragnaforge RAG 시스템 UI 시작"
echo "=================================="

# Streamlit 의존성 설치 확인
echo "📦 의존성 확인 중..."
pip install -r requirements_streamlit.txt

echo ""
echo "🚀 Streamlit UI 시작 중..."
echo "브라우저에서 http://localhost:8501 로 접속하세요"
echo ""
echo "⚠️  주의사항:"
echo "   - FastAPI 서버가 http://localhost:8000 에서 실행 중이어야 합니다"
echo "   - API 키: sk-ragnaforge-v1-test-key-12345"
echo ""

# Streamlit 앱 실행
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
