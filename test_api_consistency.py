#!/usr/bin/env python3
"""
Test script for API endpoint consistency with duplicate detection.
"""

import asyncio
import requests
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration
BASE_URL = "http://localhost:8000"
API_KEY = "sk-kure-v1-test-key-12345"  # API key from config
HEADERS = {
    "Content-Type": "application/json"
}
if API_KEY:
    HEADERS["Authorization"] = f"Bearer {API_KEY}"


def test_file_list_api():
    """Test file list API with duplicate information."""
    
    logger.info("🧪 파일 목록 API 테스트")
    
    # Test file list endpoint
    response = requests.get(f"{BASE_URL}/v1/files", headers=HEADERS)
    
    logger.info(f"응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"성공: {data['success']}")
        logger.info(f"총 파일 수: {data['total']}")
        logger.info(f"페이지: {data['page']}/{data['total_pages']}")
        
        # Check if files have duplicate information
        if data['files']:
            first_file = data['files'][0]
            logger.info(f"첫 번째 파일 정보:")
            logger.info(f"  - 파일명: {first_file['filename']}")
            logger.info(f"  - 중복 여부: {first_file['is_duplicate']}")
            logger.info(f"  - 업로드 횟수: {first_file['upload_count']}")
            logger.info(f"  - 처리 여부: {first_file['is_processed']}")
            
            # Check for duplicate files
            duplicates = [f for f in data['files'] if f['is_duplicate']]
            logger.info(f"중복 파일 수: {len(duplicates)}")
        
        return True
    else:
        logger.error(f"파일 목록 API 실패: {response.text}")
        return False


def test_duplicate_stats_api():
    """Test duplicate statistics API."""
    
    logger.info("🧪 중복 통계 API 테스트")
    
    response = requests.get(f"{BASE_URL}/v1/duplicates/stats", headers=HEADERS)
    
    logger.info(f"응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"성공: {data['success']}")
        logger.info(f"총 파일 수: {data['total_files']}")
        logger.info(f"고유 파일 수: {data['unique_files']}")
        logger.info(f"중복 그룹 수: {data['duplicate_groups']}")
        logger.info(f"총 중복 파일 수: {data['total_duplicates']}")
        logger.info(f"절약된 저장 공간: {data['storage_saved_bytes']} bytes")
        
        return True
    else:
        logger.error(f"중복 통계 API 실패: {response.text}")
        return False


def test_duplicate_list_api():
    """Test duplicate groups list API."""
    
    logger.info("🧪 중복 그룹 목록 API 테스트")
    
    response = requests.get(f"{BASE_URL}/v1/duplicates", headers=HEADERS)
    
    logger.info(f"응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"성공: {data['success']}")
        logger.info(f"총 중복 그룹 수: {data['total_groups']}")
        logger.info(f"페이지: {data['page']}/{data['total_pages']}")
        
        if data['duplicate_groups']:
            first_group = data['duplicate_groups'][0]
            logger.info(f"첫 번째 중복 그룹:")
            logger.info(f"  - 파일 해시: {first_group['file_hash'][:16]}...")
            logger.info(f"  - 파일 수: {len(first_group['files'])}")
            logger.info(f"  - 총 업로드 횟수: {first_group['total_uploads']}")
            logger.info(f"  - 처리 여부: {first_group['is_processed']}")
            
            # Show files in the group
            for i, file_info in enumerate(first_group['files']):
                logger.info(f"    파일 {i+1}: {file_info['filename']}")
        
        return True
    else:
        logger.error(f"중복 그룹 목록 API 실패: {response.text}")
        return False


def test_upload_with_duplicate_info():
    """Test file upload API with duplicate detection."""
    
    logger.info("🧪 파일 업로드 API 중복 정보 테스트")
    
    # Create test file
    test_content = b"Test content for API consistency testing"
    
    # Upload file
    files = {
        'file': ('test_api_file.txt', test_content, 'text/plain')
    }
    headers_upload = {}
    if API_KEY:
        headers_upload["Authorization"] = f"Bearer {API_KEY}"
    
    response = requests.post(f"{BASE_URL}/v1/upload", files=files, headers=headers_upload)
    
    logger.info(f"업로드 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"업로드 성공: {data['success']}")
        logger.info(f"중복 검출: {data.get('duplicate_detected', False)}")
        
        if data.get('duplicate_detected'):
            logger.info(f"기존 파일 정보: {data.get('existing_file', {})}")
        else:
            logger.info(f"새 파일 ID: {data['file_id']}")
            logger.info(f"파일 해시: {data.get('file_hash', 'N/A')[:16]}...")
        
        return True, data.get('file_id')
    else:
        logger.error(f"파일 업로드 실패: {response.text}")
        return False, None


def test_document_processing_with_duplicate():
    """Test document processing API with duplicate detection."""
    
    logger.info("🧪 문서 처리 API 중복 검사 테스트")
    
    # First upload and process
    success, file_id = test_upload_with_duplicate_info()
    if not success or not file_id:
        return False
    
    # Process document
    process_data = {
        "file_id": file_id,
        "conversion_method": "auto",
        "chunk_strategy": "sentence",
        "chunk_size": 500,
        "overlap": 50,
        "generate_embeddings": False,
        "embedding_model": "nlpai-lab/KURE-v1"
    }
    
    response = requests.post(f"{BASE_URL}/v1/process", json=process_data, headers=HEADERS)
    
    logger.info(f"처리 응답 상태: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"처리 성공: {data['success']}")
        logger.info(f"중복 검출: {data.get('duplicate_detected', False)}")
        logger.info(f"기존 문서: {data.get('existing_document', False)}")
        logger.info(f"문서 ID: {data['document_id']}")
        
        if data.get('duplicate_detected'):
            logger.info(f"원본 파일명: {data.get('original_filename')}")
            logger.info(f"메시지: {data.get('message')}")
        
        return True
    else:
        logger.error(f"문서 처리 실패: {response.text}")
        return False


def main():
    """Run all API consistency tests."""
    
    logger.info("🚀 API 일관성 테스트 시작")
    
    tests = [
        ("파일 목록 API", test_file_list_api),
        ("중복 통계 API", test_duplicate_stats_api),
        ("중복 그룹 목록 API", test_duplicate_list_api),
        ("문서 처리 중복 검사 API", test_document_processing_with_duplicate)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"테스트: {test_name}")
            logger.info(f"{'='*50}")
            
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} 통과")
            else:
                logger.error(f"❌ {test_name} 실패")
                
        except Exception as e:
            logger.error(f"❌ {test_name} 오류: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("테스트 결과 요약")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 모든 API 일관성 테스트 통과!")
        return True
    else:
        logger.error(f"⚠️ {total - passed}개 테스트 실패")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
