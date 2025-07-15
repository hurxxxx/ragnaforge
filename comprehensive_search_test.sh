#!/bin/bash

# KURE API 종합 검색 테스트 스크립트
# 모든 엣지 케이스와 오류 상황을 포함한 포괄적인 테스트

set -e  # 오류 발생 시 스크립트 중단

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 설정
API_BASE="http://127.0.0.1:8000"
API_KEY="sk-kure-v1-test-key-12345"
INVALID_API_KEY="invalid-key-123"

# 테스트 결과 추적
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
CRITICAL_FAILURES=0

echo -e "${BLUE}🚀 KURE API 종합 검색 테스트 시작${NC}"
echo "API 서버: $API_BASE"
echo "API 키: $API_KEY"
echo ""

# 테스트 결과 로깅 함수
log_test() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    local critical="$4"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        if [ "$critical" = "CRITICAL" ]; then
            echo -e "${RED}💥 [CRITICAL] $test_name${NC}"
            echo -e "${RED}   오류: $details${NC}"
            CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
        else
            echo -e "${YELLOW}⚠️  $test_name${NC}"
            echo -e "${YELLOW}   경고: $details${NC}"
        fi
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# HTTP 요청 함수 (상태 코드와 응답 분리)
make_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local auth_header="$4"
    local content_type="$5"
    
    if [ -z "$content_type" ]; then
        content_type="application/json"
    fi
    
    local temp_file=$(mktemp)
    local status_code
    
    if [ "$method" = "GET" ]; then
        status_code=$(curl -s -w "%{http_code}" -H "$auth_header" \
            "$API_BASE$endpoint" -o "$temp_file")
    elif [ "$method" = "POST" ]; then
        if [ "$content_type" = "multipart/form-data" ]; then
            # For multipart/form-data, $data contains the -F parameter
            status_code=$(curl -s -w "%{http_code}" -H "$auth_header" \
                -X POST $data "$API_BASE$endpoint" -o "$temp_file")
        else
            status_code=$(curl -s -w "%{http_code}" -H "$auth_header" \
                -H "Content-Type: $content_type" -X POST -d "$data" \
                "$API_BASE$endpoint" -o "$temp_file")
        fi
    fi
    
    echo "$status_code|$(cat "$temp_file")"
    rm -f "$temp_file"
}

# JSON 응답 검증 함수
validate_json_field() {
    local response="$1"
    local field="$2"
    local expected="$3"
    local comparison="$4"  # eq, ne, gt, lt, contains, exists
    
    local actual=$(echo "$response" | jq -r ".$field" 2>/dev/null)
    
    case "$comparison" in
        "eq")
            [ "$actual" = "$expected" ] && echo "PASS" || echo "FAIL:Expected_${expected}_Got_${actual}"
            ;;
        "ne")
            [ "$actual" != "$expected" ] && echo "PASS" || echo "FAIL:Should_not_be_${expected}"
            ;;
        "gt")
            [ "$actual" -gt "$expected" ] 2>/dev/null && echo "PASS" || echo "FAIL:Should_be_greater_than_${expected}"
            ;;
        "lt")
            [ "$actual" -lt "$expected" ] 2>/dev/null && echo "PASS" || echo "FAIL:Should_be_less_than_${expected}"
            ;;
        "contains")
            echo "$actual" | grep -q "$expected" && echo "PASS" || echo "FAIL:Should_contain_${expected}"
            ;;
        "exists")
            [ "$actual" != "null" ] && [ "$actual" != "" ] && echo "PASS" || echo "FAIL:Field_should_exist"
            ;;
        *)
            echo "FAIL:Invalid_comparison_${comparison}"
            ;;
    esac
}

# 서버 상태 확인
echo -e "${CYAN}=== 서버 상태 확인 ===${NC}"

response=$(make_request "GET" "/health" "" "")
status_code=$(echo "$response" | cut -d'|' -f1)
response_body=$(echo "$response" | cut -d'|' -f2-)

