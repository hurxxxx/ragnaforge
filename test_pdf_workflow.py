#!/usr/bin/env python3
"""
PDF 파일을 사용한 Ragnaforge 전체 워크플로우 테스트
sample2.pdf 파일로 업로드 → 처리 → 검색까지 전 과정 테스트
"""

import requests
import json
import time
from pathlib import Path
import sys

# 설정
BASE_URL = "http://localhost:8000"
API_KEY = "sk-kure-v1-test-key-12345"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
PDF_FILE_PATH = "./sample_docs/sample2.pdf"

class PDFWorkflowTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.pdf_path = Path(PDF_FILE_PATH)
        self.test_results = []
        self.file_id = None
        self.document_id = None
        
    def log_test(self, test_name: str, success: bool, message: str = "", duration: float = None, data: dict = None):
        """테스트 결과 로깅 - 임베딩 데이터 제외하고 유의미한 정보만 기록"""
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.2f}s)" if duration else ""
        print(f"{status} {test_name}{duration_str}")
        if message:
            print(f"    {message}")

        # 결과 데이터에서 유의미한 정보만 추출
        summary_data = {}
        if data and success:
            # 중요한 정보만 출력 및 저장
            if "file_id" in data:
                print(f"    File ID: {data['file_id']}")
                summary_data["file_id"] = data["file_id"]
            if "document_id" in data:
                print(f"    Document ID: {data['document_id']}")
                summary_data["document_id"] = data["document_id"]
            if "chunk_count" in data:
                print(f"    Chunks: {data['chunk_count']}")
                summary_data["chunk_count"] = data["chunk_count"]
            if "results" in data and isinstance(data["results"], list):
                print(f"    Results: {len(data['results'])} found")
                summary_data["result_count"] = len(data["results"])
                if data["results"]:
                    top_score = data["results"][0].get('score', 'N/A')
                    print(f"    Top score: {top_score}")
                    summary_data["top_score"] = top_score
                    # 첫 번째 결과의 텍스트 일부만 저장 (임베딩 제외)
                    first_result = data["results"][0]
                    if "text" in first_result:
                        summary_data["sample_text"] = first_result["text"][:200] + "..." if len(first_result["text"]) > 200 else first_result["text"]
            if "embedding_count" in data:
                print(f"    Embeddings: {data['embedding_count']} generated")
                summary_data["embedding_count"] = data["embedding_count"]
            if "total_files" in data:
                summary_data["total_files"] = data["total_files"]
            if "total_size" in data:
                summary_data["total_size"] = data["total_size"]

        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration,
            "summary": summary_data  # 임베딩 데이터 제외한 요약 정보만 저장
        })
        return success

    def check_server_health(self) -> bool:
        """서버 상태 확인"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return self.log_test(
                    "Server Health Check", 
                    True, 
                    f"Status: {data.get('status', 'unknown')}", 
                    duration,
                    data
                )
            else:
                return self.log_test("Server Health Check", False, f"HTTP {response.status_code}", duration)
                
        except Exception as e:
            return self.log_test("Server Health Check", False, f"Connection error: {str(e)}")

    def check_pdf_file(self) -> bool:
        """PDF 파일 존재 확인"""
        if not self.pdf_path.exists():
            return self.log_test("PDF File Check", False, f"File not found: {self.pdf_path}")
        
        file_size = self.pdf_path.stat().st_size
        return self.log_test(
            "PDF File Check", 
            True, 
            f"File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)"
        )

    def upload_pdf(self) -> bool:
        """PDF 파일 업로드"""
        start_time = time.time()
        try:
            with open(self.pdf_path, 'rb') as f:
                files = {'file': ('sample2.pdf', f, 'application/pdf')}
                response = requests.post(
                    f"{self.base_url}/v1/upload",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    files=files,
                    timeout=30
                )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.file_id = data.get('file_id')
                return self.log_test(
                    "PDF Upload", 
                    True, 
                    f"Upload successful", 
                    duration,
                    data
                )
            else:
                return self.log_test("PDF Upload", False, f"HTTP {response.status_code}: {response.text}", duration)
                
        except Exception as e:
            return self.log_test("PDF Upload", False, f"Error: {str(e)}")

    def process_document(self) -> bool:
        """문서 처리 및 임베딩 생성"""
        if not self.file_id:
            return self.log_test("Document Processing", False, "No file ID available")
        
        start_time = time.time()
        try:
            payload = {
                "file_id": self.file_id,
                "conversion_method": "marker",  # PDF에는 marker 사용
                "extract_images": True,
                "chunk_strategy": "sentence",
                "chunk_size": 300,
                "overlap": 50,
                "generate_embeddings": True,
                "embedding_model": "nlpai-lab/KURE-v1"
            }
            
            response = requests.post(
                f"{self.base_url}/v1/process",
                headers=self.headers,
                json=payload,
                timeout=120  # PDF 처리는 시간이 더 걸릴 수 있음
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.document_id = data.get('document_id')
                return self.log_test(
                    "Document Processing", 
                    True, 
                    f"Processing successful", 
                    duration,
                    data
                )
            else:
                return self.log_test("Document Processing", False, f"HTTP {response.status_code}: {response.text}", duration)
                
        except Exception as e:
            return self.log_test("Document Processing", False, f"Error: {str(e)}")

    def test_vector_search(self) -> bool:
        """벡터 검색 테스트"""
        start_time = time.time()
        try:
            payload = {
                "query": "금융위원회",
                "top_k": 5,
                "model": "nlpai-lab/KURE-v1"
            }

            response = requests.post(
                f"{self.base_url}/v1/search/vector",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                return self.log_test(
                    "Vector Search",
                    True,
                    f"Search successful",
                    duration,
                    data
                )
            else:
                return self.log_test("Vector Search", False, f"HTTP {response.status_code}: {response.text}", duration)

        except Exception as e:
            return self.log_test("Vector Search", False, f"Error: {str(e)}")

    def test_fulltext_search(self) -> bool:
        """풀텍스트 검색 테스트"""
        start_time = time.time()
        try:
            payload = {
                "query": "금융위원회",
                "top_k": 5
            }

            response = requests.post(
                f"{self.base_url}/v1/search/text",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            duration = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                return self.log_test(
                    "Fulltext Search",
                    True,
                    f"Search successful",
                    duration,
                    data
                )
            else:
                return self.log_test("Fulltext Search", False, f"HTTP {response.status_code}: {response.text}", duration)

        except Exception as e:
            return self.log_test("Fulltext Search", False, f"Error: {str(e)}")

    def test_hybrid_search(self) -> bool:
        """하이브리드 검색 테스트"""
        start_time = time.time()
        try:
            payload = {
                "query": "금융위원회",
                "top_k": 5,
                "vector_weight": 0.7,
                "text_weight": 0.3,
                "model": "nlpai-lab/KURE-v1"
            }
            
            response = requests.post(
                f"{self.base_url}/v1/search/hybrid",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return self.log_test(
                    "Hybrid Search", 
                    True, 
                    f"Search successful", 
                    duration,
                    data
                )
            else:
                return self.log_test("Hybrid Search", False, f"HTTP {response.status_code}: {response.text}", duration)
                
        except Exception as e:
            return self.log_test("Hybrid Search", False, f"Error: {str(e)}")

    def test_embedding_api(self) -> bool:
        """임베딩 API 직접 테스트"""
        start_time = time.time()
        try:
            payload = {
                "input": ["PDF 문서 처리 테스트", "임베딩 생성 확인"],
                "model": "nlpai-lab/KURE-v1"
            }
            
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                embeddings = data.get('data', [])
                return self.log_test(
                    "Embedding API", 
                    True, 
                    f"Generated {len(embeddings)} embeddings", 
                    duration,
                    {"embedding_count": len(embeddings)}
                )
            else:
                return self.log_test("Embedding API", False, f"HTTP {response.status_code}: {response.text}", duration)
                
        except Exception as e:
            return self.log_test("Embedding API", False, f"Error: {str(e)}")

    def check_storage_stats(self) -> bool:
        """저장소 통계 확인"""
        start_time = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/v1/storage/stats",
                headers=self.headers,
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('stats', {})
                return self.log_test(
                    "Storage Stats", 
                    True, 
                    f"Total size: {stats.get('total_size', 0):,} bytes", 
                    duration,
                    stats
                )
            else:
                return self.log_test("Storage Stats", False, f"HTTP {response.status_code}: {response.text}", duration)
                
        except Exception as e:
            return self.log_test("Storage Stats", False, f"Error: {str(e)}")

    def run_all_tests(self) -> dict:
        """모든 테스트 실행"""
        print("🚀 PDF 워크플로우 테스트 시작")
        print(f"📄 테스트 파일: {self.pdf_path}")
        print("=" * 60)
        
        # 1. 사전 확인
        print("\n📋 1. 사전 확인")
        if not self.check_server_health():
            print("❌ 서버가 실행되지 않았습니다. 테스트를 중단합니다.")
            return self.generate_summary()
        
        if not self.check_pdf_file():
            print("❌ PDF 파일을 찾을 수 없습니다. 테스트를 중단합니다.")
            return self.generate_summary()
        
        # 2. 기본 API 테스트
        print("\n🧠 2. 기본 API 테스트")
        self.test_embedding_api()
        
        # 3. 파일 업로드
        print("\n📁 3. 파일 업로드")
        if not self.upload_pdf():
            print("❌ 파일 업로드 실패. 후속 테스트를 건너뜁니다.")
            return self.generate_summary()
        
        # 4. 문서 처리
        print("\n⚙️ 4. 문서 처리")
        if not self.process_document():
            print("❌ 문서 처리 실패. 검색 테스트를 건너뜁니다.")
            return self.generate_summary()
        
        # 5. 검색 테스트
        print("\n🔍 5. 검색 테스트")
        self.test_vector_search()
        self.test_fulltext_search()
        self.test_hybrid_search()
        
        # 6. 시스템 상태 확인
        print("\n📊 6. 시스템 상태 확인")
        self.check_storage_stats()
        
        return self.generate_summary()

    def generate_summary(self) -> dict:
        """테스트 결과 요약 생성"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(
            result.get('duration', 0) for result in self.test_results 
            if result.get('duration') is not None
        )
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration,
            "test_results": self.test_results
        }
        
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {summary['success_rate']:.1f}%")
        print(f"총 소요시간: {total_duration:.2f}초")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        else:
            print("\n🎉 모든 테스트가 성공했습니다!")
        
        return summary


