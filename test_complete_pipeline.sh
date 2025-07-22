#!/bin/bash

# RagnaForge 완전한 파이프라인 테스트 스크립트
# 업로드 → 처리 → 모든 검색 케이스 테스트

set -e  # 오류 발생 시 스크립트 중단

# 설정
API_BASE="http://127.0.0.1:8000"
API_KEY="sk-kure-v1-test-key-12345"
TEST_FILE="sample_docs/lg_refrigerator_news.pdf"
SEARCH_QUERY="LG 냉장고 가격"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 함수: 헤더 출력
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# 함수: 성공 메시지
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 함수: 오류 메시지
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 함수: 정보 메시지
print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# 함수: 경고 메시지
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 함수: API 응답 시간 측정 및 결과 출력
test_api() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_status="$5"
    
    echo -e "${PURPLE}🔍 테스트: $name${NC}"
    
    start_time=$(date +%s.%N)
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $API_KEY" \
            -d "$data")
    elif [ "$method" = "POST" ] && [ -z "$data" ]; then
        # 파일 업로드용
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Authorization: Bearer $API_KEY" \
            -F "file=@$TEST_FILE" \
            -F "conversion_method=auto" \
            -F "generate_embeddings=true")
    else
        response=$(curl -s -w "\n%{http_code}" -X GET "$url" \
            -H "Authorization: Bearer $API_KEY")
    fi
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l)
    
    # HTTP 상태 코드 추출
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    # 응답 시간 출력
    printf "   ⏱️  응답 시간: %.3f초\n" "$duration"
    
    # 상태 코드 확인
    if [ "$http_code" = "$expected_status" ]; then
        print_success "HTTP $http_code (예상됨)"
    else
        print_error "HTTP $http_code (예상: $expected_status)"
        echo "응답: $response_body"
        return 1
    fi
    
    # JSON 응답 파싱 및 결과 요약
    if command -v jq >/dev/null 2>&1; then
        if echo "$response_body" | jq . >/dev/null 2>&1; then
            # 헬스 체크는 success 필드가 없으므로 status 필드로 확인
            if echo "$response_body" | jq -e '.status' >/dev/null 2>&1; then
                status=$(echo "$response_body" | jq -r '.status // "unknown"')
                if [ "$status" = "healthy" ]; then
                    print_success "헬스 체크 성공 (상태: $status)"
                else
                    print_error "헬스 체크 실패 (상태: $status)"
                    return 1
                fi
            else
                success=$(echo "$response_body" | jq -r '.success // false')
                if [ "$success" = "true" ]; then
                    print_success "API 호출 성공"
                
                # 검색 결과 요약
                if echo "$response_body" | jq -e '.results' >/dev/null 2>&1; then
                    total_results=$(echo "$response_body" | jq -r '.total_results // 0')
                    search_time=$(echo "$response_body" | jq -r '.search_time // 0')
                    search_type=$(echo "$response_body" | jq -r '.search_type // "unknown"')
                    
                    printf "   📊 검색 결과: %d개 (%.3f초, %s)\n" "$total_results" "$search_time" "$search_type"
                    
                    # 리랭킹 정보
                    if echo "$response_body" | jq -e '.rerank_applied' >/dev/null 2>&1; then
                        rerank_applied=$(echo "$response_body" | jq -r '.rerank_applied')
                        if [ "$rerank_applied" = "true" ]; then
                            echo "   🔄 리랭킹 적용됨"
                        fi
                    fi
                    
                    # 첫 번째 결과의 점수
                    if [ "$total_results" -gt 0 ]; then
                        first_score=$(echo "$response_body" | jq -r '.results[0].score // 0')
                        printf "   🎯 최고 점수: %.4f\n" "$first_score"
                    fi
                fi
                
                # 업로드 결과 요약
                if echo "$response_body" | jq -e '.upload_info' >/dev/null 2>&1; then
                    filename=$(echo "$response_body" | jq -r '.upload_info.filename // "unknown"')
                    file_size=$(echo "$response_body" | jq -r '.upload_info.file_size // 0')
                    echo "   📁 업로드된 파일: $filename ($(($file_size / 1024))KB)"
                fi
                
                # 처리 결과 요약
                if echo "$response_body" | jq -e '.chunks_count' >/dev/null 2>&1; then
                    chunks_count=$(echo "$response_body" | jq -r '.chunks_count // 0')
                    processing_time=$(echo "$response_body" | jq -r '.processing_time // 0')
                    method_used=$(echo "$response_body" | jq -r '.conversion_method_used // "unknown"')
                    printf "   📝 처리 결과: %d개 청크 (%.2f초, %s)\n" "$chunks_count" "$processing_time" "$method_used"
                fi

                else
                    error_msg=$(echo "$response_body" | jq -r '.error // "Unknown error"')
                    print_error "API 오류: $error_msg"
                    return 1
                fi
            fi
        else
            print_warning "JSON 파싱 실패"
            echo "응답: $response_body"
        fi
    else
        print_warning "jq가 설치되지 않음 - JSON 파싱 건너뜀"
        echo "응답 길이: ${#response_body} 문자"
    fi
    
    echo ""
    return 0
}

