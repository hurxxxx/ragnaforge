#!/bin/bash

API_BASE="http://127.0.0.1:8000"
API_KEY="sk-kure-v1-test-key-12345"

echo "🚀 간단한 검색어 테스트"
echo ""

# 테스트 문서 생성 및 업로드
echo "=== 테스트 문서 업로드 ==="

# 기술 문서
cat > tech_doc.txt << 'EOF'
인공지능과 머신러닝 기술 개요

인공지능(AI)은 컴퓨터가 인간의 지능을 모방하여 학습, 추론, 문제 해결 등을 수행하는 기술입니다.
머신러닝은 AI의 하위 분야로, 데이터를 통해 패턴을 학습하고 예측을 수행합니다.

주요 기술:
- 딥러닝: 신경망을 이용한 학습
- 자연어처리: 텍스트 분석 및 이해
- 컴퓨터 비전: 이미지 인식 및 분석
- 강화학습: 환경과의 상호작용을 통한 학습

Python은 AI/ML 개발에 가장 널리 사용되는 프로그래밍 언어입니다.
TensorFlow, PyTorch, scikit-learn 등의 라이브러리가 인기가 높습니다.
EOF

# 요리 문서
cat > recipe_doc.txt << 'EOF'
김치찌개 만드는 방법

재료:
- 김치 200g
- 돼지고기 150g
- 두부 1/2모
- 대파 1대
- 양파 1/2개

조리법:
1. 돼지고기를 한입 크기로 자르고 양념합니다.
2. 팬에 참기름을 두르고 돼지고기를 볶습니다.
3. 김치를 넣고 함께 볶아줍니다.
4. 물을 넣고 끓인 후 두부와 야채를 추가합니다.
5. 간을 맞추고 10분간 더 끓입니다.

맛있는 김치찌개 완성!
EOF

echo "📄 문서 업로드 중..."
curl -s -X POST -H "Authorization: Bearer $API_KEY" -F "file=@tech_doc.txt" "$API_BASE/v1/files/upload" > /dev/null
curl -s -X POST -H "Authorization: Bearer $API_KEY" -F "file=@recipe_doc.txt" "$API_BASE/v1/files/upload" > /dev/null

echo "⏳ 문서 처리 대기 (5초)..."
sleep 5

echo ""
echo "=== 검색 테스트 ==="

test_search() {
    local type=$1
    local query=$2
    local desc=$3
    
    echo "🔍 $desc"
    echo "검색어: '$query'"
    
    response=$(curl -s -X POST \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\", \"limit\": 3, \"highlight\": true}" \
        "$API_BASE/v1/search/$type")
    
    echo "결과:"
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"  성공: {data.get('success', False)}\")
    print(f\"  총 결과: {data.get('total_results', 0)}개\")
    print(f\"  검색 시간: {data.get('search_time', 0):.3f}초\")
    
    results = data.get('results', [])
    for i, result in enumerate(results[:2]):
        print(f\"  결과 {i+1}:\")
        print(f\"    ID: {result.get('id', 'N/A')}\")
        print(f\"    점수: {result.get('score', 0):.3f}\")
        content = result.get('content', '')
        if len(content) > 100:
            content = content[:100] + '...'
        print(f\"    내용: {content}\")
        
        highlights = result.get('highlights')
        if highlights:
            print(f\"    하이라이트: {list(highlights.keys())}\")
except Exception as e:
    print(f\"  오류: {e}\")
    print(f\"  원본 응답: {sys.stdin.read()}\")
"
    echo ""
    echo "---"
    echo ""
}

# 1. 기본 키워드 검색
test_search "text" "인공지능" "기본 키워드 검색 (텍스트)"
test_search "vector" "머신러닝" "기본 키워드 검색 (벡터)"
test_search "hybrid" "AI 기술" "기본 키워드 검색 (하이브리드)"

# 2. 요리 관련 검색
test_search "text" "김치찌개" "요리명 검색 (텍스트)"
test_search "vector" "돼지고기 요리" "요리 재료 검색 (벡터)"
test_search "hybrid" "두부" "재료 검색 (하이브리드)"

# 3. 복합 검색어
test_search "text" "Python 프로그래밍" "복합 검색어 (텍스트)"
test_search "vector" "딥러닝 신경망" "복합 검색어 (벡터)"
test_search "hybrid" "TensorFlow 라이브러리" "복합 검색어 (하이브리드)"

# 4. 부분 일치
test_search "text" "찌개" "부분 일치 (텍스트)"
test_search "vector" "학습" "부분 일치 (벡터)"

# 5. 존재하지 않는 검색어
test_search "text" "블록체인" "존재하지 않는 검색어 (텍스트)"
test_search "vector" "우주여행" "존재하지 않는 검색어 (벡터)"

echo "🎉 검색 테스트 완료!"

# 정리
rm -f tech_doc.txt recipe_doc.txt
echo "✅ 테스트 파일 정리 완료"