def main():
    """메인 실행 함수"""
    tester = PDFWorkflowTester()
    summary = tester.run_all_tests()

    # 임베딩 데이터를 제외한 간결한 결과만 저장
    clean_summary = {
        "total_tests": summary["total_tests"],
        "passed": summary["passed"],
        "failed": summary["failed"],
        "success_rate": summary["success_rate"],
        "total_duration": summary["total_duration"],
        "test_results": [
            {
                "test": result["test"],
                "success": result["success"],
                "message": result["message"],
                "duration": result.get("duration"),
                "summary": result.get("summary", {})  # 임베딩 제외한 요약 정보만
            }
            for result in summary["test_results"]
        ]
    }

    # 결과를 JSON 파일로 저장
    output_file = Path("pdf_test_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(clean_summary, f, indent=2, ensure_ascii=False)

    print(f"\n📄 상세 결과가 {output_file}에 저장되었습니다.")

    # 성공률이 80% 미만이면 실패로 처리
    if summary['success_rate'] < 80:
        print(f"\n💥 테스트 성공률이 80% 미만입니다. (현재: {summary['success_rate']:.1f}%)")
        sys.exit(1)
    else:
        print(f"\n✅ 테스트 성공! (성공률: {summary['success_rate']:.1f}%)")


if __name__ == "__main__":
    main()
