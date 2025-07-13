#!/usr/bin/env python3
"""
Test script for performance optimization functionality.
"""

import asyncio
import time
import logging
import random
import string
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import services
from services.file_upload_service import file_upload_service
from services.database_service import database_service


class MockUploadFile:
    """Mock UploadFile for testing."""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.size = len(content)
    
    async def read(self) -> bytes:
        return self.content


def generate_test_content(size_mb: int) -> bytes:
    """Generate test content of specified size."""
    size_bytes = size_mb * 1024 * 1024
    # Generate random content
    content = ''.join(random.choices(string.ascii_letters + string.digits + ' \n', k=size_bytes))
    return content.encode('utf-8')


async def test_chunked_hash_calculation():
    """Test chunked hash calculation for large files."""
    
    logger.info("🧪 청크 단위 해시 계산 테스트")
    
    # Test with different file sizes
    test_sizes = [1, 5, 15, 25]  # MB
    
    for size_mb in test_sizes:
        logger.info(f"테스트 파일 크기: {size_mb}MB")
        
        content = generate_test_content(size_mb)
        
        # Measure hash calculation time
        start_time = time.time()
        file_hash = file_upload_service._calculate_file_hash(content)
        calculation_time = time.time() - start_time
        
        logger.info(f"  해시: {file_hash[:16]}...")
        logger.info(f"  계산 시간: {calculation_time:.3f}초")
        logger.info(f"  처리 속도: {size_mb / calculation_time:.1f}MB/s")
        
        # Verify hash is valid
        assert len(file_hash) == 64 or file_hash.startswith("md5_") or file_hash.startswith("fallback_")
    
    logger.info("✅ 청크 단위 해시 계산 테스트 통과")


async def test_async_hash_calculation():
    """Test asynchronous hash calculation."""
    
    logger.info("🧪 비동기 해시 계산 테스트")
    
    # Generate large test content (60MB to trigger async processing)
    large_content = generate_test_content(60)
    
    # Test async hash calculation
    start_time = time.time()
    file_hash = await file_upload_service._calculate_file_hash_async(large_content)
    async_time = time.time() - start_time
    
    logger.info(f"비동기 해시: {file_hash[:16]}...")
    logger.info(f"비동기 계산 시간: {async_time:.3f}초")
    
    # Compare with sync calculation
    start_time = time.time()
    sync_hash = file_upload_service._calculate_file_hash(large_content)
    sync_time = time.time() - start_time
    
    logger.info(f"동기 해시: {sync_hash[:16]}...")
    logger.info(f"동기 계산 시간: {sync_time:.3f}초")
    
    # Hashes should be the same
    assert file_hash == sync_hash
    
    logger.info("✅ 비동기 해시 계산 테스트 통과")


async def test_cache_performance():
    """Test hash cache performance."""
    
    logger.info("🧪 캐시 성능 테스트")
    
    # Clear cache first
    file_upload_service.clear_cache()
    
    # Generate test data
    test_hash = "test_hash_123456789abcdef"
    test_file_info = {
        "file_id": "test_id",
        "filename": "test_file.txt",
        "file_type": "txt",
        "file_size": 1024
    }
    
    # Test cache miss
    start_time = time.time()
    cached_result = file_upload_service._check_hash_cache(test_hash)
    cache_miss_time = time.time() - start_time
    
    assert cached_result is None
    logger.info(f"캐시 미스 시간: {cache_miss_time * 1000:.3f}ms")
    
    # Update cache
    file_upload_service._update_hash_cache(test_hash, test_file_info)
    
    # Test cache hit
    start_time = time.time()
    cached_result = file_upload_service._check_hash_cache(test_hash)
    cache_hit_time = time.time() - start_time
    
    assert cached_result == test_file_info
    logger.info(f"캐시 히트 시간: {cache_hit_time * 1000:.3f}ms")
    
    # Cache hit should be much faster
    assert cache_hit_time < cache_miss_time
    
    logger.info("✅ 캐시 성능 테스트 통과")


