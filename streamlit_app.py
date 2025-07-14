"""
KURE 문서 검색 시스템 - Streamlit UI
종합적인 문서 관리, 검색, 챗봇 기능을 제공하는 데모 인터페이스
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
    page_title="KURE Search System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 전역 설정
API_BASE_URL = "http://localhost:8000"
DEFAULT_API_KEY = "sk-kure-v1-test-key-12345"

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
    .status-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-healthy {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .search-result {
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

# 유틸리티 함수들
def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Dict:
    """API 요청을 보내는 함수"""
    try:
        headers = {"Authorization": f"Bearer {st.session_state.get('api_key', DEFAULT_API_KEY)}"}
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, data=data, files=files)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=data)
        
        return {
            "success": response.status_code == 200,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "status_code": response.status_code
        }
    except Exception as e:
        return {"success": False, "error": str(e), "status_code": 500}

def check_system_health() -> Dict[str, Any]:
    """시스템 상태 체크"""
    health_checks = {}
    
    # 기본 헬스 체크
    result = make_api_request("/health")
    health_checks["api"] = {
        "status": "healthy" if result["success"] else "error",
        "details": result.get("data", {})
    }
    
    # 벡터 DB 상태 (Qdrant)
    result = make_api_request("/v1/storage/stats")
    health_checks["vector_db"] = {
        "status": "healthy" if result["success"] else "error",
        "details": result.get("data", {})
    }
    
    # 리랭크 서비스 상태
    result = make_api_request("/v1/rerank/health")
    health_checks["rerank"] = {
        "status": "healthy" if result["success"] else "error",
        "details": result.get("data", {})
    }
    
    return health_checks

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

# 세션 상태 초기화
if 'api_key' not in st.session_state:
    st.session_state.api_key = DEFAULT_API_KEY
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# 메인 헤더
st.markdown('<div class="main-header">🔍 KURE 문서 검색 시스템</div>', unsafe_allow_html=True)

# 사이드바 - 설정 및 상태
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    
    # API 키 설정
    api_key = st.text_input("API Key", value=st.session_state.api_key, type="password")
    st.session_state.api_key = api_key
    
    st.divider()
    
    # 시스템 상태 체크
    st.header("📊 시스템 상태")
    
    if st.button("🔄 상태 새로고침", use_container_width=True):
        with st.spinner("시스템 상태 확인 중..."):
            st.session_state.health_status = check_system_health()
    
    if 'health_status' not in st.session_state:
        st.session_state.health_status = check_system_health()
    
    # 상태 표시
    for service, status in st.session_state.health_status.items():
        status_class = "status-healthy" if status["status"] == "healthy" else "status-error"
        status_icon = "✅" if status["status"] == "healthy" else "❌"
        
        service_names = {
            "api": "API 서버",
            "vector_db": "벡터 DB",
            "rerank": "리랭크 서비스"
        }
        
        st.markdown(f"""
        <div class="status-card {status_class}">
            {status_icon} <strong>{service_names.get(service, service)}</strong><br>
            상태: {status["status"]}
        </div>
        """, unsafe_allow_html=True)

# 메인 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📄 문서 관리", 
    "🔍 검색", 
    "📊 검색 결과", 
    "🤖 AI 챗봇",
    "📈 시스템 통계"
])

# 탭 1: 문서 관리
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 파일 업로드")
        
        uploaded_file = st.file_uploader(
            "PDF 파일을 선택하세요",
            type=['pdf'],
            help="PDF 파일만 업로드 가능합니다"
        )
        
        if uploaded_file:
            st.info(f"선택된 파일: {uploaded_file.name} ({format_file_size(uploaded_file.size)})")
            
            # 처리 옵션
            st.subheader("처리 옵션")
            col_opt1, col_opt2 = st.columns(2)
            
            with col_opt1:
                conversion_method = st.selectbox("변환 방법", ["marker", "docling"], index=0)
                chunk_strategy = st.selectbox("청킹 전략", ["recursive", "semantic"], index=0)
            
            with col_opt2:
                chunk_size = st.number_input("청크 크기", min_value=100, max_value=1000, value=380)
                overlap = st.number_input("오버랩", min_value=0, max_value=200, value=70)
            
            generate_embeddings = st.checkbox("임베딩 생성", value=True, key="upload_embeddings")
            embedding_model = st.selectbox("임베딩 모델", ["nlpai-lab/KURE-v1"], index=0)
            
            if st.button("📤 업로드 및 처리", use_container_width=True):
                with st.spinner("파일 업로드 중..."):
                    # 파일 업로드
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    upload_result = make_api_request("/v1/upload", "POST", files=files)
                    
                    if upload_result["success"]:
                        file_id = upload_result["data"].get("file_id")
                        st.success(f"✅ 파일 업로드 성공! ID: {file_id}")
                        
                        # 문서 처리
                        with st.spinner("문서 처리 중..."):
                            process_data = {
                                "file_id": file_id,
                                "conversion_method": conversion_method,
                                "extract_images": False,
                                "chunk_strategy": chunk_strategy,
                                "chunk_size": chunk_size,
                                "overlap": overlap,
                                "generate_embeddings": generate_embeddings,
                                "embedding_model": embedding_model
                            }
                            
                            process_result = make_api_request("/v1/process", "POST", process_data)
                            
                            if process_result["success"]:
                                st.success("✅ 문서 처리 완료!")
                                st.json(process_result["data"])
                            else:
                                st.error(f"❌ 문서 처리 실패: {process_result.get('error', 'Unknown error')}")
                    else:
                        st.error(f"❌ 파일 업로드 실패: {upload_result.get('error', 'Unknown error')}")
    
    with col2:
        st.header("📋 문서 목록")
        
        if st.button("🔄 목록 새로고침", use_container_width=True):
            with st.spinner("문서 목록 로딩 중..."):
                files_result = make_api_request("/v1/files", "GET", {"page_size": 50})

                if files_result["success"]:
                    files_data = files_result["data"]
                    files_list = files_data.get("files", [])

                    # 각 문서의 상세 정보 조회 (처리된 문서만)
                    for file_info in files_list:
                        if file_info.get("is_processed") and file_info.get("document_id"):
                            doc_id = file_info["document_id"]
                            # 문서 청크 수 조회 시도
                            try:
                                # 간단한 검색으로 해당 문서의 청크 수 확인
                                search_result = make_api_request("/v1/search/vector", "POST", {
                                    "query": "test",
                                    "limit": 1,
                                    "score_threshold": 0.0,
                                    "filters": {"document_id": doc_id}
                                })
                                if search_result["success"]:
                                    file_info["chunk_count"] = search_result["data"].get("total_results", 0)
                                    file_info["has_embeddings"] = file_info["chunk_count"] > 0
                            except:
                                file_info["chunk_count"] = 0
                                file_info["has_embeddings"] = False

                    st.session_state.files_list = files_list
                else:
                    st.error("문서 목록을 불러올 수 없습니다.")
        
        if 'files_list' in st.session_state and st.session_state.files_list:
            st.write(f"총 {len(st.session_state.files_list)}개의 문서")
            
            # 문서 목록 표시
            for file_info in st.session_state.files_list[:10]:  # 최근 10개만 표시
                with st.expander(f"📄 {file_info.get('filename', 'Unknown')}"):
                    col_info1, col_info2 = st.columns(2)

                    with col_info1:
                        st.write(f"**파일 ID:** {file_info.get('file_id', file_info.get('id', 'N/A'))}")
                        st.write(f"**크기:** {format_file_size(file_info.get('file_size', file_info.get('size', 0)))}")
                        st.write(f"**타입:** {file_info.get('file_type', 'N/A')}")

                    with col_info2:
                        created_at = file_info.get('created_at', 0)
                        if created_at:
                            upload_time = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            upload_time = 'N/A'
                        st.write(f"**업로드:** {upload_time}")
                        st.write(f"**처리 상태:** {'✅ 완료' if file_info.get('is_processed') else '❌ 미처리'}")
                        st.write(f"**중복 파일:** {'⚠️ 중복' if file_info.get('is_duplicate') else '✅ 원본'}")

                        # 청크 수와 임베딩 정보
                        chunk_count = file_info.get('chunk_count', 0)
                        has_embeddings = file_info.get('has_embeddings', False)
                        st.write(f"**청크 수:** {chunk_count}")
                        st.write(f"**임베딩:** {'✅' if has_embeddings else '❌'}")

                        # 문서 ID가 있으면 표시
                        document_id = file_info.get('document_id')
                        if document_id:
                            st.write(f"**문서 ID:** {document_id[:8]}...")
        else:
            st.info("문서 목록을 불러오려면 '목록 새로고침' 버튼을 클릭하세요.")

# 탭 2: 검색
with tab2:
    st.header("🔍 문서 검색")
    
    # 검색 설정
    col_search1, col_search2 = st.columns([2, 1])
    
    with col_search1:
        query = st.text_input("검색어를 입력하세요", placeholder="예: 한국어 자연어 처리")
    
    with col_search2:
        search_type = st.selectbox("검색 타입", ["hybrid", "vector", "text"])
    
    # 고급 설정
    with st.expander("🔧 고급 검색 설정"):
        col_adv1, col_adv2, col_adv3 = st.columns(3)
        
        with col_adv1:
            limit = st.number_input("결과 수", min_value=1, max_value=50, value=10)
            score_threshold = st.number_input("점수 임계값", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
        
        with col_adv2:
            if search_type == "hybrid":
                vector_weight = st.slider("벡터 가중치", 0.0, 1.0, 0.7)
                text_weight = 1.0 - vector_weight
                st.write(f"텍스트 가중치: {text_weight:.1f}")
        
        with col_adv3:
            rerank = st.checkbox("리랭킹 적용", value=True, key="search_rerank")
            if rerank:
                rerank_top_k = st.number_input("리랭크 대상 수", min_value=5, max_value=100, value=20)
    
    # 검색 실행
    if st.button("🔍 검색 실행", use_container_width=True) and query:
        with st.spinner("검색 중..."):
            search_data = {
                "query": query,
                "limit": limit
            }
            
            if search_type == "vector":
                search_data.update({
                    "score_threshold": score_threshold,
                    "embedding_model": "nlpai-lab/KURE-v1"
                })
                if rerank:
                    search_data.update({
                        "rerank": True,
                        "rerank_top_k": rerank_top_k
                    })
            elif search_type == "text":
                search_data["highlight"] = True
            elif search_type == "hybrid":
                search_data.update({
                    "vector_weight": vector_weight,
                    "text_weight": text_weight,
                    "embedding_model": "nlpai-lab/KURE-v1"
                })
                if rerank:
                    search_data.update({
                        "rerank": True,
                        "rerank_top_k": rerank_top_k
                    })
            
            search_result = make_api_request(f"/v1/search/{search_type}", "POST", search_data)
            
            if search_result["success"]:
                st.session_state.search_results = search_result["data"]
                st.session_state.last_query = query
                st.success(f"✅ 검색 완료! {len(search_result['data'].get('results', []))}개 결과 발견")
                
                # 검색 통계
                search_time = search_result["data"].get("search_time", 0)
                st.info(f"⏱️ 검색 시간: {search_time:.3f}초")
            else:
                st.error(f"❌ 검색 실패: {search_result.get('error', 'Unknown error')}")

# 탭 3: 검색 결과
with tab3:
    st.header("📊 검색 결과")
    
    if st.session_state.search_results:
        results = st.session_state.search_results.get("results", [])
        
        if results:
            # 결과 통계
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("총 결과 수", len(results))
            
            with col_stat2:
                avg_score = sum(r.get("score", 0) for r in results) / len(results)
                st.metric("평균 점수", f"{avg_score:.3f}")
            
            with col_stat3:
                search_time = st.session_state.search_results.get("search_time", 0)
                st.metric("검색 시간", f"{search_time:.3f}초")
            
            with col_stat4:
                search_type = st.session_state.search_results.get("search_type", "unknown")
                st.metric("검색 타입", search_type.upper())
            
            st.divider()
            
            # 결과 목록
            for i, result in enumerate(results, 1):
                with st.expander(f"📄 결과 {i} - 점수: {result.get('score', 0):.3f}"):
                    col_res1, col_res2 = st.columns([2, 1])
                    
                    with col_res1:
                        content = result.get("content", "내용 없음")
                        st.write("**내용:**")
                        st.write(content)
                        
                        # 하이라이트 표시
                        highlights = result.get("highlights")
                        if highlights:
                            st.write("**하이라이트:**")
                            for highlight in highlights[:3]:  # 최대 3개만 표시
                                st.markdown(f"💡 {highlight}")
                    
                    with col_res2:
                        metadata = result.get("metadata", {})
                        st.write("**메타데이터:**")
                        st.write(f"파일명: {metadata.get('filename', 'N/A')}")
                        st.write(f"청크 인덱스: {metadata.get('chunk_index', 'N/A')}")
                        st.write(f"토큰 수: {metadata.get('token_count', 'N/A')}")
                        
                        # 검색 소스 정보
                        search_source = result.get("search_source", metadata.get("search_source"))
                        if search_source:
                            st.write(f"검색 소스: {search_source}")
                        
                        # 하이브리드 검색 점수
                        if "hybrid_score" in metadata:
                            st.write(f"하이브리드 점수: {metadata['hybrid_score']:.3f}")
                            st.write(f"벡터 점수: {metadata.get('vector_score', 0):.3f}")
                            st.write(f"텍스트 점수: {metadata.get('text_score', 0):.3f}")
        else:
            st.info("검색 결과가 없습니다.")
    else:
        st.info("검색을 실행하면 결과가 여기에 표시됩니다.")

# 탭 4: AI 챗봇
with tab4:
    st.header("🤖 AI 챗봇")

    # 챗봇 설정
    with st.expander("🔧 챗봇 설정"):
        col_chat1, col_chat2 = st.columns(2)

        with col_chat1:
            use_search = st.checkbox("문서 검색 기반 답변", value=True, key="chat_use_search")
            if use_search:
                search_limit = st.number_input("검색 결과 수", min_value=1, max_value=10, value=5)
                use_rerank = st.checkbox("리랭킹 적용", value=True, key="chat_rerank")

        with col_chat2:
            temperature = st.slider("창의성 (Temperature)", 0.0, 1.0, 0.7)
            max_tokens = st.number_input("최대 토큰 수", min_value=100, max_value=2000, value=500)

    # 채팅 히스토리 표시
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 사용자:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 AI 어시스턴트:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)

                # 참조 문서 표시
                if "sources" in message:
                    with st.expander("📚 참조 문서"):
                        for i, source in enumerate(message["sources"], 1):
                            st.write(f"**{i}.** {source.get('filename', 'Unknown')} (점수: {source.get('score', 0):.3f})")
                            st.write(f"내용: {source.get('content', '')[:200]}...")

    # 채팅 입력
    user_input = st.chat_input("질문을 입력하세요...")

    if user_input:
        # 사용자 메시지 추가
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.spinner("AI가 답변을 생성하고 있습니다..."):
            try:
                # 문서 검색 기반 답변
                if use_search:
                    # 먼저 관련 문서 검색
                    search_data = {
                        "query": user_input,
                        "limit": search_limit,
                        "vector_weight": 0.7,
                        "text_weight": 0.3,
                        "embedding_model": "nlpai-lab/KURE-v1"
                    }

                    if use_rerank:
                        search_data.update({
                            "rerank": True,
                            "rerank_top_k": search_limit * 2
                        })

                    search_result = make_api_request("/v1/search/hybrid", "POST", search_data)

                    if search_result["success"]:
                        search_results = search_result["data"].get("results", [])

                        # 컨텍스트 구성
                        context = "\n\n".join([
                            f"문서 {i+1}: {result.get('content', '')}"
                            for i, result in enumerate(search_results[:3])
                        ])

                        # AI 답변 생성 (실제로는 OpenAI API 등을 사용해야 함)
                        # 여기서는 시뮬레이션
                        if context:
                            ai_response = f"""