# 메인 테스트 시작
print_header "🚀 RagnaForge 완전한 파이프라인 테스트"

print_info "테스트 파일: $TEST_FILE"
print_info "검색 쿼리: $SEARCH_QUERY"
print_info "API 베이스: $API_BASE"

# 파일 존재 확인
if [ ! -f "$TEST_FILE" ]; then
    print_error "테스트 파일을 찾을 수 없습니다: $TEST_FILE"
    exit 1
fi

print_success "테스트 파일 확인됨"

# 1. 서버 상태 확인
print_header "1️⃣ 서버 상태 확인"
test_api "헬스 체크" "GET" "$API_BASE/health" "" "200"

# 2. 파일 업로드 및 전체 처리
print_header "2️⃣ 파일 업로드 및 전체 처리"
test_api "업로드 및 처리" "POST" "$API_BASE/v1/upload_and_process" "" "200"

print_info "문서 처리 완료 - 잠시 대기 후 검색 테스트 시작..."
sleep 2

# 3. 벡터 검색 테스트
print_header "3️⃣ 벡터 검색 테스트"

# 3-1. 기본 벡터 검색
test_api "기본 벡터 검색" "POST" "$API_BASE/v1/search/vector" \
    "{\"query\": \"$SEARCH_QUERY\", \"limit\": 3}" "200"

# 3-2. 벡터 검색 + 리랭킹
test_api "벡터 검색 + 리랭킹" "POST" "$API_BASE/v1/search/vector" \
    "{\"query\": \"$SEARCH_QUERY\", \"limit\": 5, \"rerank\": true}" "200"

# 3-3. 벡터 검색 + 점수 임계값
test_api "벡터 검색 + 점수 임계값" "POST" "$API_BASE/v1/search/vector" \
    "{\"query\": \"$SEARCH_QUERY\", \"limit\": 10, \"score_threshold\": 0.1}" "200"

# 4. 텍스트 검색 테스트
print_header "4️⃣ 텍스트 검색 테스트"

# 4-1. 기본 텍스트 검색
test_api "기본 텍스트 검색" "POST" "$API_BASE/v1/search/text" \
    "{\"query\": \"$SEARCH_QUERY\", \"limit\": 3}" "200"

# 4-2. 텍스트 검색 + 하이라이트
test_api "텍스트 검색 + 하이라이트" "POST" "$API_BASE/v1/search/text" \
    "{\"query\": \"$SEARCH_QUERY\", \"limit\": 5, \"highlight\": true}" "200"

# 4-3. 텍스트 검색 + 오프셋
test_api "텍스트 검색 + 오프셋" "POST" "$API_BASE/v1/search/text" \
    "{\"query\": \"$SEARCH_QUERY\", \"limit\": 3, \"offset\": 2}" "200"

# 5. 리랭킹 전용 테스트
print_header "5️⃣ 리랭킹 전용 테스트"

# 간단한 문서 리스트로 리랭킹 테스트
test_api "리랭킹 전용" "POST" "$API_BASE/v1/rerank" \
    "{\"query\": \"$SEARCH_QUERY\", \"documents\": [{\"id\": \"1\", \"text\": \"LG 냉장고는 저렴한 가격으로 유명합니다\"}, {\"id\": \"2\", \"text\": \"삼성 세탁기는 고품질입니다\"}], \"top_k\": 2}" "200"

# 7. 최종 요약
print_header "🎉 테스트 완료 요약"

print_success "모든 API 테스트가 완료되었습니다!"
print_info "테스트된 기능:"
echo "   • 파일 업로드 및 전체 처리 파이프라인"
echo "   • 벡터 검색 (기본, 리랭킹, 점수 임계값)"
echo "   • 텍스트 검색 (기본, 하이라이트, 오프셋)"
echo "   • 리랭킹 전용 API"

print_info "이제 RagnaForge가 완전히 작동하는 것을 확인했습니다! 🚀"