async def test_memory_efficiency():
    """Test memory efficiency for large files."""
    
    logger.info("🧪 메모리 효율성 테스트")
    
    # Test with large file (20MB)
    large_content = generate_test_content(20)
    mock_file = MockUploadFile("large_test.txt", large_content)
    
    # Monitor memory usage during upload
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # Upload file
    start_time = time.time()
    result = await file_upload_service.upload_file(mock_file)
    upload_time = time.time() - start_time
    
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_used = memory_after - memory_before
    
    logger.info(f"업로드 성공: {result['success']}")
    logger.info(f"업로드 시간: {upload_time:.3f}초")
    logger.info(f"메모리 사용량: {memory_used:.1f}MB")
    logger.info(f"파일 크기 대비 메모리 비율: {memory_used / 20 * 100:.1f}%")
    
    # Memory usage should be reasonable (less than 2x file size)
    assert memory_used < 40  # Less than 40MB for 20MB file
    
    logger.info("✅ 메모리 효율성 테스트 통과")


def test_database_performance():
    """Test database performance optimizations."""
    
    logger.info("🧪 데이터베이스 성능 테스트")
    
    # Test performance stats
    start_time = time.time()
    perf_stats = database_service.get_performance_stats()
    stats_time = time.time() - start_time
    
    logger.info(f"성능 통계 조회 시간: {stats_time:.3f}초")
    logger.info(f"테이블 통계: {perf_stats.get('table_stats', {})}")
    logger.info(f"인덱스 수: {perf_stats.get('index_count', 0)}")
    logger.info(f"DB 크기: {perf_stats.get('database_size_mb', 0)}MB")
    
    # Test batch operations
    test_pairs = [
        ("hash1", 5),
        ("hash2", 3),
        ("hash3", 7)
    ]
    
    start_time = time.time()
    batch_result = database_service.batch_update_upload_counts(test_pairs)
    batch_time = time.time() - start_time
    
    logger.info(f"배치 업데이트 성공: {batch_result}")
    logger.info(f"배치 업데이트 시간: {batch_time:.3f}초")
    
    # Performance should be reasonable
    assert stats_time < 1.0  # Less than 1 second
    assert batch_time < 0.5  # Less than 0.5 seconds
    
    logger.info("✅ 데이터베이스 성능 테스트 통과")


async def test_concurrent_uploads():
    """Test concurrent upload performance."""
    
    logger.info("🧪 동시 업로드 성능 테스트")
    
    # Generate multiple test files
    test_files = []
    for i in range(5):
        content = generate_test_content(2)  # 2MB each
        mock_file = MockUploadFile(f"concurrent_test_{i}.txt", content)
        test_files.append(mock_file)
    
    # Test sequential uploads
    start_time = time.time()
    sequential_results = []
    for mock_file in test_files:
        result = await file_upload_service.upload_file(mock_file)
        sequential_results.append(result)
    sequential_time = time.time() - start_time
    
    logger.info(f"순차 업로드 시간: {sequential_time:.3f}초")
    
    # Clear cache and prepare for concurrent test
    file_upload_service.clear_cache()
    
    # Test concurrent uploads
    start_time = time.time()
    concurrent_tasks = [file_upload_service.upload_file(mock_file) for mock_file in test_files]
    concurrent_results = await asyncio.gather(*concurrent_tasks)
    concurrent_time = time.time() - start_time
    
    logger.info(f"동시 업로드 시간: {concurrent_time:.3f}초")
    logger.info(f"성능 향상: {sequential_time / concurrent_time:.1f}x")
    
    # All uploads should succeed
    assert all(result['success'] for result in concurrent_results)
    
    # Concurrent should be faster (or at least not much slower)
    assert concurrent_time <= sequential_time * 1.2  # Allow 20% tolerance
    
    logger.info("✅ 동시 업로드 성능 테스트 통과")


async def main():
    """Run all performance tests."""
    
    logger.info("🚀 성능 최적화 테스트 시작")
    
    tests = [
        ("청크 단위 해시 계산", test_chunked_hash_calculation),
        ("비동기 해시 계산", test_async_hash_calculation),
        ("캐시 성능", test_cache_performance),
        ("메모리 효율성", test_memory_efficiency),
        ("데이터베이스 성능", test_database_performance),
        ("동시 업로드 성능", test_concurrent_uploads)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"테스트: {test_name}")
            logger.info(f"{'='*50}")
            
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
            
            results.append((test_name, True))
            logger.info(f"✅ {test_name} 통과")
            
        except Exception as e:
            logger.error(f"❌ {test_name} 실패: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("성능 최적화 테스트 결과 요약")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 모든 성능 최적화 테스트 통과!")
        return True
    else:
        logger.error(f"⚠️ {total - passed}개 테스트 실패")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
