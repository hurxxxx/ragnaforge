#!/usr/bin/env python3
"""
Test script for monitoring and logging functionality.
"""

import asyncio
import time
import logging
import json
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import services
from services.monitoring_service import monitoring_service
from services.file_upload_service import file_upload_service


class MockUploadFile:
    """Mock UploadFile for testing."""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.size = len(content)
    
    async def read(self) -> bytes:
        return self.content


def test_monitoring_service_initialization():
    """Test monitoring service initialization."""
    
    logger.info("🧪 모니터링 서비스 초기화 테스트")
    
    # Check if service is properly initialized
    assert monitoring_service.log_dir.exists()
    assert monitoring_service.max_memory_events == 1000
    assert len(monitoring_service.duplicate_events) >= 0
    assert len(monitoring_service.performance_metrics) >= 0
    
    logger.info("✅ 모니터링 서비스 초기화 테스트 통과")


def test_duplicate_event_logging():
    """Test duplicate event logging."""
    
    logger.info("🧪 중복 이벤트 로깅 테스트")
    
    # Clear existing events for clean test
    monitoring_service.duplicate_events.clear()
    
    # Log test duplicate events
    test_events = [
        {
            "file_hash": "test_hash_1",
            "filename": "test1.txt",
            "file_size": 1024,
            "file_type": "txt",
            "upload_count": 2,
            "detection_method": "hash"
        },
        {
            "file_hash": "test_hash_2",
            "filename": "test2.pdf",
            "file_size": 2048,
            "file_type": "pdf",
            "upload_count": 3,
            "detection_method": "cache"
        }
    ]
    
    for event in test_events:
        monitoring_service.log_duplicate_event(**event)
    
    # Verify events were logged
    assert len(monitoring_service.duplicate_events) == 2
    
    # Check event details
    logged_event = monitoring_service.duplicate_events[0]
    assert logged_event.file_hash == "test_hash_1"
    assert logged_event.filename == "test1.txt"
    assert logged_event.upload_count == 2
    assert logged_event.storage_saved_bytes == 1024  # (2-1) * 1024
    
    logger.info("✅ 중복 이벤트 로깅 테스트 통과")


def test_performance_metric_logging():
    """Test performance metric logging."""
    
    logger.info("🧪 성능 메트릭 로깅 테스트")
    
    # Clear existing metrics for clean test
    monitoring_service.performance_metrics.clear()
    
    # Log test performance metrics
    test_metrics = [
        {
            "operation": "upload",
            "duration_ms": 150.5,
            "file_size_bytes": 1024,
            "success": True
        },
        {
            "operation": "hash_calculation",
            "duration_ms": 25.3,
            "file_size_bytes": 2048,
            "success": True
        },
        {
            "operation": "upload",
            "duration_ms": 200.0,
            "file_size_bytes": 512,
            "success": False,
            "error_message": "Test error"
        }
    ]
    
    for metric in test_metrics:
        monitoring_service.log_performance_metric(**metric)
    
    # Verify metrics were logged
    assert len(monitoring_service.performance_metrics) == 3
    
    # Check metric details
    logged_metric = monitoring_service.performance_metrics[0]
    assert logged_metric.operation == "upload"
    assert logged_metric.duration_ms == 150.5
    assert logged_metric.success == True
    
    # Check failed metric
    failed_metric = monitoring_service.performance_metrics[2]
    assert failed_metric.success == False
    assert failed_metric.error_message == "Test error"
    
    logger.info("✅ 성능 메트릭 로깅 테스트 통과")


def test_duplicate_statistics():
    """Test duplicate statistics generation."""
    
    logger.info("🧪 중복 통계 생성 테스트")
    
    # Get statistics (should include events from previous test)
    stats = monitoring_service.get_duplicate_statistics(hours=24)
    
    logger.info(f"통계 결과: {stats}")
    
    # Verify statistics structure
    required_fields = [
        "period_hours", "total_duplicates", "unique_files", 
        "storage_saved_bytes", "storage_saved_mb", "detection_methods",
        "file_types", "top_duplicated_files", "hourly_distribution"
    ]
    
    for field in required_fields:
        assert field in stats, f"Missing field: {field}"
    
    # Verify data types
    assert isinstance(stats["total_duplicates"], int)
    assert isinstance(stats["storage_saved_mb"], (int, float))
    assert isinstance(stats["detection_methods"], dict)
    assert isinstance(stats["file_types"], dict)
    
    logger.info("✅ 중복 통계 생성 테스트 통과")