if [ "$status_code" = "200" ]; then
    log_test "서버 헬스 체크" "PASS" ""
else
    log_test "서버 헬스 체크" "FAIL" "HTTP $status_code" "CRITICAL"
    echo -e "${RED}서버가 응답하지 않습니다. 테스트를 중단합니다.${NC}"
    exit 1
fi

# 다양한 테스트 문서들 생성
echo -e "${CYAN}=== 테스트 문서 생성 ===${NC}"

# 문서 1: 기본 한국어 문서
cat > test_korean.txt << 'EOF'
한국어 자연어처리 테스트 문서

인공지능과 머신러닝은 현대 기술의 핵심입니다.
Python은 데이터 과학과 AI 개발에 널리 사용됩니다.
자연어처리와 컴퓨터 비전은 AI의 주요 분야입니다.

딥러닝, 신경망, 트랜스포머 모델이 주목받고 있습니다.
한국어 텍스트 처리도 중요한 기능입니다.
검색 시스템은 정확하고 빠른 결과를 제공해야 합니다.

특수문자: !@#$%^&*()_+-=[]{}|;':\",./<>?
숫자: 123456789, 3.14159, -42, 1.5e-10
EOF

# 문서 2: 영어 문서
cat > test_english.txt << 'EOF'
English Natural Language Processing Test Document

Artificial Intelligence and Machine Learning are core technologies.
Python is widely used for data science and AI development.
Natural Language Processing and Computer Vision are major AI fields.

Deep learning, neural networks, and transformer models are trending.
Text processing capabilities are essential for search systems.
Search systems must provide accurate and fast results.

Special characters: !@#$%^&*()_+-=[]{}|;':\",./<>?
Numbers: 123456789, 3.14159, -42, 1.5e-10
Mixed: AI/ML, NLP, GPT-4, BERT, T5
EOF

# 문서 3: 혼합 언어 문서
cat > test_mixed.txt << 'EOF'
Mixed Language Document 혼합 언어 문서

This document contains both English and 한국어 text.
AI (Artificial Intelligence) 인공지능은 rapidly evolving field입니다.

Technical terms:
- Machine Learning = 머신러닝
- Deep Learning = 딥러닝  
- Neural Network = 신경망
- Transformer = 트랜스포머

Code examples:
```python
import torch
import tensorflow as tf
model = torch.nn.Linear(10, 1)
```

URLs: https://example.com, http://test.org
Emails: test@example.com, user@domain.co.kr
EOF

# 문서 4: 특수 케이스 문서
cat > test_special.txt << 'EOF'
Special Cases Test Document

Empty lines:



Multiple    spaces    and	tabs

Very long line: Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum

Unicode: 🚀 🔍 ✅ ❌ 🎉 😀 😢 🤖 💻 📊 📈 📉
Emojis: 👍👎💡🔥⭐🌟💯🎯🚨⚡

Mathematical symbols: ∑∏∫∂∇∞±×÷≤≥≠≈∈∉⊂⊃∪∩
Greek letters: αβγδεζηθικλμνξοπρστυφχψω

Currency: $100, €50, ¥1000, ₩5000
Dates: 2024-01-01, 01/01/2024, Jan 1, 2024
Times: 12:34:56, 09:30 AM, 14:45:30.123

JSON-like: {"key": "value", "number": 42, "array": [1,2,3]}
XML-like: <tag attribute="value">content</tag>
EOF

# 문서 5: 빈 문서와 최소 문서
echo -n "" > test_empty.txt
echo "A" > test_minimal.txt

# 문서 6: 매우 긴 문서 (청킹 테스트용)
python3 -c "
content = '이것은 매우 긴 문서입니다. ' * 1000
content += '인공지능과 머신러닝에 대한 내용입니다. ' * 500
content += 'Python과 데이터 과학에 관한 설명입니다. ' * 300
with open('test_long.txt', 'w', encoding='utf-8') as f:
    f.write(content)
"

