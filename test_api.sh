#!/bin/bash

# KURE API 통합 테스트 스크립트
# 모든 주요 API 엔드포인트를 테스트합니다.

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 설정
API_KEY="sk-kure-v1-test-key-12345"
BASE_URL="http://127.0.0.1:8000"
TEST_FILE="test_document.txt"

# 헬퍼 함수
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# HTTP 상태 코드 확인
check_status() {
    local status=$1
    local expected=$2
    local test_name=$3
    
    if [ "$status" -eq "$expected" ]; then
        print_success "$test_name (Status: $status)"
        return 0
    else
        print_error "$test_name (Expected: $expected, Got: $status)"
        return 1
    fi
}

# JSON 응답에서 success 필드 확인
check_success() {
    local response=$1
    local test_name=$2
    
    local success=$(echo "$response" | jq -r '.success // false')
    if [ "$success" = "true" ]; then
        print_success "$test_name"
        return 0
    else
        local error=$(echo "$response" | jq -r '.error // .detail // "Unknown error"')
        print_error "$test_name - Error: $error"
        return 1
    fi
}

# 테스트 파일 생성
create_test_file() {
    echo "한국어 테스트 문서입니다. 이 문서는 벡터 검색과 텍스트 검색을 테스트하기 위한 샘플 문서입니다." > "$TEST_FILE"
    print_success "테스트 파일 생성: $TEST_FILE"
}

# 서버 상태 확인
check_server() {
    print_header "서버 상태 확인"
    
    local response=$(curl -s -w "%{http_code}" "$BASE_URL/health")
    local status="${response: -3}"
    local body="${response%???}"
    
    if check_status "$status" "200" "헬스 체크"; then
        local model_loaded=$(echo "$body" | jq -r '.is_model_loaded')
        if [ "$model_loaded" = "true" ]; then
            print_success "모델 로드 상태: 정상"
        else
            print_warning "모델 로드 상태: 비정상"
        fi
    else
        print_error "서버가 응답하지 않습니다. 서버를 시작해주세요."
        exit 1
    fi
}

# 1. 파일 업로드 테스트
test_file_upload() {
    print_header "파일 업로드 테스트"
    
    local response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $API_KEY" \
        -F "file=@$TEST_FILE" \
        "$BASE_URL/v1/upload")
    
    local status="${response: -3}"
    local body="${response%???}"
    
    if check_status "$status" "200" "파일 업로드"; then
        check_success "$body" "파일 업로드 응답"
        
        # 파일 ID 추출
        FILE_ID=$(echo "$body" | jq -r '.file_id')
        print_success "파일 ID: $FILE_ID"
        
        # 중복 감지 확인
        local duplicate=$(echo "$body" | jq -r '.duplicate_detected // false')
        if [ "$duplicate" = "true" ]; then
            print_warning "중복 파일 감지됨"
        else
            print_success "새 파일 업로드 완료"
        fi
    fi
}

# 2. 문서 처리 테스트
test_document_processing() {
    print_header "문서 처리 테스트"
    
    if [ -z "$FILE_ID" ]; then
        print_error "파일 ID가 없습니다. 파일 업로드를 먼저 실행하세요."
        return 1
    fi
    
    local response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"file_id\": \"$FILE_ID\",
            \"conversion_method\": \"auto\",
            \"extract_images\": false,
            \"chunk_strategy\": \"recursive\",
            \"chunk_size\": 380,
            \"overlap\": 70,
            \"generate_embeddings\": true,
            \"embedding_model\": \"nlpai-lab/KURE-v1\"
        }" \
        "$BASE_URL/v1/process")
    
    local status="${response: -3}"
    local body="${response%???}"
    
    if check_status "$status" "200" "문서 처리"; then
        check_success "$body" "문서 처리 응답"
        
        local chunks=$(echo "$body" | jq -r '.total_chunks // 0')
        print_success "생성된 청크 수: $chunks"
        
        local embeddings=$(echo "$body" | jq -r '.embeddings_generated // false')
        if [ "$embeddings" = "true" ]; then
            print_success "임베딩 생성 완료"
        else
            print_warning "임베딩 생성 실패"
        fi
    fi
}