검색된 문서를 바탕으로 답변드리겠습니다.

**질문:** {user_input}

**답변:**
제공된 문서들을 분석한 결과, 다음과 같은 정보를 찾을 수 있었습니다:

{context[:500]}...

이 정보가 도움이 되셨나요? 더 구체적인 질문이 있으시면 언제든 말씀해 주세요.
                            """

                            # 어시스턴트 메시지 추가
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": ai_response,
                                "sources": search_results[:3]
                            })
                        else:
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": "죄송합니다. 관련된 문서를 찾을 수 없어 답변을 드리기 어렵습니다. 다른 질문을 해보시겠어요?"
                            })
                    else:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": "문서 검색 중 오류가 발생했습니다. 다시 시도해 주세요."
                        })
                else:
                    # 일반 AI 답변 (문서 검색 없이)
                    ai_response = f"질문: '{user_input}'에 대한 일반적인 답변을 제공하겠습니다. (실제 구현에서는 LLM API를 연동해야 합니다.)"
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": ai_response
                    })

            except Exception as e:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"오류가 발생했습니다: {str(e)}"
                })

        # 페이지 새로고침으로 새 메시지 표시
        st.rerun()

    # 채팅 히스토리 초기화
    if st.button("🗑️ 채팅 히스토리 초기화"):
        st.session_state.chat_history = []
        st.rerun()

# 탭 5: 시스템 통계
with tab5:
    st.header("📈 시스템 통계")

    # 통계 새로고침
    if st.button("🔄 통계 새로고침", use_container_width=True):
        with st.spinner("통계 데이터 로딩 중..."):
            # 저장소 통계
            storage_result = make_api_request("/v1/storage/stats")
            if storage_result["success"]:
                st.session_state.storage_stats = storage_result["data"]

            # 모니터링 통계
            monitoring_result = make_api_request("/v1/monitoring/stats")
            if monitoring_result["success"]:
                st.session_state.monitoring_stats = monitoring_result["data"]

            # 파일 통계
            files_result = make_api_request("/v1/files", "GET", {"page_size": 1000})
            if files_result["success"]:
                st.session_state.files_stats = files_result["data"]

    # 저장소 통계
    if 'storage_stats' in st.session_state:
        st.subheader("💾 저장소 통계")

        storage_data = st.session_state.storage_stats.get("stats", {})

        col_storage1, col_storage2, col_storage3, col_storage4 = st.columns(4)

        with col_storage1:
            total_size = storage_data.get("total_size", 0)
            st.metric("총 저장소 사용량", format_file_size(total_size))

        with col_storage2:
            file_count = storage_data.get("file_count", 0)
            st.metric("총 파일 수", file_count)

        with col_storage3:
            avg_size = total_size / max(file_count, 1)
            st.metric("평균 파일 크기", format_file_size(avg_size))

        with col_storage4:
            directories = storage_data.get("directories", {})
            st.metric("디렉토리 수", len(directories))

    # 모니터링 통계
    if 'monitoring_stats' in st.session_state:
        st.subheader("📊 모니터링 통계")

        monitoring_data = st.session_state.monitoring_stats.get("stats", {})

        col_mon1, col_mon2, col_mon3, col_mon4 = st.columns(4)

        with col_mon1:
            total_requests = monitoring_data.get("total_requests", 0)
            st.metric("총 요청 수", total_requests)

        with col_mon2:
            avg_response_time = monitoring_data.get("average_response_time", 0)
            st.metric("평균 응답 시간", f"{avg_response_time:.3f}초")

        with col_mon3:
            duplicate_count = monitoring_data.get("duplicate_files_detected", 0)
            st.metric("중복 파일 감지", duplicate_count)

        with col_mon4:
            space_saved = monitoring_data.get("space_saved_bytes", 0)
            st.metric("절약된 공간", format_file_size(space_saved))

        # 성능 차트
        if "performance_history" in monitoring_data:
            st.subheader("📈 성능 추이")

            perf_data = monitoring_data["performance_history"]
            if perf_data:
                df = pd.DataFrame(perf_data)

                # 응답 시간 차트
                fig_response = px.line(
                    df,
                    x="timestamp",
                    y="response_time",
                    title="응답 시간 추이",
                    labels={"response_time": "응답 시간 (초)", "timestamp": "시간"}
                )
                st.plotly_chart(fig_response, use_container_width=True)

    # 파일 타입 분포
    if 'files_stats' in st.session_state:
        st.subheader("📄 파일 타입 분포")

        files = st.session_state.files_stats.get("files", [])
        if files:
            # 파일 타입별 통계
            file_types = {}
            for file_info in files:
                file_type = file_info.get("file_type", "unknown")
                file_types[file_type] = file_types.get(file_type, 0) + 1

            # 파이 차트
            if file_types:
                fig_pie = px.pie(
                    values=list(file_types.values()),
                    names=list(file_types.keys()),
                    title="파일 타입별 분포"
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            # 최근 업로드 파일들
            st.subheader("📅 최근 업로드 파일")

            recent_files = sorted(files, key=lambda x: x.get("created_at", 0), reverse=True)[:10]

            if recent_files:
                df_recent = pd.DataFrame([
                    {
                        "파일명": f.get("filename", "Unknown"),
                        "크기": format_file_size(f.get("file_size", f.get("size", 0))),
                        "타입": f.get("file_type", "Unknown"),
                        "처리 상태": "✅ 완료" if f.get("is_processed") else "❌ 미처리",
                        "중복": "⚠️ 중복" if f.get("is_duplicate") else "✅ 원본",
                        "업로드 시간": datetime.fromtimestamp(f.get("created_at", 0)).strftime("%Y-%m-%d %H:%M:%S") if f.get("created_at") else "Unknown"
                    }
                    for f in recent_files
                ])

                st.dataframe(df_recent, use_container_width=True)

    if not any(key in st.session_state for key in ['storage_stats', 'monitoring_stats', 'files_stats']):
        st.info("통계를 보려면 '통계 새로고침' 버튼을 클릭하세요.")

# 푸터
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🔍 KURE 문서 검색 시스템 v1.0 |
    Powered by FastAPI + Streamlit |
    <a href="https://github.com/hurxxxx/ragnaforge" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True)
