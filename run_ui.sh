#!/bin/bash

# Ragnaforge RAG 시스템 UI 실행 스크립트

echo "🔍 Ragnaforge RAG 시스템 UI 시작"
echo "=================================="

# 현재 디렉토리 확인
if [ ! -f "streamlit_simple.py" ]; then
    echo "❌ streamlit_simple.py 파일을 찾을 수 없습니다."
    echo "   프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

# Streamlit 의존성 설치 확인
echo "📦 의존성 확인 중..."
if [ -f "requirements_streamlit.txt" ]; then
    pip install -r requirements_streamlit.txt > /dev/null 2>&1
    echo "✅ 의존성 설치 완료"
else
    echo "⚠️  requirements_streamlit.txt 파일이 없습니다. 기본 패키지를 설치합니다."
    pip install streamlit plotly requests pandas > /dev/null 2>&1
fi

# FastAPI 서버 상태 확인 (선택사항)
echo "🔍 FastAPI 서버 상태 확인 중..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ FastAPI 서버가 실행 중입니다"
else
    echo "⚠️  FastAPI 서버가 실행되지 않고 있습니다."
    echo "   다른 터미널에서 'python main.py'로 서버를 시작해주세요."
fi

echo ""
echo "🚀 Streamlit UI 시작 중..."
echo "브라우저에서 http://localhost:8501 로 접속하세요"
echo ""
echo "⚠️  주의사항:"
echo "   - FastAPI 서버가 http://localhost:8000 에서 실행 중이어야 합니다"
echo "   - API 키: sk-ragnaforge-v1-test-key-12345"
echo "   - 종료하려면 Ctrl+C를 누르세요"
echo ""

# Streamlit 앱 실행
streamlit run streamlit_simple.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false