# 3. 벡터 검색 테스트
test_vector_search() {
    print_header "벡터 검색 테스트"
    
    local response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "query": "한국어 문서",
            "limit": 5,
            "score_threshold": 0.0,
            "rerank": true,
            "rerank_top_k": 10
        }' \
        "$BASE_URL/v1/search/vector")
    
    local status="${response: -3}"
    local body="${response%???}"
    
    if check_status "$status" "200" "벡터 검색"; then
        check_success "$body" "벡터 검색 응답"
        
        local results=$(echo "$body" | jq -r '.total_results // 0')
        print_success "검색 결과 수: $results"
        
        local search_time=$(echo "$body" | jq -r '.search_time // 0')
        print_success "검색 시간: ${search_time}초"
    fi
}

# 4. 텍스트 검색 테스트
test_text_search() {
    print_header "텍스트 검색 테스트"
    
    local response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "query": "테스트 문서",
            "limit": 5,
            "highlight": true
        }' \
        "$BASE_URL/v1/search/text")
    
    local status="${response: -3}"
    local body="${response%???}"
    
    if check_status "$status" "200" "텍스트 검색"; then
        check_success "$body" "텍스트 검색 응답"
        
        local results=$(echo "$body" | jq -r '.total_results // .total // 0')
        print_success "검색 결과 수: $results"
    fi
}

# 5. 하이브리드 검색 테스트
test_hybrid_search() {
    print_header "하이브리드 검색 테스트"
    
    local response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "query": "한국어 테스트",
            "limit": 3,
            "vector_weight": 0.7,
            "text_weight": 0.3,
            "rerank": true
        }' \
        "$BASE_URL/v1/search/hybrid")
    
    local status="${response: -3}"
    local body="${response%???}"
    
    if check_status "$status" "200" "하이브리드 검색"; then
        check_success "$body" "하이브리드 검색 응답"
        
        local results=$(echo "$body" | jq -r '.total_results // 0')
        print_success "검색 결과 수: $results"
        
        local vector_results=$(echo "$body" | jq -r '.vector_results_count // 0')
        local text_results=$(echo "$body" | jq -r '.text_results_count // 0')
        print_success "벡터 결과: $vector_results, 텍스트 결과: $text_results"
    fi
}

# 6. 모니터링 통계 테스트
test_monitoring() {
    print_header "모니터링 통계 테스트"
    
    local response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $API_KEY" \
        "$BASE_URL/v1/monitoring/stats")
    
    local status="${response: -3}"
    local body="${response%???}"
    
    if check_status "$status" "200" "모니터링 통계"; then
        check_success "$body" "모니터링 통계 응답"
        
        local duplicates=$(echo "$body" | jq -r '.duplicate_detection.total_duplicates // 0')
        local operations=$(echo "$body" | jq -r '.performance.total_operations // 0')
        local success_rate=$(echo "$body" | jq -r '.performance.success_rate // 0')
        
        print_success "중복 감지: $duplicates건"
        print_success "총 작업: $operations건"
        print_success "성공률: $success_rate%"
    fi
}

# 7. 파일 목록 테스트
test_file_list() {
    print_header "파일 목록 테스트"
    
    local response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $API_KEY" \
        "$BASE_URL/v1/files")
    
    local status="${response: -3}"
    local body="${response%???}"
    
    if check_status "$status" "200" "파일 목록"; then
        check_success "$body" "파일 목록 응답"
        
        local total=$(echo "$body" | jq -r '.total_files // 0')
        print_success "총 파일 수: $total개"
    fi
}

# 메인 실행
main() {
    echo -e "${BLUE}🚀 KURE API 통합 테스트 시작${NC}"
    echo "API 서버: $BASE_URL"
    echo "API 키: $API_KEY"
    
    # jq 설치 확인
    if ! command -v jq &> /dev/null; then
        print_error "jq가 설치되지 않았습니다. 'sudo apt-get install jq' 또는 'brew install jq'로 설치하세요."
        exit 1
    fi
    
    # 테스트 파일 생성
    create_test_file
    
    # 테스트 실행
    check_server
    test_file_upload
    test_document_processing
    test_vector_search
    test_text_search
    test_hybrid_search
    test_monitoring
    test_file_list
    
    # 정리
    rm -f "$TEST_FILE"
    
    echo -e "\n${GREEN}🎉 모든 테스트 완료!${NC}"
}

# 스크립트 실행
main "$@"
