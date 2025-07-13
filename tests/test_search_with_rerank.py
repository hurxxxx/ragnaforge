"""
Tests for search integration with rerank functionality.

This module tests the integration of rerank functionality with the unified search service,
including vector search, hybrid search, and API endpoints.
"""

import unittest
import asyncio
import os
import sys
import json
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.unified_search_service import unified_search_service
from services.rerank_service import rerank_service
from config import settings


class TestSearchWithRerank(unittest.TestCase):
    """Test cases for search integration with rerank functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        print("\n=== Search + Rerank 통합 테스트 시작 ===")
        
        # Initialize services
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize unified search service
            cls.unified_initialized = loop.run_until_complete(unified_search_service.initialize())
            if cls.unified_initialized:
                print("✅ Unified Search 서비스 초기화 성공")
            else:
                print("❌ Unified Search 서비스 초기화 실패")
            
            # Initialize rerank service
            cls.rerank_initialized = loop.run_until_complete(rerank_service.initialize())
            if cls.rerank_initialized:
                print("✅ Rerank 서비스 초기화 성공")
            else:
                print("❌ Rerank 서비스 초기화 실패")
                
        except Exception as e:
            print(f"❌ 서비스 초기화 중 오류: {str(e)}")
            cls.unified_initialized = False
            cls.rerank_initialized = False
        finally:
            loop.close()
    
    def setUp(self):
        """Set up each test."""
        self.test_query = "인공지능 기술 동향"
        
        # Sample documents for testing (simulating search results)
        self.sample_search_results = [
            {
                "id": "doc1",
                "score": 0.85,
                "content": "인공지능 기술의 최신 동향과 발전 방향에 대한 연구",
                "metadata": {
                    "file_name": "ai_trends.pdf",
                    "chunk_index": 1,
                    "text": "인공지능 기술의 최신 동향과 발전 방향에 대한 연구"
                }
            },
            {
                "id": "doc2",
                "score": 0.75,
                "content": "머신러닝과 딥러닝의 실제 적용 사례 분석",
                "metadata": {
                    "file_name": "ml_cases.pdf",
                    "chunk_index": 2,
                    "text": "머신러닝과 딥러닝의 실제 적용 사례 분석"
                }
            },
            {
                "id": "doc3",
                "score": 0.65,
                "content": "자연어 처리 기술을 활용한 챗봇 개발 가이드",
                "metadata": {
                    "file_name": "nlp_guide.pdf",
                    "chunk_index": 3,
                    "text": "자연어 처리 기술을 활용한 챗봇 개발 가이드"
                }
            }
        ]
    
    def test_services_initialization(self):
        """서비스 초기화 상태 테스트"""
        print("\n--- 서비스 초기화 상태 테스트 ---")
        
        print(f"✓ Unified Search 초기화: {self.unified_initialized}")
        print(f"✓ Rerank 서비스 초기화: {self.rerank_initialized}")
        print(f"✓ Rerank 활성화: {rerank_service.is_enabled()}")
        
        if self.unified_initialized:
            print(f"✓ Unified Search 상태: {unified_search_service.is_initialized}")
        
        if self.rerank_initialized:
            model_info = rerank_service.get_model_info()
            print(f"✓ Rerank 모델: {model_info.get('model_name', 'Unknown')}")
    
    def test_vector_search_with_rerank(self):
        """Vector Search + Rerank 통합 테스트"""
        print("\n--- Vector Search + Rerank 테스트 ---")
        
        if not self.unified_initialized or not self.rerank_initialized:
            print("⚠️  서비스가 초기화되지 않아 테스트를 건너뜁니다.")
            return
        
        async def run_vector_search_test():
            try:
                # Test without rerank
                result_no_rerank = await unified_search_service.vector_search(
                    query=self.test_query,
                    limit=3,
                    rerank=False
                )
                
                print(f"✓ Rerank 없는 검색 성공: {result_no_rerank.get('success', False)}")
                print(f"✓ 결과 수: {len(result_no_rerank.get('results', []))}")
                print(f"✓ Rerank 적용: {result_no_rerank.get('rerank_applied', False)}")
                
                # Test with rerank
                result_with_rerank = await unified_search_service.vector_search(
                    query=self.test_query,
                    limit=3,
                    rerank=True,
                    rerank_top_k=10
                )
                
                print(f"✓ Rerank 있는 검색 성공: {result_with_rerank.get('success', False)}")
                print(f"✓ 결과 수: {len(result_with_rerank.get('results', []))}")
                print(f"✓ Rerank 적용: {result_with_rerank.get('rerank_applied', False)}")
                
                if result_with_rerank.get('rerank_applied'):
                    rerank_info = result_with_rerank.get('rerank_info', {})
                    print(f"✓ Rerank 처리 시간: {rerank_info.get('processing_time', 0):.3f}초")
                    print(f"✓ Rerank 모델: {rerank_info.get('model_info', {}).get('model_name', 'Unknown')}")
                
                return True
                
            except Exception as e:
                print(f"❌ Vector Search + Rerank 테스트 실패: {str(e)}")
                return False
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(run_vector_search_test())
            self.assertTrue(success, "Vector Search + Rerank 테스트가 성공해야 합니다")
        finally:
            loop.close()
    
    def test_hybrid_search_with_rerank(self):
        """Hybrid Search + Rerank 통합 테스트"""
        print("\n--- Hybrid Search + Rerank 테스트 ---")
        
        if not self.unified_initialized or not self.rerank_initialized:
            print("⚠️  서비스가 초기화되지 않아 테스트를 건너뜁니다.")
            return
        
        async def run_hybrid_search_test():
            try:
                # Test without rerank
                result_no_rerank = await unified_search_service.hybrid_search(
                    query=self.test_query,
                    limit=3,
                    vector_weight=0.6,
                    text_weight=0.4,
                    rerank=False
                )
                
                print(f"✓ Rerank 없는 하이브리드 검색 성공: {result_no_rerank.get('success', False)}")
                print(f"✓ 결과 수: {len(result_no_rerank.get('results', []))}")
                print(f"✓ Rerank 적용: {result_no_rerank.get('rerank_applied', False)}")
                
                # Test with rerank
                result_with_rerank = await unified_search_service.hybrid_search(
                    query=self.test_query,
                    limit=3,
                    vector_weight=0.6,
                    text_weight=0.4,
                    rerank=True,
                    rerank_top_k=10
                )
                
                print(f"✓ Rerank 있는 하이브리드 검색 성공: {result_with_rerank.get('success', False)}")
                print(f"✓ 결과 수: {len(result_with_rerank.get('results', []))}")
                print(f"✓ Rerank 적용: {result_with_rerank.get('rerank_applied', False)}")
                
                if result_with_rerank.get('rerank_applied'):
                    rerank_info = result_with_rerank.get('rerank_info', {})
                    print(f"✓ Rerank 처리 시간: {rerank_info.get('processing_time', 0):.3f}초")
                    print(f"✓ Vector 결과 수: {result_with_rerank.get('vector_results_count', 0)}")
                    print(f"✓ Text 결과 수: {result_with_rerank.get('text_results_count', 0)}")
                
                return True
                
            except Exception as e:
                print(f"❌ Hybrid Search + Rerank 테스트 실패: {str(e)}")
                return False
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(run_hybrid_search_test())
            self.assertTrue(success, "Hybrid Search + Rerank 테스트가 성공해야 합니다")
        finally:
            loop.close()
    
    def test_rerank_performance_comparison(self):
        """Rerank 성능 비교 테스트"""
        print("\n--- Rerank 성능 비교 테스트 ---")
        
        if not self.rerank_initialized:
            print("⚠️  Rerank 서비스가 초기화되지 않아 테스트를 건너뜁니다.")
            return
        
        async def run_performance_test():
            try:
                # Test direct rerank service
                rerank_docs = []
                for result in self.sample_search_results:
                    doc = {
                        "id": result["id"],
                        "text": result["content"],
                        "score": result["score"],
                        "metadata": result["metadata"]
                    }
                    rerank_docs.append(doc)
                
                # Perform reranking
                rerank_result = await rerank_service.rerank_documents(
                    query=self.test_query,
                    documents=rerank_docs,
                    top_k=3,
                    use_cache=False  # Don't use cache for performance test
                )
                
                print(f"✓ 직접 Rerank 성공: {rerank_result.get('success', False)}")
                print(f"✓ 처리 시간: {rerank_result.get('processing_time', 0):.3f}초")
                print(f"✓ 원본 문서 수: {rerank_result.get('original_count', 0)}")
                print(f"✓ 재순위 문서 수: {rerank_result.get('reranked_count', 0)}")
                
                # Show reranked results
                documents = rerank_result.get('documents', [])
                if documents:
                    print("\n재순위 결과:")
                    for i, doc in enumerate(documents, 1):
                        print(f"  {i}. ID: {doc.get('id', 'N/A')}")
                        print(f"     Rerank 점수: {doc.get('rerank_score', 0):.3f}")
                        print(f"     원본 점수: {doc.get('original_score', 0):.3f}")
                
                return True
                
            except Exception as e:
                print(f"❌ 성능 비교 테스트 실패: {str(e)}")
                return False
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(run_performance_test())
            self.assertTrue(success, "성능 비교 테스트가 성공해야 합니다")
        finally:
            loop.close()
    
    def test_configuration_check(self):
        """통합 설정 확인 테스트"""
        print("\n--- 통합 설정 확인 테스트 ---")
        
        # Check search settings
        print(f"✓ Vector Backend: {getattr(settings, 'vector_backend', 'N/A')}")
        print(f"✓ Text Backend: {getattr(settings, 'text_backend', 'N/A')}")
        
        # Check rerank settings
        print(f"✓ Rerank 활성화: {getattr(settings, 'rerank_enabled', True)}")
        print(f"✓ Rerank 모델: {getattr(settings, 'rerank_model', 'N/A')}")
        print(f"✓ Rerank Top-K: {getattr(settings, 'rerank_top_k', 100)}")
        
        # Check service states
        print(f"✓ Unified Search 초기화: {unified_search_service.is_initialized}")
        print(f"✓ Rerank 서비스 활성화: {rerank_service.is_enabled()}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        print("\n=== Search + Rerank 통합 테스트 완료 ===")
        
        # Cleanup if initialized
        if getattr(cls, 'rerank_initialized', False):
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