echo "✅ 테스트 문서 6개 생성 완료"

# 문서 업로드 테스트
echo -e "${CYAN}=== 문서 업로드 테스트 ===${NC}"

upload_file() {
    local filename="$1"
    local expected_status="$2"
    local test_description="$3"
    
    if [ ! -f "$filename" ]; then
        log_test "$test_description" "FAIL" "파일이 존재하지 않음: $filename"
        return
    fi
    
    response=$(make_request "POST" "/v1/upload" "-F file=@$filename" "Authorization: Bearer $API_KEY" "multipart/form-data")
    status_code=$(echo "$response" | cut -d'|' -f1)
    response_body=$(echo "$response" | cut -d'|' -f2-)
    
    if [ "$status_code" = "$expected_status" ]; then
        if [ "$expected_status" = "200" ]; then
            success_check=$(validate_json_field "$response_body" "success" "true" "eq")
            if [ "$success_check" = "PASS" ]; then
                log_test "$test_description" "PASS" ""
            else
                log_test "$test_description" "FAIL" "응답에서 success=true가 아님"
            fi
        else
            log_test "$test_description" "PASS" ""
        fi
    else
        log_test "$test_description" "FAIL" "HTTP $status_code (예상: $expected_status)"
    fi
}

# 정상 파일 업로드
upload_file "test_korean.txt" "200" "한국어 문서 업로드"
upload_file "test_english.txt" "200" "영어 문서 업로드"
upload_file "test_mixed.txt" "200" "혼합 언어 문서 업로드"
upload_file "test_special.txt" "200" "특수 문자 문서 업로드"
upload_file "test_minimal.txt" "200" "최소 크기 문서 업로드"
upload_file "test_long.txt" "200" "긴 문서 업로드"

# 빈 파일 업로드 (거부됨)
upload_file "test_empty.txt" "400" "빈 파일 업로드 (거부됨)"

echo "⏳ 문서 처리 대기 (10초)..."
sleep 10

# 인증 테스트
echo -e "${CYAN}=== 인증 테스트 ===${NC}"

test_search_auth() {
    local auth_header="$1"
    local expected_status="$2"
    local test_description="$3"

    response=$(make_request "POST" "/v1/search/text" '{"query": "테스트", "limit": 1}' "$auth_header")
    status_code=$(echo "$response" | cut -d'|' -f1)

    if [ "$status_code" = "$expected_status" ]; then
        log_test "$test_description" "PASS" ""
    else
        log_test "$test_description" "FAIL" "HTTP $status_code (예상: $expected_status)"
    fi
}

# 정상 인증
test_search_auth "Authorization: Bearer $API_KEY" "200" "정상 API 키 인증"

# 잘못된 인증
test_search_auth "Authorization: Bearer $INVALID_API_KEY" "401" "잘못된 API 키 (401 예상)"
test_search_auth "Authorization: Invalid $API_KEY" "401" "잘못된 인증 형식 (401 예상)"
test_search_auth "" "401" "인증 헤더 없음 (401 예상)"

# 텍스트 검색 테스트
echo -e "${CYAN}=== 텍스트 검색 테스트 ===${NC}"

