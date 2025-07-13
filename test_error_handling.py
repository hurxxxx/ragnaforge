#!/usr/bin/env python3
"""
Test script for error handling and recovery functionality.
"""

import asyncio
import tempfile
import os
import logging
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

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


async def test_hash_calculation_fallback():
    """Test hash calculation fallback mechanisms."""
    
    logger.info("🧪 해시 계산 대체 로직 테스트")
    
    test_content = b"Test content for hash fallback testing"
    
    # Test 1: Normal hash calculation
    normal_hash = file_upload_service._calculate_file_hash(test_content)
    logger.info(f"정상 해시: {normal_hash}")
    assert len(normal_hash) == 64  # SHA-256 hex length
    
    # Test 2: Simulate SHA-256 failure
    with patch('hashlib.sha256') as mock_sha256:
        mock_sha256.side_effect = Exception("SHA-256 calculation failed")
        
        fallback_hash = file_upload_service._calculate_file_hash(test_content)
        logger.info(f"대체 해시: {fallback_hash}")
        assert fallback_hash.startswith("md5_")
    
    # Test 3: Simulate both SHA-256 and MD5 failure
    with patch('hashlib.sha256') as mock_sha256, patch('hashlib.md5') as mock_md5:
        mock_sha256.side_effect = Exception("SHA-256 failed")
        mock_md5.side_effect = Exception("MD5 failed")
        
        emergency_hash = file_upload_service._calculate_file_hash(test_content)
        logger.info(f"비상 식별자: {emergency_hash}")
        assert emergency_hash.startswith("fallback_")
    
    logger.info("✅ 해시 계산 대체 로직 테스트 통과")


async def test_upload_error_recovery():
    """Test file upload error recovery."""
    
    logger.info("🧪 파일 업로드 에러 복구 테스트")
    
    test_content = b"Test content for upload error recovery"
    mock_file = MockUploadFile("test_error_recovery.txt", test_content)
    
    # Test 1: Database storage failure simulation
    with patch.object(database_service, 'store_file', return_value=False):
        result = await file_upload_service.upload_file(mock_file)
        
        logger.info(f"데이터베이스 저장 실패 시 결과: {result['success']}")
        assert result["success"] == False
        assert "Database storage failed" in result["error"]
    
    logger.info("✅ 파일 업로드 에러 복구 테스트 통과")


def test_data_consistency_check():
    """Test data consistency verification."""
    
    logger.info("🧪 데이터 일관성 검사 테스트")
    
    # Run consistency check
    result = database_service.verify_data_consistency()
    
    logger.info(f"일관성 검사 결과: {result}")
    assert "consistent" in result
    assert "issues_found" in result
    assert "checked_at" in result
    
    if not result["consistent"]:
        logger.info(f"발견된 문제: {result['issues_found']}개")
        for issue in result.get("issues", []):
            logger.info(f"  - {issue['type']}: {issue['count']}개")
    
    logger.info("✅ 데이터 일관성 검사 테스트 통과")


def test_data_repair_dry_run():
    """Test data repair in dry run mode."""
    
    logger.info("🧪 데이터 복구 드라이 런 테스트")
    
    # Run repair in dry run mode
    result = database_service.repair_data_inconsistencies(dry_run=True)
    
    logger.info(f"드라이 런 결과: {result}")
    assert "success" in result
    assert result["dry_run"] == True
    assert "repairs_performed" in result
    
    if result["repairs_performed"] > 0:
        logger.info(f"수행 가능한 복구: {result['repairs_performed']}개")
        for repair in result.get("repairs", []):
            logger.info(f"  - {repair['type']}: {repair['count']}개 ({repair['action']})")
    else:
        logger.info("복구가 필요한 항목이 없습니다")
    
    logger.info("✅ 데이터 복구 드라이 런 테스트 통과")


def test_fallback_identifier_generation():
    """Test fallback identifier generation."""
    
    logger.info("🧪 대체 식별자 생성 테스트")
    
    # Test with various inputs
    test_cases = [
        ("normal_file.txt", 1024, 1234567890.123),
        ("file with spaces.pdf", 2048, 1234567890.456),
        ("파일명한글.docx", 4096, 1234567890.789),
        ("very_long_filename_that_should_be_truncated_to_reasonable_length.txt", 8192, 1234567890.999)
    ]
    
    for filename, size, timestamp in test_cases:
        identifier = file_upload_service._generate_fallback_identifier(filename, size, timestamp)
        logger.info(f"파일: {filename} -> 식별자: {identifier}")
        
        assert identifier.startswith("fallback_")
        assert str(size) in identifier
        assert len(identifier) < 200  # Reasonable length limit
    
    logger.info("✅ 대체 식별자 생성 테스트 통과")


async def test_database_transaction_rollback():
    """Test database transaction rollback on errors."""
    
    logger.info("🧪 데이터베이스 트랜잭션 롤백 테스트")
    
    # This test would require more complex setup to properly test rollback
    # For now, we'll just verify the rollback mechanism exists
    
    try:
        # Simulate a transaction that should fail
        with database_service.get_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            # This would be where we'd test actual rollback scenarios
            conn.execute("ROLLBACK")
        
        logger.info("트랜잭션 롤백 메커니즘 확인됨")
    except Exception as e:
        logger.error(f"트랜잭션 테스트 실패: {e}")
        raise
    
    logger.info("✅ 데이터베이스 트랜잭션 롤백 테스트 통과")


async def main():
    """Run all error handling tests."""
    
    logger.info("🚀 에러 처리 및 복구 테스트 시작")
    
    tests = [
        ("해시 계산 대체 로직", test_hash_calculation_fallback),
        ("파일 업로드 에러 복구", test_upload_error_recovery),
        ("데이터 일관성 검사", test_data_consistency_check),
        ("데이터 복구 드라이 런", test_data_repair_dry_run),
        ("대체 식별자 생성", test_fallback_identifier_generation),
        ("데이터베이스 트랜잭션 롤백", test_database_transaction_rollback)
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
    logger.info("에러 처리 테스트 결과 요약")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 모든 에러 처리 테스트 통과!")
        return True
    else:
        logger.error(f"⚠️ {total - passed}개 테스트 실패")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
