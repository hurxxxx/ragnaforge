"""
통합 테스트: Ragnaforge 전체 워크플로우 테스트
파일 업로드 → 문서 처리 → 임베딩 생성 → 검색 → Storage 관리
"""

import asyncio
import json
import os
import time
import requests
from pathlib import Path

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_KEY = "sk-kure-v1-test-key-12345"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

class RagnaforgeIntegrationTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.test_results = []
        self.uploaded_file_id = None
        self.processed_document_id = None
        
    def log_test(self, test_name, success, message, duration=None):
        """테스트 결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.2f}s)" if duration else ""
        print(f"{status} {test_name}{duration_str}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration
        })
        
    def test_health_check(self):
        """1. 헬스 체크 테스트"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/health")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, 
                            f"Status: {data.get('status')}, Models: {len(data.get('models', []))}", duration)
                return True
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Health Check", False, f"Error: {str(e)}", duration)
            return False
    
    def test_storage_stats_initial(self):
        """2. 초기 Storage 통계 확인"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/v1/storage/stats", headers=self.headers)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('stats', {})
                total_size = stats.get('total_size', 0)
                self.log_test("Initial Storage Stats", True, 
                            f"Total size: {total_size} bytes", duration)
                return True
            else:
                self.log_test("Initial Storage Stats", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Initial Storage Stats", False, f"Error: {str(e)}", duration)
            return False
    
    def test_file_upload(self):
        """3. 파일 업로드 테스트"""
        start_time = time.time()
        try:
            # 테스트 파일 경로
            test_file_path = "sample_docs/기업 문서 검색 도구 분석.md"
            
            if not os.path.exists(test_file_path):
                duration = time.time() - start_time
                self.log_test("File Upload", False, f"Test file not found: {test_file_path}", duration)
                return False
            
            # 파일 업로드
            with open(test_file_path, 'rb') as f:
                files = {'file': f}
                headers_upload = {"Authorization": f"Bearer {API_KEY}"}
                response = requests.post(f"{self.base_url}/v1/upload", 
                                       headers=headers_upload, files=files)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.uploaded_file_id = data.get('file_id')
                    file_size = data.get('file_size', 0)
                    self.log_test("File Upload", True, 
                                f"File ID: {self.uploaded_file_id}, Size: {file_size} bytes", duration)
                    return True
                else:
                    self.log_test("File Upload", False, f"Upload failed: {data.get('error')}", duration)
                    return False
            else:
                self.log_test("File Upload", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("File Upload", False, f"Error: {str(e)}", duration)
            return False
    
    def test_document_processing(self):
        """4. 문서 처리 테스트"""
        if not self.uploaded_file_id:
            self.log_test("Document Processing", False, "No uploaded file ID")
            return False
            
        start_time = time.time()
        try:
            payload = {
                "file_id": self.uploaded_file_id,
                "generate_embeddings": True,
                "chunk_strategy": "recursive",
                "chunk_size": 380,
                "overlap": 70
            }
            
            response = requests.post(f"{self.base_url}/v1/process", 
                                   headers=self.headers, json=payload)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.processed_document_id = data.get('document_id')
                    chunks_count = data.get('total_chunks', 0)
                    self.log_test("Document Processing", True, 
                                f"Document ID: {self.processed_document_id}, Chunks: {chunks_count}", duration)
                    return True
                else:
                    self.log_test("Document Processing", False, f"Processing failed: {data.get('error')}", duration)
                    return False
            else:
                self.log_test("Document Processing", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Document Processing", False, f"Error: {str(e)}", duration)
            return False
    
    def test_storage_after_processing(self):
        """5. 처리 후 Storage 상태 확인"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/v1/storage/stats", headers=self.headers)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('stats', {})
                directories = stats.get('directories', {})
                
                uploads_count = directories.get('uploads', {}).get('file_count', 0)
                processed_count = directories.get('processed', {}).get('file_count', 0)
                
                self.log_test("Storage After Processing", True, 
                            f"Uploads: {uploads_count} files, Processed: {processed_count} files", duration)
                return True
            else:
                self.log_test("Storage After Processing", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Storage After Processing", False, f"Error: {str(e)}", duration)
            return False
    
    def test_vector_search(self):
        """6. Vector 검색 테스트"""
        start_time = time.time()
        try:
            payload = {
                "query": "MCP 기반 하이브리드 검색 시스템",
                "top_k": 5,
                "search_type": "vector"
            }
            
            response = requests.post(f"{self.base_url}/v1/search", 
                                   headers=self.headers, json=payload)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    results = data.get('results', [])
                    self.log_test("Vector Search", True, 
                                f"Found {len(results)} results", duration)
                    return True
                else:
                    self.log_test("Vector Search", False, f"Search failed: {data.get('error')}", duration)
                    return False
            else:
                self.log_test("Vector Search", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Vector Search", False, f"Error: {str(e)}", duration)
            return False
    
    def test_embeddings_api(self):
        """7. 임베딩 API 테스트"""
        start_time = time.time()
        try:
            payload = {
                "input": ["안녕하세요", "한국어 임베딩 테스트"],
                "model": "nlpai-lab/KURE-v1"
            }
            
            response = requests.post(f"{self.base_url}/embeddings",
                                   headers=self.headers, json=payload)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                embeddings_data = data.get('data', [])
                if embeddings_data:
                    embedding_dim = len(embeddings_data[0].get('embedding', []))
                    self.log_test("Embeddings API", True, 
                                f"Generated {len(embeddings_data)} embeddings, dim: {embedding_dim}", duration)
                    return True
                else:
                    self.log_test("Embeddings API", False, "No embeddings generated", duration)
                    return False
            else:
                self.log_test("Embeddings API", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Embeddings API", False, f"Error: {str(e)}", duration)
            return False
    
    def test_qdrant_stats(self):
        """8. Qdrant 통계 테스트"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/v1/qdrant/stats", headers=self.headers)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                points_count = data.get('points_count', 0)
                vectors_count = data.get('vectors_count', 0)
                self.log_test("Qdrant Stats", True, 
                            f"Points: {points_count}, Vectors: {vectors_count}", duration)
                return True
            else:
                self.log_test("Qdrant Stats", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Qdrant Stats", False, f"Error: {str(e)}", duration)
            return False
    
    def test_storage_cleanup(self):
        """9. Storage 정리 테스트"""
        start_time = time.time()
        try:
            payload = {"max_age_hours": 24}
            response = requests.post(f"{self.base_url}/v1/storage/cleanup", 
                                   headers=self.headers, json=payload)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                deleted_count = data.get('deleted_count', 0)
                self.log_test("Storage Cleanup", True, 
                            f"Deleted {deleted_count} temporary files", duration)
                return True
            else:
                self.log_test("Storage Cleanup", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Storage Cleanup", False, f"Error: {str(e)}", duration)
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 Ragnaforge 통합 테스트 시작")
        print("=" * 60)
        
        total_start_time = time.time()
        
        # 테스트 순서대로 실행
        tests = [
            self.test_health_check,
            self.test_storage_stats_initial,
            self.test_file_upload,
            self.test_document_processing,
            self.test_storage_after_processing,
            self.test_vector_search,
            self.test_embeddings_api,
            self.test_qdrant_stats,
            self.test_storage_cleanup
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
            print()  # 빈 줄 추가
        
        total_duration = time.time() - total_start_time
        
        print("=" * 60)
        print(f"📊 테스트 결과 요약")
        print(f"✅ 통과: {passed}")
        print(f"❌ 실패: {failed}")
        print(f"⏱️  총 소요시간: {total_duration:.2f}초")
        print(f"📈 성공률: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 모든 테스트가 성공적으로 통과했습니다!")
        else:
            print(f"\n⚠️  {failed}개의 테스트가 실패했습니다. 로그를 확인해주세요.")
        
        return failed == 0

if __name__ == "__main__":
    test_runner = RagnaforgeIntegrationTest()
    success = test_runner.run_all_tests()
    exit(0 if success else 1)
