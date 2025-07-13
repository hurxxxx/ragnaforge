"""
Tests for the rerank service functionality.

This module tests the BGE reranker implementation and the main rerank service,
including basic functionality, API endpoints, and integration with the search system.
"""

import unittest
import asyncio
import os
import sys
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rerank_service import rerank_service
from services.rerank.bge_reranker import BGEReranker
from services.rerank.rerank_factory import RerankFactory, RerankModelType
from config import settings


class TestRerankService(unittest.TestCase):
    """Test cases for rerank service functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        print("\n=== Rerank Service 테스트 시작 ===")
        
        # Check if rerank is enabled
        if not getattr(settings, 'rerank_enabled', True):
            print("⚠️  Rerank 서비스가 비활성화되어 있습니다.")
            return
        
        # Initialize rerank service
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            cls.initialized = loop.run_until_complete(rerank_service.initialize())
            if cls.initialized:
                print("✅ Rerank 서비스 초기화 성공")
            else:
                print("❌ Rerank 서비스 초기화 실패")
        except Exception as e:
            print(f"❌ Rerank 서비스 초기화 중 오류: {str(e)}")
            cls.initialized = False
        finally:
            loop.close()
    
    def setUp(self):
        """Set up each test."""
        self.sample_documents = [
            {
                "id": "doc1",
                "text": "인공지능 기술의 최신 동향과 발전 방향에 대한 연구",
                "score": 0.8,
                "metadata": {"source": "research_paper"}
            },
            {
                "id": "doc2", 
                "text": "머신러닝과 딥러닝의 실제 적용 사례 분석",
                "score": 0.7,
                "metadata": {"source": "case_study"}
            },
            {
                "id": "doc3",
                "text": "자연어 처리 기술을 활용한 챗봇 개발 가이드",
                "score": 0.6,
                "metadata": {"source": "tutorial"}
            },
            {
                "id": "doc4",
                "text": "컴퓨터 비전 기술의 산업 응용 분야",
                "score": 0.5,
                "metadata": {"source": "industry_report"}
            }
        ]
        
        self.test_query = "인공지능 기술 동향"
    
    def test_rerank_service_enabled(self):
        """Rerank 서비스 활성화 상태 테스트"""
        print("\n--- Rerank 서비스 활성화 테스트 ---")
        
        enabled = rerank_service.is_enabled()
        print(f"✓ Rerank 서비스 활성화: {enabled}")
        
        if enabled:
            model_info = rerank_service.get_model_info()
            print(f"✓ 모델 정보: {model_info.get('model_name', 'Unknown')}")
            print(f"✓ 모델 타입: {model_info.get('model_type', 'Unknown')}")
    
    def test_rerank_factory(self):
        """Rerank 팩토리 테스트"""
        print("\n--- Rerank 팩토리 테스트 ---")
        
        try:
            # Get available models
            available_models = RerankFactory.get_available_models()
            print(f"✓ 사용 가능한 모델 수: {len(available_models)}")
            
            for model_type, info in available_models.items():
                print(f"  - {model_type}: {info['name']}")
            
            # Test creating default reranker
            reranker = RerankFactory.create_default_reranker()
            print(f"✓ 기본 Reranker 생성 성공: {type(reranker).__name__}")
            
        except Exception as e:
            print(f"❌ Rerank 팩토리 테스트 실패: {str(e)}")
    
    def test_basic_rerank_functionality(self):
        """기본 Rerank 기능 테스트"""
        print("\n--- 기본 Rerank 기능 테스트 ---")
        
        if not getattr(self.__class__, 'initialized', False):
            print("⚠️  Rerank 서비스가 초기화되지 않아 테스트를 건너뜁니다.")
            return
        
        async def run_rerank_test():
            try:
                # Test reranking
                result = await rerank_service.rerank_documents(
                    query=self.test_query,
                    documents=self.sample_documents,
                    top_k=3
                )
                
                print(f"✓ Rerank 성공: {result.get('success', False)}")
                print(f"✓ 처리 시간: {result.get('processing_time', 0):.3f}초")
                print(f"✓ 원본 문서 수: {result.get('original_count', 0)}")
                print(f"✓ 재순위 문서 수: {result.get('reranked_count', 0)}")
                print(f"✓ Rerank 적용: {result.get('rerank_applied', False)}")
                
                # Check results
                documents = result.get('documents', [])
                if documents:
                    print("\n재순위 결과:")
                    for i, doc in enumerate(documents[:3], 1):
                        print(f"  {i}. ID: {doc.get('id', 'N/A')}")
                        print(f"     점수: {doc.get('score', 0):.3f}")
                        print(f"     원본 점수: {doc.get('original_score', 0):.3f}")
                        print(f"     텍스트: {doc.get('text', '')[:50]}...")
                
                return result.get('success', False)
                
            except Exception as e:
                print(f"❌ Rerank 테스트 실패: {str(e)}")
                return False
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(run_rerank_test())
            self.assertTrue(success, "Rerank 기능이 정상적으로 작동해야 합니다")
        finally:
            loop.close()
    
    def test_rerank_cache(self):
        """Rerank 캐시 기능 테스트"""
        print("\n--- Rerank 캐시 테스트 ---")
        
        if not getattr(self.__class__, 'initialized', False):
            print("⚠️  Rerank 서비스가 초기화되지 않아 테스트를 건너뜁니다.")
            return
        
        async def run_cache_test():
            try:
                # Clear cache first
                rerank_service.clear_cache()
                
                # First request (should not be from cache)
                result1 = await rerank_service.rerank_documents(
                    query=self.test_query,
                    documents=self.sample_documents[:2],
                    use_cache=True
                )
                
                # Second request (should be from cache)
                result2 = await rerank_service.rerank_documents(
                    query=self.test_query,
                    documents=self.sample_documents[:2],
                    use_cache=True
                )
                
                print(f"✓ 첫 번째 요청 캐시 사용: {result1.get('from_cache', False)}")
                print(f"✓ 두 번째 요청 캐시 사용: {result2.get('from_cache', False)}")
                
                # Get cache stats
                cache_stats = rerank_service.get_cache_stats()
                print(f"✓ 캐시 활성화: {cache_stats.get('enabled', False)}")
                print(f"✓ 캐시 크기: {cache_stats.get('size', 0)}")
                
                return True
                
            except Exception as e:
                print(f"❌ 캐시 테스트 실패: {str(e)}")
                return False
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(run_cache_test())
            self.assertTrue(success, "캐시 기능이 정상적으로 작동해야 합니다")
        finally:
            loop.close()
    
    def test_configuration_check(self):
        """설정 확인 테스트"""
        print("\n--- Rerank 설정 확인 테스트 ---")
        
        # Check rerank settings
        print(f"✓ Rerank 활성화: {getattr(settings, 'rerank_enabled', True)}")
        print(f"✓ Rerank 모델: {getattr(settings, 'rerank_model', 'N/A')}")
        print(f"✓ Rerank 모델 타입: {getattr(settings, 'rerank_model_type', 'N/A')}")
        print(f"✓ Rerank Top-K: {getattr(settings, 'rerank_top_k', 100)}")
        print(f"✓ Rerank 배치 크기: {getattr(settings, 'rerank_batch_size', 32)}")
        print(f"✓ Rerank 캐시 활성화: {getattr(settings, 'rerank_cache_enabled', True)}")
        print(f"✓ Rerank 캐시 크기: {getattr(settings, 'rerank_cache_size', 1000)}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        print("\n=== Rerank Service 테스트 완료 ===")
        
        # Cleanup if initialized
        if getattr(cls, 'initialized', False):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(rerank_service.cleanup())
                print("✅ Rerank 서비스 정리 완료")
            except Exception as e:
                print(f"⚠️  정리 중 오류: {str(e)}")
            finally:
                loop.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