def test_performance_statistics():
    """Test performance statistics generation."""
    
    logger.info("🧪 성능 통계 생성 테스트")
    
    # Get statistics (should include metrics from previous test)
    stats = monitoring_service.get_performance_statistics(hours=24)
    
    logger.info(f"성능 통계: {stats}")
    
    # Verify statistics structure
    required_fields = [
        "period_hours", "total_operations", "success_rate",
        "average_duration_ms", "operations", "error_summary"
    ]
    
    for field in required_fields:
        assert field in stats, f"Missing field: {field}"
    
    # Verify data types and values
    assert isinstance(stats["total_operations"], int)
    assert 0 <= stats["success_rate"] <= 100
    assert isinstance(stats["average_duration_ms"], (int, float))
    assert isinstance(stats["operations"], dict)
    
    logger.info("✅ 성능 통계 생성 테스트 통과")


async def test_integrated_monitoring():
    """Test integrated monitoring with actual file upload."""
    
    logger.info("🧪 통합 모니터링 테스트")
    
    # Clear monitoring data
    monitoring_service.duplicate_events.clear()
    monitoring_service.performance_metrics.clear()
    
    # Create test files
    test_content = b"Test content for integrated monitoring"
    
    # Upload first file
    mock_file1 = MockUploadFile("monitor_test1.txt", test_content)
    result1 = await file_upload_service.upload_file(mock_file1)
    
    logger.info(f"첫 번째 업로드 결과: {result1['success']}")
    
    # Upload same file again (should trigger duplicate detection)
    mock_file2 = MockUploadFile("monitor_test2.txt", test_content)
    result2 = await file_upload_service.upload_file(mock_file2)
    
    logger.info(f"두 번째 업로드 결과: {result2['success']}, 중복: {result2.get('duplicate_detected', False)}")
    
    # Wait a moment for logging to complete
    await asyncio.sleep(0.1)
    
    # Check that monitoring data was collected
    assert len(monitoring_service.performance_metrics) > 0, "No performance metrics logged"
    
    # Check for duplicate event if duplicate was detected
    if result2.get('duplicate_detected'):
        assert len(monitoring_service.duplicate_events) > 0, "No duplicate events logged"
        
        # Verify duplicate event details
        duplicate_event = monitoring_service.duplicate_events[-1]
        assert duplicate_event.filename == "monitor_test2.txt"
        assert duplicate_event.upload_count >= 2
    
    # Get comprehensive statistics
    export_stats = monitoring_service.export_statistics(hours=1)
    
    logger.info(f"통합 통계: {export_stats}")
    
    # Verify export structure
    assert "duplicate_detection" in export_stats
    assert "performance" in export_stats
    assert "system_info" in export_stats
    
    logger.info("✅ 통합 모니터링 테스트 통과")


def test_log_file_creation():
    """Test log file creation and cleanup."""
    
    logger.info("🧪 로그 파일 생성 및 정리 테스트")
    
    # Log some events to ensure files are created
    monitoring_service.log_duplicate_event(
        file_hash="test_cleanup_hash",
        filename="cleanup_test.txt",
        file_size=1024,
        file_type="txt",
        upload_count=2
    )
    
    monitoring_service.log_performance_metric(
        operation="test_cleanup",
        duration_ms=100.0,
        file_size_bytes=1024,
        success=True
    )
    
    # Check if log files exist
    log_files = list(monitoring_service.log_dir.glob("*.jsonl"))
    assert len(log_files) > 0, "No log files created"
    
    logger.info(f"생성된 로그 파일: {[f.name for f in log_files]}")
    
    # Test cleanup (with 0 days to keep - should clean everything)
    # Note: This is just testing the method, not actually cleaning current logs
    try:
        monitoring_service.cleanup_old_logs(days_to_keep=365)  # Keep everything for test
        logger.info("로그 정리 메서드 실행 성공")
    except Exception as e:
        logger.error(f"로그 정리 실패: {e}")
        raise
    
    logger.info("✅ 로그 파일 생성 및 정리 테스트 통과")


async def main():
    """Run all monitoring and logging tests."""
    
    logger.info("🚀 모니터링 및 로깅 테스트 시작")
    
    tests = [
        ("모니터링 서비스 초기화", test_monitoring_service_initialization),
        ("중복 이벤트 로깅", test_duplicate_event_logging),
        ("성능 메트릭 로깅", test_performance_metric_logging),
        ("중복 통계 생성", test_duplicate_statistics),
        ("성능 통계 생성", test_performance_statistics),
        ("통합 모니터링", test_integrated_monitoring),
        ("로그 파일 생성 및 정리", test_log_file_creation)
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
    logger.info("모니터링 및 로깅 테스트 결과 요약")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 모든 모니터링 및 로깅 테스트 통과!")
        return True
    else:
        logger.error(f"⚠️ {total - passed}개 테스트 실패")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
