#!/bin/bash

# Streamlit UI 시작 스크립트
echo "🔍 Streamlit UI 시작..."

# 필수 패키지 설치
pip install streamlit plotly requests > /dev/null 2>&1

# Streamlit 실행
streamlit run streamlit_simple.py --server.port 8501 --server.address 0.0.0.0
