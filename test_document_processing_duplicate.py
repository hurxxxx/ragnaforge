#!/usr/bin/env python3
"""
Test script for document processing pipeline duplicate detection.
"""

import asyncio
import tempfile
import os
import logging
from pathlib import Path
from io import BytesIO

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import services
from services.file_upload_service import file_upload_service
from services.document_processing_service import document_processing_service
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


async def test_document_processing_duplicate():
    """Test document processing pipeline with duplicate detection."""
    
    logger.info("🧪 문서 처리 파이프라인 중복 검사 테스트 시작")
    
    # Create test content
    test_content = b"# Test Document\n\nThis is a test document for duplicate detection in processing pipeline.\n\n## Section 1\n\nSome content here.\n\n## Section 2\n\nMore content here."
    
    # Test 1: Upload and process first document
    logger.info("📤 첫 번째 문서 업로드 및 처리")
    mock_file1 = MockUploadFile("test_doc.md", test_content, "text/markdown")
    
    # Upload file
    upload_result1 = await file_upload_service.upload_file(mock_file1)
    logger.info(f"업로드 결과: {upload_result1['success']}, 중복: {upload_result1.get('duplicate_detected', False)}")
    
    assert upload_result1["success"] == True
    assert upload_result1["duplicate_detected"] == False
    
    file_id1 = upload_result1["file_id"]
    
    # Process document
    process_result1 = await document_processing_service.process_document(
        file_id=file_id1,
        conversion_method="auto",
        chunk_strategy="sentence",
        chunk_size=500,
        overlap=50,
        generate_embeddings=False,  # Skip embeddings for faster testing
        embedding_model="nlpai-lab/KURE-v1"
    )
    
    logger.info(f"첫 번째 처리 결과: {process_result1['success']}")
    logger.info(f"문서 ID: {process_result1.get('document_id')}")
    logger.info(f"청크 수: {process_result1.get('total_chunks', 0)}")
    
    assert process_result1["success"] == True
    assert "document_id" in process_result1
    assert process_result1.get("duplicate_detected", False) == False
    
    document_id1 = process_result1["document_id"]
    
    # Test 2: Upload identical file with different name
    logger.info("📤 동일한 내용의 파일을 다른 이름으로 업로드")
    mock_file2 = MockUploadFile("same_content_different_name.md", test_content, "text/markdown")
    
    # Upload file (should detect duplicate)
    upload_result2 = await file_upload_service.upload_file(mock_file2)
    logger.info(f"두 번째 업로드 결과: {upload_result2['success']}, 중복: {upload_result2.get('duplicate_detected', False)}")
    
    assert upload_result2["success"] == True
    assert upload_result2["duplicate_detected"] == True
    
    # Get the file_id for the duplicate (it should be a new file_id but referencing existing content)
    file_id2 = upload_result2["existing_file"]["file_id"]
    
    # Test 3: Process the duplicate file (should return existing document)
    logger.info("📋 중복 파일 처리 시도")
    process_result2 = await document_processing_service.process_document(
        file_id=file_id2,
        conversion_method="auto",
        chunk_strategy="sentence",
        chunk_size=500,
        overlap=50,
        generate_embeddings=False,
        embedding_model="nlpai-lab/KURE-v1"
    )
    
    logger.info(f"두 번째 처리 결과: {process_result2['success']}")
    logger.info(f"중복 검출: {process_result2.get('duplicate_detected', False)}")
    logger.info(f"기존 문서: {process_result2.get('existing_document', False)}")
    logger.info(f"문서 ID: {process_result2.get('document_id')}")
    
    assert process_result2["success"] == True
    assert process_result2.get("duplicate_detected", False) == True
    assert process_result2.get("existing_document", False) == True
    assert process_result2["document_id"] == document_id1  # Should be same document ID
    
    # Test 4: Upload and process different content
    logger.info("📤 다른 내용의 문서 업로드 및 처리")
    different_content = b"# Different Document\n\nThis is completely different content.\n\n## Different Section\n\nDifferent content here."
    mock_file3 = MockUploadFile("different_doc.md", different_content, "text/markdown")
    
    # Upload file
    upload_result3 = await file_upload_service.upload_file(mock_file3)
    logger.info(f"세 번째 업로드 결과: {upload_result3['success']}, 중복: {upload_result3.get('duplicate_detected', False)}")
    
    assert upload_result3["success"] == True
    assert upload_result3["duplicate_detected"] == False
    
    file_id3 = upload_result3["file_id"]
    
    # Process document
    process_result3 = await document_processing_service.process_document(
        file_id=file_id3,
        conversion_method="auto",
        chunk_strategy="sentence",
        chunk_size=500,
        overlap=50,
        generate_embeddings=False,
        embedding_model="nlpai-lab/KURE-v1"
    )
    
    logger.info(f"세 번째 처리 결과: {process_result3['success']}")
    logger.info(f"문서 ID: {process_result3.get('document_id')}")
    
    assert process_result3["success"] == True
    assert process_result3.get("duplicate_detected", False) == False
    assert process_result3["document_id"] != document_id1  # Should be different document ID
    
    logger.info("✅ 모든 문서 처리 중복 검사 테스트 통과!")


async def main():
    """Run all tests."""
    try:
        await test_document_processing_duplicate()
        logger.info("🎉 모든 테스트 완료!")
        
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
