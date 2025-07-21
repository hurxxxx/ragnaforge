"""
Ragnaforge RAG 시스템 - 심플 Streamlit UI
대시보드, 문서 색인, 검색 기능을 제공하는 간단한 인터페이스
"""

import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="Ragnaforge RAG System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 전역 설정
API_BASE_URL = "http://192.168.0.47:8000"
DEFAULT_API_KEY = "sk-ragnaforge-v1-test-key-12345"

# 세션 상태 초기화
if 'api_key' not in st.session_state:
    st.session_state.api_key = DEFAULT_API_KEY

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 유틸리티 함수
def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Dict:
    """API 요청을 보내는 함수"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.api_key}"}
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files, data=data)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=data)
        
        return {
            "success": response.status_code == 200,
            "data": response.json() if response.status_code == 200 else None,
            "error": response.text if response.status_code != 200 else None,
            "status_code": response.status_code
        }
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 500}

def format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형태로 변환"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

# 메인 헤더
st.markdown('<div class="main-header">🔍 Ragnaforge RAG 시스템</div>', unsafe_allow_html=True)

# 사이드바 - API 키 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("API Key", value=st.session_state.api_key, type="password")
    st.session_state.api_key = api_key
    
    # 시스템 상태 체크
    st.header("📊 시스템 상태")
    if st.button("🔄 상태 확인"):
        health_result = make_api_request("/health")
        if health_result["success"]:
            st.success("✅ 시스템 정상")
        else:
            st.error("❌ 시스템 오류")

# 메인 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 대시보드",
    "📤 문서 색인",
    "🔍 문서 검색",
    "🌐 URL 색인",
    "⚙️ 컬렉션 관리"
])

# 탭 1: 대시보드
with tab1:
    st.header("📊 시스템 대시보드")
    
    if st.button("🔄 데이터 새로고침", use_container_width=True):
        with st.spinner("데이터 로딩 중..."):
            # 저장소 통계 가져오기
            storage_result = make_api_request("/v1/storage/stats")
            files_result = make_api_request("/v1/files", "GET", {"page_size": 1000})
            
            if storage_result["success"]:
                st.session_state.storage_stats = storage_result["data"]
            if files_result["success"]:
                st.session_state.files_data = files_result["data"]
    
    # 메트릭 표시
    if 'storage_stats' in st.session_state:
        stats = st.session_state.storage_stats.get("stats", {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_files = stats.get("file_count", 0) or 0
            st.metric("총 파일 수", total_files)

        with col2:
            total_size = stats.get("total_size", 0) or 0
            st.metric("총 저장 용량", format_file_size(total_size))
        
        with col3:
            # 처리된 문서 수 계산 (files_data에서)
            processed_count = 0
            if 'files_data' in st.session_state:
                files = st.session_state.files_data.get("files", [])
                processed_count = sum(1 for f in files if f.get("is_processed", False))
            st.metric("처리 완료", processed_count)
        
        with col4:
            # 벡터화된 문서 수
            vectorized_count = 0
            if 'files_data' in st.session_state:
                files = st.session_state.files_data.get("files", [])
                vectorized_count = sum(1 for f in files if f.get("has_embeddings", False))
            st.metric("벡터화 완료", vectorized_count)
    
    else:
        st.info("데이터를 보려면 '데이터 새로고침' 버튼을 클릭하세요.")

# 탭 2: 문서 색인
with tab2:
    st.header("📤 문서 색인")
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        "문서 파일을 선택하세요",
        type=['pdf', 'docx', 'pptx', 'md', 'txt'],
        help="지원 형식: PDF, DOCX, PPTX, MD, TXT"
    )
    
    if uploaded_file:
        st.info(f"선택된 파일: {uploaded_file.name} ({format_file_size(uploaded_file.size)})")
        
        # 처리 옵션
        col1, col2 = st.columns(2)
        
        with col1:
            conversion_method = st.selectbox("변환 방법", ["marker", "docling"], index=0)
            chunk_strategy = st.selectbox("청킹 전략", ["semantic", "recursive", "sentence", "token"], index=0)
        
        with col2:
            chunk_size = st.number_input("청크 크기", min_value=100, max_value=2048, value=768)
            generate_embeddings = st.checkbox("임베딩 생성", value=True)
        
        if st.button("📤 업로드 및 처리", use_container_width=True):
            # 파일 업로드
            with st.spinner("파일 업로드 중..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                upload_result = make_api_request("/v1/upload", "POST", files=files)
            
            if upload_result["success"]:
                file_id = upload_result["data"].get("file_id")
                st.success(f"✅ 파일 업로드 성공! ID: {file_id}")
                
                # 문서 처리
                with st.spinner("문서 처리 중..."):
                    process_data = {
                        "file_id": file_id,
                        "conversion_method": conversion_method,
                        "chunk_strategy": chunk_strategy,
                        "chunk_size": chunk_size,
                        "generate_embeddings": generate_embeddings
                    }
                    
                    process_result = make_api_request("/v1/process", "POST", process_data)
                
                if process_result["success"]:
                    st.success("✅ 문서 처리 완료!")
                    
                    # 처리 결과 표시
                    result_data = process_result["data"]
                    
                    col_result1, col_result2 = st.columns(2)
                    
                    with col_result1:
                        st.write("**처리 정보:**")
                        st.write(f"- 변환 방법: {result_data.get('conversion_method', 'N/A')}")
                        st.write(f"- 처리 시간: {result_data.get('processing_time', 0):.2f}초")
                        st.write(f"- 청크 수: {result_data.get('total_chunks', 0)}")
                    
                    with col_result2:
                        st.write("**파일 정보:**")
                        st.write(f"- 마크다운 길이: {result_data.get('markdown_length', 0):,} 문자")
                        st.write(f"- 임베딩 생성: {'✅' if result_data.get('embeddings_generated') else '❌'}")
                        st.write(f"- 문서 ID: {result_data.get('document_id', 'N/A')[:8]}...")
                
                else:
                    st.error(f"❌ 문서 처리 실패: {process_result.get('error', 'Unknown error')}")
            else:
                st.error(f"❌ 파일 업로드 실패: {upload_result.get('error', 'Unknown error')}")

# 탭 3: 문서 검색
with tab3:
    st.header("🔍 문서 검색")
    
    # 검색 입력
    query = st.text_input("검색어를 입력하세요", placeholder="예: 한국어 자연어 처리")
    
    col_search1, col_search2 = st.columns([2, 1])
    
    with col_search1:
        search_type = st.selectbox("검색 타입", ["hybrid", "vector", "text"])
    
    with col_search2:
        limit = st.number_input("결과 수", min_value=1, max_value=50, value=10)
    
    if st.button("🔍 검색 실행", use_container_width=True) and query:
        with st.spinner("검색 중..."):
            search_data = {
                "query": query,
                "limit": limit,
                "search_type": search_type
            }
            
            search_result = make_api_request(f"/v1/search/{search_type}", "POST", search_data)
        
        if search_result["success"]:
            results = search_result["data"].get("results", [])
            st.success(f"✅ 검색 완료! {len(results)}개 결과 발견")
            
            # 검색 결과 표시
            for i, result in enumerate(results, 1):
                with st.expander(f"📄 결과 {i} - 점수: {result.get('score', 0):.3f}"):
                    col_res1, col_res2 = st.columns([3, 1])
                    
                    with col_res1:
                        content = result.get("content", "내용 없음")
                        st.write("**내용:**")
                        st.write(content[:500] + "..." if len(content) > 500 else content)
                    
                    with col_res2:
                        metadata = result.get("metadata", {})
                        st.write("**메타데이터:**")
                        st.write(f"파일명: {metadata.get('filename', 'N/A')}")
                        st.write(f"청크: {metadata.get('chunk_index', 'N/A')}")
                        
                        # 다운로드 버튼 (향후 구현)
                        if st.button(f"📥 다운로드", key=f"download_{i}"):
                            st.info("다운로드 기능은 향후 구현 예정입니다.")
        else:
            st.error(f"❌ 검색 실패: {search_result.get('error', 'Unknown error')}")

# 탭 4: URL 색인 (향후 구현)
with tab4:
    st.header("🌐 URL 색인")
    st.info("🚧 이 기능은 현재 개발 중입니다.")

    # URL 입력 UI (미리 준비)
    url_input = st.text_input("URL을 입력하세요", placeholder="https://example.com")

    col_url1, col_url2 = st.columns(2)

    with col_url1:
        url_type = st.selectbox("콘텐츠 타입", ["웹페이지", "PDF", "YouTube", "기타"])

    with col_url2:
        auto_process = st.checkbox("자동 처리", value=True)

    if st.button("🌐 URL 색인 시작", use_container_width=True, disabled=True):
        st.warning("이 기능은 아직 구현되지 않았습니다.")

# 탭 5: 컬렉션 관리
with tab5:
    st.header("⚙️ 컬렉션 관리")
    st.info("Qdrant와 MeiliSearch 컬렉션을 관리할 수 있습니다.")

    # 컬렉션 상태 확인
    if st.button("🔄 컬렉션 상태 새로고침", use_container_width=True):
        with st.spinner("컬렉션 상태 확인 중..."):
            status_result = make_api_request("/v1/admin/collections/status")

            if status_result["success"]:
                st.session_state.collections_status = status_result["data"]
                st.success("✅ 컬렉션 상태 업데이트 완료")
            else:
                st.error(f"❌ 상태 확인 실패: {status_result.get('error', 'Unknown error')}")

    # 컬렉션 상태 표시
    if 'collections_status' in st.session_state:
        status_data = st.session_state.collections_status

        # Qdrant 상태
        st.subheader("🔵 Qdrant 벡터 데이터베이스")

        col_q1, col_q2 = st.columns(2)

        with col_q1:
            qdrant_health = status_data.get("qdrant", {}).get("health", {})
            qdrant_stats = status_data.get("qdrant", {}).get("stats", {})

            st.write("**연결 상태:**")
            if qdrant_health.get("connected"):
                st.success("✅ 연결됨")
            else:
                st.error("❌ 연결 안됨")

            st.write("**컬렉션 정보:**")
            st.write(f"- 컬렉션명: {qdrant_stats.get('collection_name', 'N/A')}")
            points_count = qdrant_stats.get('points_count', 0) or 0
            vectors_count = qdrant_stats.get('vectors_count', 0) or 0
            st.write(f"- 포인트 수: {points_count:,}")
            st.write(f"- 벡터 수: {vectors_count:,}")

        with col_q2:
            st.write("**관리 작업:**")
            if st.button("🗑️ Qdrant 컬렉션 초기화", type="secondary"):
                if st.session_state.get('confirm_qdrant_reset'):
                    with st.spinner("Qdrant 컬렉션 초기화 중..."):
                        reset_result = make_api_request("/v1/admin/collections/qdrant/reset", "POST")

                        if reset_result["success"]:
                            st.success(f"✅ {reset_result['data']['message']}")
                            st.info(f"삭제된 포인트: {reset_result['data']['points_deleted']:,}개")
                            # 상태 새로고침
                            del st.session_state.collections_status
                        else:
                            st.error(f"❌ 초기화 실패: {reset_result.get('error', 'Unknown error')}")

                    st.session_state.confirm_qdrant_reset = False
                else:
                    st.warning("⚠️ 정말로 Qdrant 컬렉션을 초기화하시겠습니까?")
                    if st.button("확인", key="confirm_qdrant"):
                        st.session_state.confirm_qdrant_reset = True
                        st.rerun()

        st.divider()

        # MeiliSearch 상태
        st.subheader("🟡 MeiliSearch 텍스트 검색")

        col_m1, col_m2 = st.columns(2)

        with col_m1:
            meilisearch_health = status_data.get("meilisearch", {}).get("health", {})
            meilisearch_stats = status_data.get("meilisearch", {}).get("stats", {})

            st.write("**연결 상태:**")
            if meilisearch_health.get("status") == "healthy":
                st.success("✅ 연결됨")
            else:
                st.error("❌ 연결 안됨")

            st.write("**인덱스 정보:**")
            st.write(f"- 인덱스명: {meilisearch_stats.get('index_name', 'N/A')}")
            documents_count = meilisearch_stats.get('documents_count', 0) or 0
            is_indexing = meilisearch_stats.get('is_indexing', False) or False
            st.write(f"- 문서 수: {documents_count:,}")
            st.write(f"- 인덱싱 중: {'예' if is_indexing else '아니오'}")

        with col_m2:
            st.write("**관리 작업:**")
            if st.button("🗑️ MeiliSearch 인덱스 초기화", type="secondary"):
                if st.session_state.get('confirm_meilisearch_reset'):
                    with st.spinner("MeiliSearch 인덱스 초기화 중..."):
                        reset_result = make_api_request("/v1/admin/collections/meilisearch/reset", "POST")

                        if reset_result["success"]:
                            st.success(f"✅ {reset_result['data']['message']}")
                            st.info(f"삭제된 문서: {reset_result['data']['documents_deleted']:,}개")
                            # 상태 새로고침
                            del st.session_state.collections_status
                        else:
                            st.error(f"❌ 초기화 실패: {reset_result.get('error', 'Unknown error')}")

                    st.session_state.confirm_meilisearch_reset = False
                else:
                    st.warning("⚠️ 정말로 MeiliSearch 인덱스를 초기화하시겠습니까?")
                    if st.button("확인", key="confirm_meilisearch"):
                        st.session_state.confirm_meilisearch_reset = True
                        st.rerun()

    else:
        st.info("컬렉션 상태를 확인하려면 '컬렉션 상태 새로고침' 버튼을 클릭하세요.")

# 푸터
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🔍 Ragnaforge RAG 시스템 v1.0 | 
    Powered by FastAPI + Streamlit
</div>
""", unsafe_allow_html=True)
