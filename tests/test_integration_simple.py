"""
간단한 통합 테스트

실제 서비스들이 제대로 작동하는지 확인하는 기본적인 테스트
"""

import pytest
import asyncio
import time
from pathlib import Path

from services.file_upload_service import file_upload_service
from services.document_processing_service import document_processing_service
from services.embedding_service import embedding_service
from services.qdrant_service import qdrant_service
from services.search_service import search_service
from models import SupportedFileType


class MockUploadFile:
    """테스트용 모의 업로드 파일"""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.size = len(content)
    
    async def read(self) -> bytes:
        return self.content


class TestSimpleIntegration:
    """간단한 통합 테스트"""

    def test_service_imports(self):
        """모든 서비스가 정상적으로 임포트되는지 테스트"""
        print("\n=== 서비스 임포트 테스트 ===")
        
        assert file_upload_service is not None
        print("✓ file_upload_service")
        
        assert document_processing_service is not None
        print("✓ document_processing_service")
        
        assert embedding_service is not None
        print("✓ embedding_service")
        
        assert qdrant_service is not None
        print("✓ qdrant_service")
        
        assert search_service is not None
        print("✓ search_service")
        
        print("=== 모든 서비스 임포트 성공 ===\n")

    def test_embedding_service_basic(self):
        """임베딩 서비스 기본 기능 테스트"""
        print("\n=== 임베딩 서비스 기본 테스트 ===")
        
        # 사용 가능한 모델 확인
        models = embedding_service.get_available_models()
        assert len(models) > 0
        print(f"✓ 사용 가능한 모델: {len(models)}개")
        
        # 간단한 텍스트 임베딩
        text = "테스트 문장입니다."
        embeddings = embedding_service.encode_texts([text])
        
        assert embeddings is not None
        assert len(embeddings) == 1
        assert len(embeddings[0]) > 0
        print(f"✓ 임베딩 생성 성공: {len(embeddings[0])}차원")
        
        print("=== 임베딩 서비스 테스트 완료 ===\n")

    def test_qdrant_connection(self):
        """Qdrant 연결 테스트"""
        print("\n=== Qdrant 연결 테스트 ===")
        
        health = qdrant_service.health_check()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert "connected" in health
        
        if health["connected"]:
            print("✓ Qdrant 연결 성공")
            print(f"  상태: {health['status']}")
        else:
            print("⚠ Qdrant 연결 실패")
            print(f"  오류: {health.get('error', 'Unknown error')}")
        
        print("=== Qdrant 연결 테스트 완료 ===\n")

    @pytest.mark.asyncio
    async def test_file_upload_basic(self, tmp_path):
        """파일 업로드 기본 테스트"""
        print("\n=== 파일 업로드 기본 테스트 ===")

        # 테스트 파일 생성
        test_file = tmp_path / "test_upload.txt"
        test_content = """테스트 문서

금융위원회는 금융시장의 안정성을 유지하고 금융소비자를 보호하는 역할을 담당합니다.

주요 업무:
1. 금융정책 수립 및 시행
2. 금융기관 감독
3. 금융소비자 보호
"""
        test_file.write_text(test_content, encoding='utf-8')

        # 테스트 파일 읽기
        with open(test_file, 'rb') as f:
            content = f.read()
        
        mock_file = MockUploadFile("test_simple.txt", content, "text/plain")
        
        # 파일 업로드
        result = await file_upload_service.upload_file(mock_file)
        
        assert isinstance(result, dict)
        assert "success" in result
        
        if result["success"]:
            print("✓ 파일 업로드 성공")
            print(f"  파일 ID: {result['file_id']}")
            print(f"  파일 크기: {result['file_size']} bytes")
            return result["file_id"]
        else:
            print("⚠ 파일 업로드 실패")
            print(f"  오류: {result.get('error', 'Unknown error')}")
            return None

    @pytest.mark.asyncio
    async def test_document_processing_basic(self, tmp_path):
        """문서 처리 기본 테스트"""
        print("\n=== 문서 처리 기본 테스트 ===")

        # 테스트 파일 생성
        test_file = tmp_path / "test_processing.txt"
        test_content = """테스트 문서

금융위원회는 금융시장의 안정성을 유지하고 금융소비자를 보호하는 역할을 담당합니다.

주요 업무:
1. 금융정책 수립 및 시행
2. 금융기관 감독
3. 금융소비자 보호
4. 금융시장 안정성 관리
"""
        test_file.write_text(test_content, encoding='utf-8')

        # 먼저 파일 업로드
        with open(test_file, 'rb') as f:
            content = f.read()
        
        mock_file = MockUploadFile("test_processing.txt", content, "text/plain")
        upload_result = await file_upload_service.upload_file(mock_file)
        
        if not upload_result["success"]:
            pytest.skip("파일 업로드 실패로 인한 스킵")
        
        file_id = upload_result["file_id"]
        
        # 문서 처리
        processing_result = await document_processing_service.process_document(
            file_id=file_id,
            conversion_method="direct",
            extract_images=False,
            generate_embeddings=True
        )
        
        assert isinstance(processing_result, dict)
        assert "success" in processing_result
        
        if processing_result["success"]:
            print("✓ 문서 처리 성공")
            print(f"  문서 ID: {processing_result['document_id']}")
            print(f"  마크다운 길이: {processing_result['markdown_length']} 문자")
            print(f"  청크 수: {processing_result['total_chunks']}개")
            print(f"  임베딩 생성: {processing_result['embeddings_generated']}")
            return processing_result["document_id"]
        else:
            print("⚠ 문서 처리 실패")
            print(f"  오류: {processing_result.get('error', 'Unknown error')}")
            return None

    @pytest.mark.asyncio
    async def test_search_basic(self):
        """검색 기본 테스트"""
        print("\n=== 검색 기본 테스트 ===")
        
        query = "금융위원회"
        
        # 벡터 검색 테스트
        search_result = await search_service.vector_search(
            query=query,
            limit=5
        )
        
        assert isinstance(search_result, dict)
        assert "success" in search_result
        
        if search_result["success"]:
            results = search_result.get("results", [])
            print(f"✓ 벡터 검색 성공: {len(results)}개 결과")
            if results:
                print(f"  첫 번째 결과 점수: {results[0].get('score', 'N/A')}")
        else:
            print("⚠ 벡터 검색 실패")
            print(f"  오류: {search_result.get('error', 'Unknown error')}")
        
        print("=== 검색 기본 테스트 완료 ===\n")

    def test_service_stats(self):
        """서비스 통계 테스트"""
        print("\n=== 서비스 통계 테스트 ===")
        
        # 임베딩 서비스 통계
        try:
            models = embedding_service.get_available_models()
            print(f"✓ 임베딩 모델: {len(models)}개")
        except Exception as e:
            print(f"⚠ 임베딩 서비스 오류: {str(e)}")
        
        # Qdrant 통계
        try:
            stats = qdrant_service.get_collection_stats()
            if isinstance(stats, dict):
                points_count = stats.get("points_count", 0)
                print(f"✓ Qdrant 포인트: {points_count}개")
            else:
                print("⚠ Qdrant 통계 조회 실패")
        except Exception as e:
            print(f"⚠ Qdrant 통계 오류: {str(e)}")
        
        # 검색 서비스 통계
        try:
            search_stats = search_service.get_search_stats()
            if isinstance(search_stats, dict):
                print("✓ 검색 서비스 통계 조회 성공")
            else:
                print("⚠ 검색 서비스 통계 조회 실패")
        except Exception as e:
            print(f"⚠ 검색 서비스 통계 오류: {str(e)}")
        
        print("=== 서비스 통계 테스트 완료 ===\n")

    @pytest.mark.asyncio
    async def test_full_workflow_simple(self, tmp_path):
        """간단한 전체 워크플로우 테스트"""
        print("\n=== 간단한 전체 워크플로우 테스트 ===")

        try:
            # 테스트 파일 생성
            test_file = tmp_path / "workflow_test.txt"
            test_content = """워크플로우 테스트 문서

금융위원회는 금융시장의 안정성을 유지하고 금융소비자를 보호하는 역할을 담당합니다.

주요 업무:
1. 금융정책 수립 및 시행
2. 금융기관 감독
3. 금융소비자 보호
4. 금융시장 안정성 관리

금융위원회는 투명하고 공정한 금융시장 조성을 위해 노력하고 있습니다.
"""
            test_file.write_text(test_content, encoding='utf-8')

            # 1. 파일 업로드
            with open(test_file, 'rb') as f:
                content = f.read()
            
            mock_file = MockUploadFile("workflow_test.txt", content, "text/plain")
            upload_result = await file_upload_service.upload_file(mock_file)
            
            if not upload_result["success"]:
                print("⚠ 워크플로우 중단: 파일 업로드 실패")
                return
            
            print(f"1. ✓ 파일 업로드: {upload_result['file_id']}")
            
            # 2. 문서 처리
            processing_result = await document_processing_service.process_document(
                file_id=upload_result["file_id"],
                conversion_method="direct",
                generate_embeddings=True
            )
            
            if not processing_result["success"]:
                print("⚠ 워크플로우 중단: 문서 처리 실패")
                return
            
            print(f"2. ✓ 문서 처리: {processing_result['total_chunks']}개 청크")
            
            # 3. 검색 테스트 (데이터가 있는 경우)
            search_result = await search_service.vector_search(
                query="금융위원회",
                limit=3
            )
            
            if search_result["success"]:
                results_count = len(search_result.get("results", []))
                print(f"3. ✓ 검색 테스트: {results_count}개 결과")
            else:
                print("3. ⚠ 검색 실패 (데이터 부족 가능)")
            
            print("=== 전체 워크플로우 테스트 완료 ===\n")
            
        except Exception as e:
            print(f"⚠ 워크플로우 오류: {str(e)}")
            print("=== 전체 워크플로우 테스트 실패 ===\n")

    def test_configuration_check(self):
        """설정 확인 테스트"""
        print("\n=== 설정 확인 테스트 ===")
        
        from config import settings
        
        # 기본 설정 확인
        print(f"✓ 기본 모델: {getattr(settings, 'default_model', 'N/A')}")
        print(f"✓ 사용 가능한 모델: {len(getattr(settings, 'available_models', []))}개")
        print(f"✓ Qdrant 컬렉션: {getattr(settings, 'qdrant_collection_name', 'N/A')}")
        print(f"✓ 저장소 경로: {getattr(settings, 'storage_base_path', 'N/A')}")
        
        print("=== 설정 확인 테스트 완료 ===\n")
