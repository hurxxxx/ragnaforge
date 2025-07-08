#!/usr/bin/env python3
"""
Performance test for the unified search system.

This script tests the performance of vector, text, and hybrid search
with various query types and loads.
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, List, Any
import concurrent.futures
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceResult:
    """Performance test result."""
    test_name: str
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    requests_per_second: float
    success_rate: float
    total_requests: int
    successful_requests: int


class UnifiedSearchPerformanceTest:
    """Performance test suite for unified search system."""
    
    def __init__(self):
        self.test_queries = [
            "인공지능 기술",
            "머신러닝 알고리즘",
            "딥러닝 모델",
            "자연어 처리",
            "컴퓨터 비전",
            "데이터 분석",
            "빅데이터 처리",
            "클라우드 컴퓨팅",
            "소프트웨어 개발",
            "웹 개발 프레임워크"
        ]
        
    async def test_vector_search_performance(self, num_requests: int = 50) -> PerformanceResult:
        """Test vector search performance."""
        print(f"\n🔍 Vector Search Performance Test ({num_requests} requests)")
        print("-" * 60)
        
        from services.unified_search_service import unified_search_service
        
        if not unified_search_service.is_initialized:
            await unified_search_service.initialize()
        
        times = []
        successful = 0
        
        start_time = time.time()
        
        for i in range(num_requests):
            query = self.test_queries[i % len(self.test_queries)]
            
            try:
                request_start = time.time()
                result = await unified_search_service.vector_search(
                    query=query,
                    limit=10
                )
                request_time = time.time() - request_start
                
                if result.get("success"):
                    successful += 1
                    times.append(request_time)
                    
                    if i % 10 == 0:
                        print(f"  Request {i+1}: {request_time:.3f}s - {len(result.get('results', []))} results")
                
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")
        
        total_time = time.time() - start_time
        
        if times:
            return PerformanceResult(
                test_name="Vector Search",
                total_time=total_time,
                avg_time=statistics.mean(times),
                min_time=min(times),
                max_time=max(times),
                requests_per_second=successful / total_time,
                success_rate=successful / num_requests,
                total_requests=num_requests,
                successful_requests=successful
            )
        else:
            return PerformanceResult(
                test_name="Vector Search",
                total_time=total_time,
                avg_time=0,
                min_time=0,
                max_time=0,
                requests_per_second=0,
                success_rate=0,
                total_requests=num_requests,
                successful_requests=0
            )
    
    async def test_text_search_performance(self, num_requests: int = 50) -> PerformanceResult:
        """Test text search performance."""
        print(f"\n📝 Text Search Performance Test ({num_requests} requests)")
        print("-" * 60)
        
        from services.unified_search_service import unified_search_service
        
        if not unified_search_service.is_initialized:
            await unified_search_service.initialize()
        
        times = []
        successful = 0
        
        start_time = time.time()
        
        for i in range(num_requests):
            query = self.test_queries[i % len(self.test_queries)]
            
            try:
                request_start = time.time()
                result = await unified_search_service.text_search(
                    query=query,
                    limit=10
                )
                request_time = time.time() - request_start
                
                if result.get("success"):
                    successful += 1
                    times.append(request_time)
                    
                    if i % 10 == 0:
                        print(f"  Request {i+1}: {request_time:.3f}s - {len(result.get('results', []))} results")
                
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")
        
        total_time = time.time() - start_time
        
        if times:
            return PerformanceResult(
                test_name="Text Search",
                total_time=total_time,
                avg_time=statistics.mean(times),
                min_time=min(times),
                max_time=max(times),
                requests_per_second=successful / total_time,
                success_rate=successful / num_requests,
                total_requests=num_requests,
                successful_requests=successful
            )
        else:
            return PerformanceResult(
                test_name="Text Search",
                total_time=total_time,
                avg_time=0,
                min_time=0,
                max_time=0,
                requests_per_second=0,
                success_rate=0,
                total_requests=num_requests,
                successful_requests=0
            )
    
    async def test_hybrid_search_performance(self, num_requests: int = 50) -> PerformanceResult:
        """Test hybrid search performance."""
        print(f"\n🔀 Hybrid Search Performance Test ({num_requests} requests)")
        print("-" * 60)
        
        from services.unified_search_service import unified_search_service
        
        if not unified_search_service.is_initialized:
            await unified_search_service.initialize()
        
        times = []
        successful = 0
        
        start_time = time.time()
        
        for i in range(num_requests):
            query = self.test_queries[i % len(self.test_queries)]
            
            try:
                request_start = time.time()
                result = await unified_search_service.hybrid_search(
                    query=query,
                    limit=10,
                    vector_weight=0.6,
                    text_weight=0.4
                )
                request_time = time.time() - request_start
                
                if result.get("success"):
                    successful += 1
                    times.append(request_time)
                    
                    if i % 10 == 0:
                        print(f"  Request {i+1}: {request_time:.3f}s - {result.get('total_results', 0)} results")
                        print(f"    Vector: {result.get('vector_results_count', 0)}, Text: {result.get('text_results_count', 0)}")
                
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")
        
        total_time = time.time() - start_time
        
        if times:
            return PerformanceResult(
                test_name="Hybrid Search",
                total_time=total_time,
                avg_time=statistics.mean(times),
                min_time=min(times),
                max_time=max(times),
                requests_per_second=successful / total_time,
                success_rate=successful / num_requests,
                total_requests=num_requests,
                successful_requests=successful
            )
        else:
            return PerformanceResult(
                test_name="Hybrid Search",
                total_time=total_time,
                avg_time=0,
                min_time=0,
                max_time=0,
                requests_per_second=0,
                success_rate=0,
                total_requests=num_requests,
                successful_requests=0
            )

    def print_performance_summary(self, results: List[PerformanceResult]):
        """Print performance test summary."""
        print(f"\n{'='*80}")
        print("📊 Performance Test Summary")
        print(f"{'='*80}")

        for result in results:
            print(f"\n🧪 {result.test_name}")
            print(f"  Total Requests: {result.total_requests}")
            print(f"  Successful: {result.successful_requests} ({result.success_rate:.1%})")
            print(f"  Total Time: {result.total_time:.2f}s")
            print(f"  Average Time: {result.avg_time:.3f}s")
            print(f"  Min Time: {result.min_time:.3f}s")
            print(f"  Max Time: {result.max_time:.3f}s")
            print(f"  Requests/Second: {result.requests_per_second:.2f}")

        # Overall comparison
        print(f"\n📈 Performance Comparison:")
        print(f"{'Test':<20} {'Avg Time':<12} {'RPS':<8} {'Success':<8}")
        print("-" * 50)

        for result in results:
            print(f"{result.test_name:<20} {result.avg_time:<12.3f} {result.requests_per_second:<8.2f} {result.success_rate:<8.1%}")

    async def run_all_performance_tests(self, num_requests: int = 30):
        """Run all performance tests."""
        print("🚀 Starting Unified Search Performance Tests")
        print(f"📊 Test Configuration: {num_requests} requests per test")

        start_time = time.time()

        # Run tests
        tests = [
            ("Vector Search", self.test_vector_search_performance(num_requests)),
            ("Text Search", self.test_text_search_performance(num_requests)),
            ("Hybrid Search", self.test_hybrid_search_performance(num_requests))
        ]

        results = []
        for test_name, test in tests:
            try:
                print(f"\n🧪 Running {test_name} test...")
                result = await test
                results.append(result)
            except Exception as e:
                print(f"❌ {test_name} test failed: {e}")

        total_test_time = time.time() - start_time

        # Print summary
        self.print_performance_summary(results)

        print(f"\n⏱️  Total Test Time: {total_test_time:.2f}s")
        print("✅ Performance tests completed!")

        return results


async def main():
    """Run performance tests."""
    try:
        # Initialize unified search service
        from services.unified_search_service import unified_search_service

        print("🔧 Initializing unified search service...")
        init_success = await unified_search_service.initialize()

        if not init_success:
            print("❌ Failed to initialize unified search service")
            return

        print("✅ Unified search service initialized")

        # Run performance tests
        test_runner = UnifiedSearchPerformanceTest()
        await test_runner.run_all_performance_tests(num_requests=10)  # Reduced for faster testing

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
