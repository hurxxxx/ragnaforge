#!/bin/bash

# 간단한 데이터 초기화 스크립트 (Bash 버전)
# Python 의존성 없이 실행 가능

echo "⚠️  경고: 이 스크립트는 모든 로컬 데이터를 삭제합니다!"
echo "- 로컬 스토리지 파일"
echo "- 캐시 파일"
echo "- 모델 캐시"
echo ""

read -p "정말로 로컬 데이터를 초기화하시겠습니까? (yes/no): " confirm

if [[ $confirm != "yes" && $confirm != "y" ]]; then
    echo "❌ 초기화가 취소되었습니다."
    exit 0
fi

echo "🚀 로컬 데이터 초기화 시작..."

# 1. 스토리지 디렉토리 삭제
echo "📁 스토리지 디렉토리 삭제 중..."
if [ -d "./data" ]; then
    rm -rf ./data
    echo "✅ ./data 디렉토리 삭제 완료"
fi

# 2. 모델 캐시 삭제
echo "🤖 모델 캐시 삭제 중..."
if [ -d "./models" ]; then
    rm -rf ./models
    echo "✅ ./models 디렉토리 삭제 완료"
fi

# 3. Python 캐시 삭제
echo "🧹 Python 캐시 삭제 중..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
echo "✅ Python 캐시 삭제 완료"

# 4. 스토리지 디렉토리 재생성
echo "📁 스토리지 디렉토리 재생성 중..."
mkdir -p ./data/storage/uploads
mkdir -p ./data/storage/processed
mkdir -p ./data/storage/temp
echo "✅ 스토리지 디렉토리 재생성 완료"

echo ""
echo "🎉 로컬 데이터 초기화 완료!"
echo ""
echo "⚠️  참고: Qdrant와 MeiliSearch 원격 데이터는 Python 스크립트로 초기화하세요:"
echo "python reset_all_data.py"