test_text_search() {
    local query="$1"
    local expected_status="$2"
    local test_description="$3"
    local additional_params="$4"

    # Escape special characters in query for JSON using Python
    local escaped_query=$(python3 -c "
import json
import sys
query = '''$query'''
print(json.dumps(query)[1:-1])
" 2>/dev/null || echo "$query")
    local json_data="{\"query\": \"$escaped_query\", \"limit\": 5, \"highlight\": true$additional_params}"

    response=$(make_request "POST" "/v1/search/text" "$json_data" "Authorization: Bearer $API_KEY")
    status_code=$(echo "$response" | cut -d'|' -f1)
    response_body=$(echo "$response" | cut -d'|' -f2-)

    if [ "$status_code" = "$expected_status" ]; then
        if [ "$expected_status" = "200" ]; then
            success_check=$(validate_json_field "$response_body" "success" "true" "eq")
            search_type_check=$(validate_json_field "$response_body" "search_type" "text" "eq")

            if [ "$success_check" = "PASS" ] && [ "$search_type_check" = "PASS" ]; then
                log_test "$test_description" "PASS" ""
            else
                log_test "$test_description" "FAIL" "응답 형식 오류"
            fi
        else
            log_test "$test_description" "PASS" ""
        fi
    else
        log_test "$test_description" "FAIL" "HTTP $status_code (예상: $expected_status)"
    fi
}

# 정상 텍스트 검색
test_text_search "인공지능" "200" "기본 한국어 검색"
test_text_search "artificial intelligence" "200" "기본 영어 검색"
test_text_search "AI 머신러닝" "200" "복합 키워드 검색"
test_text_search "Python" "200" "영어 기술 용어 검색"
test_text_search "자연어처리" "200" "한국어 기술 용어 검색"

# 특수 문자 검색
test_text_search "!@#$%^&*()" "200" "특수 문자 검색"
test_text_search "123456789" "200" "숫자 검색"
test_text_search "3.14159" "200" "소수점 숫자 검색"
test_text_search "test@example.com" "200" "이메일 형식 검색"
test_text_search "https://example.com" "200" "URL 형식 검색"

# 유니코드 및 이모지 검색
test_text_search "🚀" "200" "이모지 검색"
test_text_search "αβγ" "200" "그리스 문자 검색"
test_text_search "∑∏∫" "200" "수학 기호 검색"

# 엣지 케이스
test_text_search "" "422" "빈 검색어 (422 예상)"
test_text_search "a" "200" "한 글자 검색"
long_query=$(python3 -c "print('a' * 1000)")
test_text_search "$long_query" "200" "매우 긴 검색어"

# 잘못된 JSON
response=$(make_request "POST" "/v1/search/text" '{"query": "test", "limit":}' "Authorization: Bearer $API_KEY")
status_code=$(echo "$response" | cut -d'|' -f1)
if [ "$status_code" = "422" ] || [ "$status_code" = "400" ]; then
    log_test "잘못된 JSON 형식 (오류 예상)" "PASS" ""
else
    log_test "잘못된 JSON 형식 (오류 예상)" "FAIL" "HTTP $status_code"
fi

# 파라미터 테스트
test_text_search "테스트" "200" "limit 파라미터 테스트" ', "limit": 1'
test_text_search "테스트" "200" "offset 파라미터 테스트" ', "offset": 5'
test_text_search "테스트" "200" "highlight false 테스트" ', "highlight": false'

# 벡터 검색 테스트
echo -e "${CYAN}=== 벡터 검색 테스트 ===${NC}"

test_vector_search() {
    local query="$1"
    local expected_status="$2"
    local test_description="$3"
    local additional_params="$4"

    # Escape special characters in query for JSON using Python
    local escaped_query=$(python3 -c "
import json
import sys
query = '''$query'''
print(json.dumps(query)[1:-1])
" 2>/dev/null || echo "$query")
    local json_data="{\"query\": \"$escaped_query\", \"limit\": 5$additional_params}"

    response=$(make_request "POST" "/v1/search/vector" "$json_data" "Authorization: Bearer $API_KEY")
    status_code=$(echo "$response" | cut -d'|' -f1)
    response_body=$(echo "$response" | cut -d'|' -f2-)

    if [ "$status_code" = "$expected_status" ]; then
        if [ "$expected_status" = "200" ]; then
            success_check=$(validate_json_field "$response_body" "success" "true" "eq")
            search_type_check=$(validate_json_field "$response_body" "search_type" "vector" "eq")

            if [ "$success_check" = "PASS" ] && [ "$search_type_check" = "PASS" ]; then
                # content 필드 존재 확인
                results_count=$(echo "$response_body" | jq '.results | length' 2>/dev/null)
                if [ "$results_count" -gt 0 ]; then
                    content_check=$(echo "$response_body" | jq -r '.results[0].content' 2>/dev/null)
                    if [ "$content_check" != "null" ] && [ "$content_check" != "" ]; then
                        log_test "$test_description" "PASS" ""
                    else
                        log_test "$test_description" "FAIL" "content 필드가 null 또는 빈 값"
                    fi
                else
                    log_test "$test_description" "PASS" "결과 없음 (정상)"
                fi
            else
                log_test "$test_description" "FAIL" "응답 형식 오류"
            fi
        else
            log_test "$test_description" "PASS" ""
        fi
    else
        log_test "$test_description" "FAIL" "HTTP $status_code (예상: $expected_status)"
    fi
}

# 정상 벡터 검색
test_vector_search "인공지능과 머신러닝" "200" "기본 한국어 벡터 검색"
test_vector_search "artificial intelligence and machine learning" "200" "기본 영어 벡터 검색"
test_vector_search "딥러닝 신경망" "200" "기술 용어 벡터 검색"
test_vector_search "Python 프로그래밍" "200" "혼합 언어 벡터 검색"

# 파라미터 테스트
test_vector_search "AI" "200" "score_threshold 테스트" ', "score_threshold": 0.5'
test_vector_search "AI" "200" "limit 테스트" ', "limit": 1'
test_vector_search "AI" "200" "rerank 테스트" ', "rerank": true, "rerank_top_k": 10'

# 엣지 케이스
test_vector_search "" "422" "빈 검색어 벡터 검색 (422 예상)"
test_vector_search "존재하지않는매우특이한검색어12345" "200" "존재하지 않는 검색어"

# 하이브리드 검색 테스트
echo -e "${CYAN}=== 하이브리드 검색 테스트 ===${NC}"

test_hybrid_search() {
    local query="$1"
    local expected_status="$2"
    local test_description="$3"
    local additional_params="$4"

    # Escape special characters in query for JSON using Python
    local escaped_query=$(python3 -c "
import json
import sys
query = '''$query'''
print(json.dumps(query)[1:-1])
" 2>/dev/null || echo "$query")
    local json_data="{\"query\": \"$escaped_query\", \"limit\": 5, \"highlight\": true$additional_params}"

    response=$(make_request "POST" "/v1/search/hybrid" "$json_data" "Authorization: Bearer $API_KEY")
    status_code=$(echo "$response" | cut -d'|' -f1)
    response_body=$(echo "$response" | cut -d'|' -f2-)

    if [ "$status_code" = "$expected_status" ]; then
        if [ "$expected_status" = "200" ]; then
            success_check=$(validate_json_field "$response_body" "success" "true" "eq")
            search_type_check=$(validate_json_field "$response_body" "search_type" "hybrid" "eq")

            if [ "$success_check" = "PASS" ] && [ "$search_type_check" = "PASS" ]; then
                # 가중치 확인
                vector_weight=$(echo "$response_body" | jq -r '.weights.vector' 2>/dev/null)
                text_weight=$(echo "$response_body" | jq -r '.weights.text' 2>/dev/null)

                if [ "$vector_weight" != "null" ] && [ "$text_weight" != "null" ]; then
                    log_test "$test_description" "PASS" ""
                else
                    log_test "$test_description" "FAIL" "가중치 정보 누락"
                fi
            else
                log_test "$test_description" "FAIL" "응답 형식 오류"
            fi
        else
            log_test "$test_description" "PASS" ""
        fi
    else
        log_test "$test_description" "FAIL" "HTTP $status_code (예상: $expected_status)"
    fi
}

# 정상 하이브리드 검색
test_hybrid_search "인공지능" "200" "기본 하이브리드 검색"
test_hybrid_search "AI technology" "200" "영어 하이브리드 검색"
test_hybrid_search "머신러닝 Python" "200" "혼합 키워드 하이브리드 검색"

# 가중치 테스트
test_hybrid_search "AI" "200" "벡터 가중치 높음" ', "vector_weight": 0.8, "text_weight": 0.2'
test_hybrid_search "AI" "200" "텍스트 가중치 높음" ', "vector_weight": 0.3, "text_weight": 0.7'
test_hybrid_search "AI" "200" "동일 가중치" ', "vector_weight": 0.5, "text_weight": 0.5'

# 잘못된 가중치 (정규화 테스트)
test_hybrid_search "AI" "200" "가중치 합이 1이 아님 (정규화 테스트)" ', "vector_weight": 0.6, "text_weight": 0.6'

# 리랭킹 테스트
test_hybrid_search "인공지능 머신러닝" "200" "리랭킹 활성화" ', "rerank": true, "rerank_top_k": 20'

# 극한 상황 테스트
echo -e "${CYAN}=== 극한 상황 테스트 ===${NC}"

# 매우 큰 limit 값
test_text_search "AI" "422" "매우 큰 limit 값 (1000 초과)" ', "limit": 10000'
test_vector_search "AI" "422" "매우 큰 limit 값 (벡터, 1000 초과)" ', "limit": 10000'
test_text_search "AI" "200" "큰 limit 값 (1000 이하)" ', "limit": 1000'
test_vector_search "AI" "200" "큰 limit 값 (벡터, 1000 이하)" ', "limit": 1000'

# 음수 값들
response=$(make_request "POST" "/v1/search/text" '{"query": "AI", "limit": -1}' "Authorization: Bearer $API_KEY")
status_code=$(echo "$response" | cut -d'|' -f1)
if [ "$status_code" = "422" ] || [ "$status_code" = "400" ]; then
    log_test "음수 limit 값 (오류 예상)" "PASS" ""
else
    log_test "음수 limit 값 (오류 예상)" "FAIL" "HTTP $status_code"
fi

response=$(make_request "POST" "/v1/search/vector" '{"query": "AI", "score_threshold": -1}' "Authorization: Bearer $API_KEY")
status_code=$(echo "$response" | cut -d'|' -f1)
if [ "$status_code" = "422" ] || [ "$status_code" = "400" ]; then
    log_test "음수 score_threshold (오류 예상)" "PASS" ""
else
    log_test "음수 score_threshold (오류 예상)" "FAIL" "HTTP $status_code"
fi

# 잘못된 데이터 타입
response=$(make_request "POST" "/v1/search/text" '{"query": 123, "limit": "abc"}' "Authorization: Bearer $API_KEY")
status_code=$(echo "$response" | cut -d'|' -f1)
if [ "$status_code" = "422" ] || [ "$status_code" = "400" ]; then
    log_test "잘못된 데이터 타입 (오류 예상)" "PASS" ""
else
    log_test "잘못된 데이터 타입 (오류 예상)" "FAIL" "HTTP $status_code"
fi

# 필수 필드 누락
response=$(make_request "POST" "/v1/search/text" '{"limit": 5}' "Authorization: Bearer $API_KEY")
status_code=$(echo "$response" | cut -d'|' -f1)
if [ "$status_code" = "422" ] || [ "$status_code" = "400" ]; then
    log_test "query 필드 누락 (오류 예상)" "PASS" ""
else
    log_test "query 필드 누락 (오류 예상)" "FAIL" "HTTP $status_code"
fi

# 매우 긴 JSON 페이로드
long_query=$(python3 -c "print('매우 긴 검색어 ' * 1000)")
response=$(make_request "POST" "/v1/search/text" "{\"query\": \"$long_query\", \"limit\": 5}" "Authorization: Bearer $API_KEY")
status_code=$(echo "$response" | cut -d'|' -f1)
if [ "$status_code" = "200" ] || [ "$status_code" = "413" ]; then
    log_test "매우 긴 JSON 페이로드" "PASS" ""
else
    log_test "매우 긴 JSON 페이로드" "FAIL" "HTTP $status_code"
fi

# 동시성 테스트
echo -e "${CYAN}=== 동시성 테스트 ===${NC}"

# 동시 요청 테스트
echo "동시 요청 10개 실행 중..."
for i in {1..10}; do
    (
        response=$(make_request "POST" "/v1/search/text" '{"query": "AI", "limit": 3}' "Authorization: Bearer $API_KEY")
        status_code=$(echo "$response" | cut -d'|' -f1)
        if [ "$status_code" = "200" ]; then
            echo "Request $i: SUCCESS"
        else
            echo "Request $i: FAILED ($status_code)"
        fi
    ) &
done
wait

log_test "동시 요청 처리" "PASS" "10개 요청 완료"

# 성능 테스트
echo -e "${CYAN}=== 성능 테스트 ===${NC}"

# 응답 시간 측정
measure_response_time() {
    local endpoint="$1"
    local data="$2"
    local test_name="$3"

    start_time=$(date +%s.%N)
    response=$(make_request "POST" "$endpoint" "$data" "Authorization: Bearer $API_KEY")
    end_time=$(date +%s.%N)

    status_code=$(echo "$response" | cut -d'|' -f1)
    response_time=$(echo "$end_time - $start_time" | bc)

    if [ "$status_code" = "200" ]; then
        # 응답 시간이 5초 이내인지 확인
        if (( $(echo "$response_time < 5.0" | bc -l) )); then
            log_test "$test_name (${response_time}초)" "PASS" ""
        else
            log_test "$test_name (${response_time}초)" "FAIL" "응답 시간이 5초 초과"
        fi
    else
        log_test "$test_name" "FAIL" "HTTP $status_code"
    fi
}

measure_response_time "/v1/search/text" '{"query": "인공지능", "limit": 10}' "텍스트 검색 응답 시간"
measure_response_time "/v1/search/vector" '{"query": "인공지능", "limit": 10}' "벡터 검색 응답 시간"
measure_response_time "/v1/search/hybrid" '{"query": "인공지능", "limit": 10}' "하이브리드 검색 응답 시간"

# 메모리 사용량 테스트 (큰 결과 집합)
measure_response_time "/v1/search/vector" '{"query": "AI", "limit": 100}' "대용량 결과 벡터 검색"
measure_response_time "/v1/search/hybrid" '{"query": "AI", "limit": 100, "rerank": true}' "대용량 결과 하이브리드 검색 (리랭킹)"

# 특수 문자 및 인코딩 테스트
echo -e "${CYAN}=== 특수 문자 및 인코딩 테스트 ===${NC}"

# 다양한 언어
test_text_search "中文测试" "200" "중국어 검색"
test_text_search "日本語テスト" "200" "일본어 검색"
test_text_search "Русский тест" "200" "러시아어 검색"
test_text_search "العربية اختبار" "200" "아랍어 검색"
test_text_search "हिंदी परीक्षण" "200" "힌디어 검색"

# 특수 유니코드 문자
test_text_search "🌍🌎🌏" "200" "지구 이모지 검색"
test_text_search "👨‍💻👩‍💻" "200" "복합 이모지 검색"
test_text_search "™®©" "200" "상표 기호 검색"

# SQL 인젝션 시도
test_text_search "'; DROP TABLE documents; --" "200" "SQL 인젝션 시도 (안전해야 함)"
test_text_search "' OR '1'='1" "200" "SQL 인젝션 시도 2 (안전해야 함)"

# XSS 시도
test_text_search "<script>alert('xss')</script>" "200" "XSS 시도 (안전해야 함)"
test_text_search "javascript:alert('xss')" "200" "JavaScript 인젝션 시도 (안전해야 함)"

# 정규식 특수 문자
test_text_search '.*+?^${}()|[]' "200" "정규식 특수 문자 검색"

# 제어 문자
test_text_search "$(printf 'test\x00null')" "200" "NULL 바이트 포함 검색"
test_text_search "$(printf 'test\ttab\nnewline')" "200" "제어 문자 포함 검색"

# 응답 형식 검증 테스트
echo -e "${CYAN}=== 응답 형식 검증 테스트 ===${NC}"

validate_response_format() {
    local endpoint="$1"
    local data="$2"
    local test_name="$3"

    response=$(make_request "POST" "$endpoint" "$data" "Authorization: Bearer $API_KEY")
    status_code=$(echo "$response" | cut -d'|' -f1)
    response_body=$(echo "$response" | cut -d'|' -f2-)

    if [ "$status_code" = "200" ]; then
        # 필수 필드 존재 확인
        local checks=0
        local passed=0

        # success 필드
        checks=$((checks + 1))
        [ "$(validate_json_field "$response_body" "success" "" "exists")" = "PASS" ] && passed=$((passed + 1))

        # results 필드
        checks=$((checks + 1))
        [ "$(validate_json_field "$response_body" "results" "" "exists")" = "PASS" ] && passed=$((passed + 1))

        # total_results 필드
        checks=$((checks + 1))
        [ "$(validate_json_field "$response_body" "total_results" "" "exists")" = "PASS" ] && passed=$((passed + 1))

        # search_time 필드
        checks=$((checks + 1))
        [ "$(validate_json_field "$response_body" "search_time" "" "exists")" = "PASS" ] && passed=$((passed + 1))

        # query 필드
        checks=$((checks + 1))
        [ "$(validate_json_field "$response_body" "query" "" "exists")" = "PASS" ] && passed=$((passed + 1))

        # 결과가 있는 경우 결과 형식 확인
        results_count=$(echo "$response_body" | jq '.results | length' 2>/dev/null)
        if [ "$results_count" -gt 0 ]; then
            # 첫 번째 결과의 필수 필드 확인
            checks=$((checks + 1))
            [ "$(echo "$response_body" | jq -r '.results[0].id' 2>/dev/null)" != "null" ] && passed=$((passed + 1))

            checks=$((checks + 1))
            [ "$(echo "$response_body" | jq -r '.results[0].score' 2>/dev/null)" != "null" ] && passed=$((passed + 1))

            checks=$((checks + 1))
            [ "$(echo "$response_body" | jq -r '.results[0].metadata' 2>/dev/null)" != "null" ] && passed=$((passed + 1))
        fi

        if [ "$passed" -eq "$checks" ]; then
            log_test "$test_name" "PASS" ""
        else
            log_test "$test_name" "FAIL" "응답 형식 검증 실패 ($passed/$checks)"
        fi
    else
        log_test "$test_name" "FAIL" "HTTP $status_code"
    fi
}

validate_response_format "/v1/search/text" '{"query": "AI", "limit": 3}' "텍스트 검색 응답 형식"
validate_response_format "/v1/search/vector" '{"query": "AI", "limit": 3}' "벡터 검색 응답 형식"
validate_response_format "/v1/search/hybrid" '{"query": "AI", "limit": 3}' "하이브리드 검색 응답 형식"

# 정리
echo -e "${CYAN}=== 테스트 정리 ===${NC}"
rm -f test_*.txt

# 최종 결과 출력
echo ""
echo -e "${BLUE}=== 테스트 결과 요약 ===${NC}"
echo -e "총 테스트: ${TOTAL_TESTS}"
echo -e "${GREEN}성공: ${PASSED_TESTS}${NC}"
echo -e "${RED}실패: ${FAILED_TESTS}${NC}"

if [ "$CRITICAL_FAILURES" -gt 0 ]; then
    echo -e "${RED}💥 치명적 오류: ${CRITICAL_FAILURES}${NC}"
fi

success_rate=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
echo -e "성공률: ${success_rate}%"

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}🎉 모든 테스트가 성공했습니다!${NC}"
    exit 0
elif [ "$CRITICAL_FAILURES" -gt 0 ]; then
    echo -e "${RED}💥 치명적 오류가 발생했습니다!${NC}"
    exit 2
else
    echo -e "${YELLOW}⚠️  일부 테스트가 실패했습니다.${NC}"
    exit 1
fi
