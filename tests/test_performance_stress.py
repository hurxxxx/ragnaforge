"""
성능 및 스트레스 테스트: Ragnaforge 시스템 부하 테스트
동시 요청, 대용량 파일, 연속 처리 등을 테스트
"""

import asyncio
import concurrent.futures
import json
import os
import time
import requests
from pathlib import Path
import threading

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_KEY = "sk-kure-v1-test-key-12345"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

class PerformanceStressTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.results = []
        
    def log_result(self, test_name, success, duration, details=None):
        """결과 로깅"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
        if details:
            print(f"    {details}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "duration": duration,
            "details": details
        })
    
    def test_concurrent_embeddings(self, num_requests=10):
        """동시 임베딩 요청 테스트"""
        print(f"\n🔄 동시 임베딩 요청 테스트 ({num_requests}개 요청)")
        
        def make_embedding_request(request_id):
            start_time = time.time()
            try:
                payload = {
                    "input": [f"동시 요청 테스트 {request_id}"],
                    "model": "nlpai-lab/KURE-v1"
                }
                response = requests.post(f"{self.base_url}/embeddings", 
                                       headers=self.headers, json=payload)
                duration = time.time() - start_time
                return {
                    "request_id": request_id,
                    "success": response.status_code == 200,
                    "duration": duration,
                    "status_code": response.status_code
                }
            except Exception as e:
                duration = time.time() - start_time
                return {
                    "request_id": request_id,
                    "success": False,
                    "duration": duration,
                    "error": str(e)
                }
        
        start_time = time.time()
        
        # 동시 요청 실행
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_embedding_request, i) for i in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_duration = time.time() - start_time
        
        # 결과 분석
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        avg_duration = sum(r["duration"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
        max_duration = max(r["duration"] for r in successful_requests) if successful_requests else 0
        min_duration = min(r["duration"] for r in successful_requests) if successful_requests else 0
        
        details = f"성공: {len(successful_requests)}/{num_requests}, 평균: {avg_duration:.2f}s, 최대: {max_duration:.2f}s, 최소: {min_duration:.2f}s"
        
        self.log_result("Concurrent Embeddings", len(failed_requests) == 0, total_duration, details)
        return len(failed_requests) == 0
    
    def test_large_text_embedding(self):
        """대용량 텍스트 임베딩 테스트"""
        print(f"\n📄 대용량 텍스트 임베딩 테스트")
        
        # 긴 텍스트 생성 (약 4000자)
        large_text = "한국어 자연어 처리는 매우 중요한 기술입니다. " * 200
        
        start_time = time.time()
        try:
            payload = {
                "input": [large_text],
                "model": "nlpai-lab/KURE-v1"
            }
            response = requests.post(f"{self.base_url}/embeddings", 
                                   headers=self.headers, json=payload)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                embedding_dim = len(data["data"][0]["embedding"])
                details = f"텍스트 길이: {len(large_text)}, 임베딩 차원: {embedding_dim}"
                self.log_result("Large Text Embedding", True, duration, details)
                return True
            else:
                self.log_result("Large Text Embedding", False, duration, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Large Text Embedding", False, duration, f"Error: {str(e)}")
            return False
    
    def test_batch_embedding_performance(self):
        """배치 임베딩 성능 테스트"""
        print(f"\n📦 배치 임베딩 성능 테스트")
        
        # 다양한 배치 크기 테스트
        batch_sizes = [1, 5, 10, 16]
        results = []
        
        for batch_size in batch_sizes:
            texts = [f"배치 테스트 텍스트 {i}" for i in range(batch_size)]
            
            start_time = time.time()
            try:
                payload = {
                    "input": texts,
                    "model": "nlpai-lab/KURE-v1"
                }
                response = requests.post(f"{self.base_url}/embeddings", 
                                       headers=self.headers, json=payload)
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    throughput = batch_size / duration
                    results.append({
                        "batch_size": batch_size,
                        "duration": duration,
                        "throughput": throughput,
                        "success": True
                    })
                    print(f"    배치 크기 {batch_size}: {duration:.2f}s, 처리량: {throughput:.2f} texts/sec")
                else:
                    results.append({
                        "batch_size": batch_size,
                        "duration": duration,
                        "success": False,
                        "status_code": response.status_code
                    })
            except Exception as e:
                duration = time.time() - start_time
                results.append({
                    "batch_size": batch_size,
                    "duration": duration,
                    "success": False,
                    "error": str(e)
                })
        
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            best_throughput = max(r["throughput"] for r in successful_results)
            best_batch = next(r for r in successful_results if r["throughput"] == best_throughput)
            details = f"최적 배치 크기: {best_batch['batch_size']}, 최대 처리량: {best_throughput:.2f} texts/sec"
            self.log_result("Batch Embedding Performance", True, 0, details)
            return True
        else:
            self.log_result("Batch Embedding Performance", False, 0, "모든 배치 테스트 실패")
            return False
    
    def test_search_performance(self):
        """검색 성능 테스트"""
        print(f"\n🔍 검색 성능 테스트")
        
        search_queries = [
            "MCP 기반 하이브리드 검색",
            "AI 에이전트 시스템",
            "벡터 데이터베이스",
            "문서 변환 처리",
            "한국어 자연어 처리"
        ]
        
        results = []
        
        for i, query in enumerate(search_queries):
            start_time = time.time()
            try:
                payload = {
                    "query": query,
                    "top_k": 5,
                    "search_type": "vector"
                }
                response = requests.post(f"{self.base_url}/v1/search", 
                                       headers=self.headers, json=payload)
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    result_count = len(data.get("results", []))
                    results.append({
                        "query": query,
                        "duration": duration,
                        "result_count": result_count,
                        "success": True
                    })
                    print(f"    쿼리 {i+1}: {duration:.2f}s, 결과: {result_count}개")
                else:
                    results.append({
                        "query": query,
                        "duration": duration,
                        "success": False,
                        "status_code": response.status_code
                    })
            except Exception as e:
                duration = time.time() - start_time
                results.append({
                    "query": query,
                    "duration": duration,
                    "success": False,
                    "error": str(e)
                })
        
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            avg_duration = sum(r["duration"] for r in successful_results) / len(successful_results)
            total_results = sum(r["result_count"] for r in successful_results)
            details = f"평균 검색 시간: {avg_duration:.2f}s, 총 결과: {total_results}개"
            self.log_result("Search Performance", True, avg_duration, details)
            return True
        else:
            self.log_result("Search Performance", False, 0, "모든 검색 테스트 실패")
            return False
    
    def test_storage_operations_performance(self):
        """Storage 작업 성능 테스트"""
        print(f"\n📁 Storage 작업 성능 테스트")
        
        operations = [
            ("stats", lambda: requests.get(f"{self.base_url}/v1/storage/stats", headers=self.headers)),
            ("list_uploads", lambda: requests.get(f"{self.base_url}/v1/storage/files/uploads", headers=self.headers)),
            ("list_processed", lambda: requests.get(f"{self.base_url}/v1/storage/files/processed", headers=self.headers)),
            ("cleanup", lambda: requests.post(f"{self.base_url}/v1/storage/cleanup", headers=self.headers, json={"max_age_hours": 24}))
        ]
        
        results = []
        
        for op_name, op_func in operations:
            start_time = time.time()
            try:
                response = op_func()
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    results.append({
                        "operation": op_name,
                        "duration": duration,
                        "success": True
                    })
                    print(f"    {op_name}: {duration:.3f}s")
                else:
                    results.append({
                        "operation": op_name,
                        "duration": duration,
                        "success": False,
                        "status_code": response.status_code
                    })
            except Exception as e:
                duration = time.time() - start_time
                results.append({
                    "operation": op_name,
                    "duration": duration,
                    "success": False,
                    "error": str(e)
                })
        
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            avg_duration = sum(r["duration"] for r in successful_results) / len(successful_results)
            details = f"성공한 작업: {len(successful_results)}/{len(operations)}, 평균 시간: {avg_duration:.3f}s"
            self.log_result("Storage Operations Performance", len(successful_results) == len(operations), avg_duration, details)
            return len(successful_results) == len(operations)
        else:
            self.log_result("Storage Operations Performance", False, 0, "모든 Storage 작업 실패")
            return False
    
    def run_all_tests(self):
        """모든 성능 테스트 실행"""
        print("🚀 Ragnaforge 성능 및 스트레스 테스트 시작")
        print("=" * 70)
        
        total_start_time = time.time()
        
        # 테스트 실행
        tests = [
            lambda: self.test_concurrent_embeddings(10),
            self.test_large_text_embedding,
            self.test_batch_embedding_performance,
            self.test_search_performance,
            self.test_storage_operations_performance
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            if test():
                passed += 1
            else:
                failed += 1
        
        total_duration = time.time() - total_start_time
        
        print("\n" + "=" * 70)
        print(f"📊 성능 테스트 결과 요약")
        print(f"✅ 통과: {passed}")
        print(f"❌ 실패: {failed}")
        print(f"⏱️  총 소요시간: {total_duration:.2f}초")
        print(f"📈 성공률: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 모든 성능 테스트가 성공적으로 통과했습니다!")
        else:
            print(f"\n⚠️  {failed}개의 테스트가 실패했습니다.")
        
        return failed == 0

if __name__ == "__main__":
    test_runner = PerformanceStressTest()
    success = test_runner.run_all_tests()
    exit(0 if success else 1)
