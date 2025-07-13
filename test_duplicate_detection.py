#!/usr/bin/env python3
"""
Test script for duplicate file detection functionality.
"""

import asyncio
import tempfile
import os
import logging
from pathlib import Path
from io import BytesIO
from fastapi import UploadFile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import services
from services.file_upload_service import file_upload_service
from services.database_service import database_service


class MockUploadFile:
    """Mock UploadFile for testing."""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "application/pdf"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.size = len(content)
    
    async def read(self) -> bytes:
        return self.content


async def test_duplicate_detection():
    """Test duplicate file detection functionality."""
    
    logger.info("🧪 중복 파일 검사 테스트 시작")
    
    # Create test content
    test_content = b"This is a test PDF content for duplicate detection testing."
    
    # Test 1: Upload first file
    logger.info("📤 첫 번째 파일 업로드 테스트")
    mock_file1 = MockUploadFile("test_document.pdf", test_content)
    
    result1 = await file_upload_service.upload_file(mock_file1)
    
    logger.info(f"첫 번째 업로드 결과: {result1}")
    
    assert result1["success"] == True
    assert result1["duplicate_detected"] == False
    assert "file_hash" in result1
    assert result1["upload_count"] == 1
    
    first_file_id = result1["file_id"]
    file_hash = result1["file_hash"]
    
    # Test 2: Upload identical file (should detect duplicate)
    logger.info("📤 동일한 파일 재업로드 테스트")
    mock_file2 = MockUploadFile("same_document_different_name.pdf", test_content)
    
    result2 = await file_upload_service.upload_file(mock_file2)
    
    logger.info(f"두 번째 업로드 결과: {result2}")
    
    assert result2["success"] == True
    assert result2["duplicate_detected"] == True
    assert result2["existing_file"]["file_id"] == first_file_id
    assert result2["existing_file"]["upload_count"] == 2
    
    # Test 3: Upload different file (should not detect duplicate)
    logger.info("📤 다른 파일 업로드 테스트")
    different_content = b"This is completely different content for testing."
    mock_file3 = MockUploadFile("different_document.pdf", different_content)
    
    result3 = await file_upload_service.upload_file(mock_file3)
    
    logger.info(f"세 번째 업로드 결과: {result3}")
    
    assert result3["success"] == True
    assert result3["duplicate_detected"] == False
    assert result3["file_hash"] != file_hash
    assert result3["upload_count"] == 1
    
    # Test 4: Verify database state
    logger.info("🔍 데이터베이스 상태 확인")
    existing_file = database_service.find_file_by_hash(file_hash)
    
    logger.info(f"데이터베이스 조회 결과: {existing_file}")
    
    assert existing_file is not None
    assert existing_file["file_id"] == first_file_id
    assert existing_file["upload_count"] == 2
    
    logger.info("✅ 모든 중복 검사 테스트 통과!")


async def test_hash_calculation():
    """Test file hash calculation."""
    
    logger.info("🔢 파일 해시 계산 테스트")
    
    # Test with known content
    test_content = b"Hello, World!"
    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"  # SHA-256 of "Hello, World!"
    
    calculated_hash = file_upload_service._calculate_file_hash(test_content)
    
    logger.info(f"예상 해시: {expected_hash}")
    logger.info(f"계산된 해시: {calculated_hash}")
    
    assert calculated_hash == expected_hash
    
    logger.info("✅ 해시 계산 테스트 통과!")


async def main():
    """Run all tests."""
    try:
        await test_hash_calculation()
        await test_duplicate_detection()
        logger.info("🎉 모든 테스트 완료!")
        
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
