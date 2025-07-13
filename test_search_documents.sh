#!/bin/bash

# 다양한 검색 테스트를 위한 문서 업로드 및 검색 스크립트

API_BASE="http://127.0.0.1:8000"
API_KEY="sk-kure-v1-test-key-12345"

echo "🚀 다양한 검색어 테스트 시작"
echo "API 서버: $API_BASE"
echo "API 키: $API_KEY"
echo ""

# 테스트 문서들 생성
echo "=== 테스트 문서 생성 ==="

# 문서 1: 기술 문서
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

# 문서 2: 요리 레시피
cat > recipe_doc.txt << 'EOF'
김치찌개 만드는 방법

재료:
- 김치 200g
- 돼지고기 150g
- 두부 1/2모
- 대파 1대
- 양파 1/2개
- 마늘 3쪽
- 고춧가루 1큰술
- 참기름 1작은술

조리법:
1. 돼지고기를 한입 크기로 자르고 양념합니다.
2. 팬에 참기름을 두르고 돼지고기를 볶습니다.
3. 김치를 넣고 함께 볶아줍니다.
4. 물을 넣고 끓인 후 두부와 야채를 추가합니다.
5. 간을 맞추고 10분간 더 끓입니다.

맛있는 김치찌개 완성!
EOF

# 문서 3: 여행 가이드
cat > travel_doc.txt << 'EOF'
제주도 여행 가이드

제주도는 대한민국의 아름다운 섬으로 다양한 관광명소가 있습니다.

주요 관광지:
- 한라산: 제주도의 최고봉, 등산과 트레킹
- 성산일출봉: 일출 명소, 유네스코 세계자연유산
- 우도: 작은 섬, 자전거 여행
- 중문관광단지: 해변과 리조트
- 천지연폭포: 아름다운 폭포

제주 특산품:
- 감귤: 제주도의 대표 과일
- 흑돼지: 제주도 특산 돼지고기
- 한라봉: 제주도 특산 감귤류
- 녹차: 제주도에서 재배되는 차

교통: 항공편으로 접근 가능, 렌터카 이용 추천
EOF

# 문서 4: 건강 정보
cat > health_doc.txt << 'EOF'
건강한 생활습관 가이드

규칙적인 운동과 균형잡힌 식단은 건강한 삶의 기본입니다.

운동 권장사항:
- 유산소 운동: 주 3-4회, 30분 이상
- 근력 운동: 주 2-3회
- 스트레칭: 매일 10-15분
- 걷기: 하루 8000-10000보

영양 관리:
- 충분한 수분 섭취 (하루 2L)
- 다양한 채소와 과일 섭취
- 단백질 적절한 섭취
- 가공식품 줄이기
- 규칙적인 식사시간

수면 관리:
- 하루 7-8시간 수면
- 규칙적인 수면 패턴
- 취침 전 스마트폰 사용 자제
- 편안한 수면 환경 조성

스트레스 관리도 중요합니다.
EOF

echo "✅ 테스트 문서 4개 생성 완료"

# 문서 업로드
echo ""
echo "=== 문서 업로드 ==="

upload_file() {
    local file=$1
    local filename=$(basename "$file")
    echo "📄 업로드 중: $filename"
    
    response=$(curl -s -X POST \
        -H "Authorization: Bearer $API_KEY" \
        -F "file=@$file" \
        "$API_BASE/v1/files/upload")
    
    echo "응답: $response" | jq .
    echo ""
}

upload_file "tech_doc.txt"
upload_file "recipe_doc.txt" 
upload_file "travel_doc.txt"
upload_file "health_doc.txt"

echo "=== 문서 처리 대기 (5초) ==="
sleep 5

# 다양한 검색어 테스트
echo ""
echo "=== 다양한 검색어 테스트 ==="

test_search() {
    local search_type=$1
    local query=$2
    local description=$3
    
    echo "🔍 $description"
    echo "검색어: '$query'"
    echo "검색 타입: $search_type"
    
    case $search_type in
        "text")
            endpoint="$API_BASE/v1/search/text"
            ;;
        "vector")
            endpoint="$API_BASE/v1/search/vector"
            ;;
        "hybrid")
            endpoint="$API_BASE/v1/search/hybrid"
            ;;
    esac
    
    response=$(curl -s -X POST \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\", \"limit\": 3, \"highlight\": true}" \
        "$endpoint")
    
    echo "결과:"
    echo "$response" | jq '{
        success: .success,
        total_results: .total_results,
        search_time: .search_time,
        results: .results | map({
            id: .id,
            score: .score,
            content: .content[0:100] + "...",
            highlights: .highlights
        })
    }'
    echo ""
    echo "---"
    echo ""
}

# 1. 기술 관련 검색
test_search "text" "인공지능" "기술 용어 검색 (텍스트)"
test_search "vector" "머신러닝과 딥러닝" "기술 개념 검색 (벡터)"
test_search "hybrid" "Python 프로그래밍" "프로그래밍 언어 검색 (하이브리드)"

# 2. 요리 관련 검색
test_search "text" "김치찌개" "요리명 검색 (텍스트)"
test_search "vector" "돼지고기 요리 만들기" "요리 방법 검색 (벡터)"
test_search "hybrid" "두부 재료" "재료 검색 (하이브리드)"

# 3. 여행 관련 검색
test_search "text" "제주도" "지역명 검색 (텍스트)"
test_search "vector" "한라산 등산" "관광지 활동 검색 (벡터)"
test_search "hybrid" "감귤 특산품" "특산품 검색 (하이브리드)"

# 4. 건강 관련 검색
test_search "text" "운동" "건강 키워드 검색 (텍스트)"
test_search "vector" "건강한 식단 관리" "건강 관리 검색 (벡터)"
test_search "hybrid" "수면 패턴" "생활습관 검색 (하이브리드)"

# 5. 복합 검색어
test_search "text" "제주도 흑돼지" "복합 키워드 검색 (텍스트)"
test_search "vector" "건강한 운동과 영양 관리" "복합 개념 검색 (벡터)"
test_search "hybrid" "AI 기술과 Python" "기술 조합 검색 (하이브리드)"

# 6. 한글/영어 혼합
test_search "text" "TensorFlow 라이브러리" "한영 혼합 검색 (텍스트)"
test_search "vector" "machine learning 머신러닝" "한영 동의어 검색 (벡터)"

# 7. 부분 일치 검색
test_search "text" "찌개" "부분 단어 검색 (텍스트)"
test_search "vector" "섬 여행" "일반적 개념 검색 (벡터)"

# 8. 존재하지 않는 검색어
test_search "text" "블록체인 암호화폐" "존재하지 않는 내용 검색 (텍스트)"
test_search "vector" "우주여행 화성탐사" "존재하지 않는 내용 검색 (벡터)"

echo "🎉 모든 검색 테스트 완료!"

# 정리
rm -f tech_doc.txt recipe_doc.txt travel_doc.txt health_doc.txt
echo "✅ 테스트 파일 정리 완료"
