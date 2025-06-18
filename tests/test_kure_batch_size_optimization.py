#!/usr/bin/env python3
"""
KURE v1 모델 배치 사이즈 최적화 테스트
다양한 배치 사이즈에서 KURE v1 모델의 성능을 측정하여 최적값을 찾습니다.
"""

import os
import time
import json
import requests
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv
import statistics


# Load environment variables
load_dotenv()


class KureBatchSizeOptimizer:
    """KURE v1 모델 배치 사이즈 최적화 클래스"""
    
    def __init__(self):
        # API 설정
        self.kure_api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
        self.kure_base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        # KURE API 헤더
        self.kure_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.kure_api_key}"
        }
        
        # 테스트 결과 저장
        self.results = {}
        self.test_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        # 테스트할 배치 사이즈들 (최대 제한 찾기 위해 150까지)
        self.batch_sizes = [10,  32]
        
    def load_document(self, file_path: str) -> str:
        """문서 파일을 로드합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ 문서 로드 완료: {len(content)} 문자")
            return content
        except Exception as e:
            print(f"❌ 문서 로드 실패: {e}")
            return ""
    
    def chunk_document(self, text: str, chunk_size: int = 380, overlap: int = 70) -> List[str]:
        """KURE API를 사용하여 문서를 청킹합니다."""
        try:
            payload = {
                "text": text,
                "strategy": "recursive",
                "chunk_size": chunk_size,
                "overlap": overlap,
                "language": "ko"
            }
            
            response = requests.post(
                f"{self.kure_base_url}/v1/chunk",
                json=payload,
                headers=self.kure_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                chunks = [chunk['text'] for chunk in data['data']]
                print(f"✅ 청킹 완료: {len(chunks)}개 청크 생성")
                return chunks
            else:
                print(f"❌ 청킹 실패: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ 청킹 오류: {e}")
            return []

    def test_batch_size(self, chunks: List[str], batch_size: int, test_chunks: int = 500) -> Dict[str, Any]:
        """특정 배치 사이즈로 KURE 임베딩 성능을 테스트합니다."""
        print(f"\n🔍 배치 사이즈 {batch_size} 테스트 (청크 {test_chunks}개)...")
        
        # 테스트용 청크 샘플링
        test_sample = chunks[:test_chunks] if len(chunks) >= test_chunks else chunks
        
        start_time = time.time()
        embeddings = []
        batch_times = []
        request_count = 0
        
        try:
            for i in range(0, len(test_sample), batch_size):
                batch = test_sample[i:i + batch_size]
                batch_start = time.time()
                
                payload = {
                    "input": batch,
                    "model": "nlpai-lab/KURE-v1"
                }
                
                response = requests.post(
                    f"{self.kure_base_url}/embeddings",
                    json=payload,
                    headers=self.kure_headers
                )
                
                batch_end = time.time()
                batch_time = batch_end - batch_start
                batch_times.append(batch_time)
                request_count += 1
                
                if response.status_code == 200:
                    data = response.json()
                    batch_embeddings = [item['embedding'] for item in data['data']]
                    embeddings.extend(batch_embeddings)
                    
                    if i % (batch_size * 10) == 0:  # 진행상황 출력
                        print(f"   진행: {len(embeddings)}/{len(test_sample)} 청크 완료")
                else:
                    print(f"❌ 배치 실패: {response.status_code}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            print(f"❌ 임베딩 오류: {e}")
            return {"success": False, "error": str(e)}
        
        total_time = time.time() - start_time
        
        result = {
            "success": True,
            "batch_size": batch_size,
            "test_chunks": len(test_sample),
            "total_time": total_time,
            "avg_time_per_chunk": total_time / len(test_sample),
            "chunks_per_second": len(test_sample) / total_time,
            "request_count": request_count,
            "avg_batch_time": statistics.mean(batch_times),
            "batch_time_std": statistics.stdev(batch_times) if len(batch_times) > 1 else 0,
            "min_batch_time": min(batch_times),
            "max_batch_time": max(batch_times),
            "throughput_per_request": len(test_sample) / request_count,
            "requests_per_second": request_count / total_time
        }
        
        print(f"✅ 배치 사이즈 {batch_size} 완료:")
        print(f"   총 시간: {total_time:.2f}초")
        print(f"   처리 속도: {result['chunks_per_second']:.2f} 청크/초")
        print(f"   요청 수: {request_count}개")
        print(f"   평균 배치 시간: {result['avg_batch_time']:.3f}초")
        
        return result

    def run_batch_size_optimization(self, chunks: List[str]) -> Dict[str, Any]:
        """모든 배치 사이즈에 대해 최적화 테스트를 실행합니다."""
        print(f"\n🚀 KURE v1 배치 사이즈 최적화 테스트 시작")
        print(f"📄 테스트 배치 사이즈: {self.batch_sizes}")
        print("=" * 80)
        
        results = {}
        
        for batch_size in self.batch_sizes:
            result = self.test_batch_size(chunks, batch_size)
            if result["success"]:
                results[f"batch_{batch_size}"] = result
            else:
                print(f"❌ 배치 사이즈 {batch_size} 테스트 실패: {result.get('error', 'Unknown error')}")
        
        return results

    def analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """결과를 분석하여 최적 배치 사이즈를 찾습니다."""
        print(f"\n📊 배치 사이즈 최적화 결과 분석...")
        
        if not results:
            return {}
        
        # 성능 메트릭 추출
        batch_sizes = []
        chunks_per_second = []
        avg_batch_times = []
        requests_per_second = []
        
        for key, result in results.items():
            batch_sizes.append(result["batch_size"])
            chunks_per_second.append(result["chunks_per_second"])
            avg_batch_times.append(result["avg_batch_time"])
            requests_per_second.append(result["requests_per_second"])
        
        # 최적값 찾기
        max_throughput_idx = chunks_per_second.index(max(chunks_per_second))
        optimal_batch_size = batch_sizes[max_throughput_idx]
        max_throughput = chunks_per_second[max_throughput_idx]
        
        # 분석 결과
        analysis = {
            "optimal_batch_size": optimal_batch_size,
            "max_throughput": max_throughput,
            "performance_summary": {
                "batch_sizes": batch_sizes,
                "chunks_per_second": chunks_per_second,
                "avg_batch_times": avg_batch_times,
                "requests_per_second": requests_per_second
            },
            "recommendations": self.generate_recommendations(results)
        }
        
        print(f"🏆 최적 배치 사이즈: {optimal_batch_size}")
        print(f"🏆 최대 처리량: {max_throughput:.2f} 청크/초")
        
        return analysis

    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """성능 결과를 바탕으로 권장사항을 생성합니다."""
        recommendations = []

        # 처리량 기준 상위 3개 배치 사이즈 찾기
        sorted_results = sorted(results.items(),
                              key=lambda x: x[1]["chunks_per_second"],
                              reverse=True)

        top_3 = sorted_results[:3]

        recommendations.append(f"최고 성능: 배치 사이즈 {top_3[0][1]['batch_size']} ({top_3[0][1]['chunks_per_second']:.2f} 청크/초)")

        if len(top_3) > 1:
            recommendations.append(f"2위: 배치 사이즈 {top_3[1][1]['batch_size']} ({top_3[1][1]['chunks_per_second']:.2f} 청크/초)")

        if len(top_3) > 2:
            recommendations.append(f"3위: 배치 사이즈 {top_3[2][1]['batch_size']} ({top_3[2][1]['chunks_per_second']:.2f} 청크/초)")

        # 메모리 효율성 고려
        memory_efficient = [r for r in sorted_results if r[1]["batch_size"] <= 32]
        if memory_efficient:
            best_small = memory_efficient[0]
            recommendations.append(f"메모리 효율적 선택: 배치 사이즈 {best_small[1]['batch_size']} ({best_small[1]['chunks_per_second']:.2f} 청크/초)")

        # 안정성 고려 (배치 시간 표준편차가 낮은 것)
        stable_results = sorted(results.items(), key=lambda x: x[1]["batch_time_std"])
        if stable_results:
            most_stable = stable_results[0]
            recommendations.append(f"가장 안정적: 배치 사이즈 {most_stable[1]['batch_size']} (표준편차: {most_stable[1]['batch_time_std']:.3f}초)")

        return recommendations



    def save_results(self, results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """결과를 파일로 저장합니다."""
        # 결과 디렉토리 생성
        output_dir = f"test_outputs/{self.test_timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        # 전체 결과 JSON 저장
        full_report = {
            "test_info": {
                "timestamp": self.test_timestamp,
                "batch_sizes_tested": self.batch_sizes,
                "test_type": "KURE v1 Batch Size Optimization"
            },
            "detailed_results": results,
            "analysis": analysis
        }

        json_file = f"{output_dir}/kure_batch_size_optimization.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, ensure_ascii=False, indent=2)

        # 요약 리포트 저장
        summary_file = f"{output_dir}/batch_size_summary.md"
        self.generate_markdown_report(full_report, summary_file)

        print(f"✅ 결과 저장 완료:")
        print(f"   📄 JSON 리포트: {json_file}")
        print(f"   📄 요약 리포트: {summary_file}")

        return output_dir

    def generate_markdown_report(self, report: Dict[str, Any], file_path: str):
        """마크다운 형식의 요약 리포트를 생성합니다."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# KURE v1 배치 사이즈 최적화 리포트\n\n")
            f.write(f"**테스트 시간**: {report['test_info']['timestamp']}\n")
            f.write(f"**테스트 배치 사이즈**: {', '.join(map(str, report['test_info']['batch_sizes_tested']))}\n\n")

            # 최적화 결과
            analysis = report["analysis"]
            f.write("## 🏆 최적화 결과\n\n")
            f.write(f"**최적 배치 사이즈**: {analysis['optimal_batch_size']}\n")
            f.write(f"**최대 처리량**: {analysis['max_throughput']:.2f} 청크/초\n\n")

            # 성능 비교 테이블
            f.write("## 📊 성능 비교\n\n")
            f.write("| 배치 사이즈 | 처리량 (청크/초) | 평균 배치 시간 (초) | 요청/초 | 표준편차 |\n")
            f.write("|-------------|------------------|-------------------|---------|----------|\n")

            for result in report["detailed_results"].values():
                f.write(f"| {result['batch_size']} | {result['chunks_per_second']:.2f} | {result['avg_batch_time']:.3f} | {result['requests_per_second']:.2f} | {result['batch_time_std']:.3f} |\n")

            # 권장사항
            f.write("\n## 💡 권장사항\n\n")
            for i, rec in enumerate(analysis["recommendations"], 1):
                f.write(f"{i}. {rec}\n")

    def run_full_optimization(self, document_path: str) -> str:
        """전체 배치 사이즈 최적화 테스트를 실행합니다."""
        print("🧪 KURE v1 배치 사이즈 최적화 테스트 시작")
        print("=" * 80)

        # 1. 문서 로드
        document_content = self.load_document(document_path)
        if not document_content:
            print("❌ 문서 로드 실패")
            return ""

        # 2. 문서 청킹
        chunks = self.chunk_document(document_content)
        if not chunks:
            print("❌ 문서 청킹 실패")
            return ""

        # 3. 배치 사이즈 최적화 테스트
        results = self.run_batch_size_optimization(chunks)
        if not results:
            print("❌ 배치 사이즈 테스트 실패")
            return ""

        # 4. 결과 분석
        analysis = self.analyze_results(results)

        # 5. 결과 저장
        output_dir = self.save_results(results, analysis)

        # 6. 결과 출력
        self.print_summary(results, analysis)

        return output_dir

    def print_summary(self, results: Dict[str, Any], analysis: Dict[str, Any]):
        """결과 요약을 출력합니다."""
        print(f"\n🎉 배치 사이즈 최적화 테스트 완료!")
        print("=" * 80)

        print(f"\n🏆 최적화 결과:")
        print(f"  최적 배치 사이즈: {analysis['optimal_batch_size']}")
        print(f"  최대 처리량: {analysis['max_throughput']:.2f} 청크/초")

        print(f"\n📊 상위 성능 배치 사이즈:")
        sorted_results = sorted(results.items(),
                              key=lambda x: x[1]["chunks_per_second"],
                              reverse=True)

        for i, (_, result) in enumerate(sorted_results[:5], 1):
            print(f"  {i}. 배치 사이즈 {result['batch_size']}: {result['chunks_per_second']:.2f} 청크/초")

        print(f"\n💡 권장사항:")
        for i, rec in enumerate(analysis["recommendations"], 1):
            print(f"  {i}. {rec}")


def main():
    """메인 함수"""
    # 문서 경로
    document_path = "sample_docs/P02_01_01_001_20210101_marker.md"

    # 테스트 실행
    optimizer = KureBatchSizeOptimizer()
    output_dir = optimizer.run_full_optimization(document_path)

    if output_dir:
        print(f"\n📁 결과 저장 위치: {output_dir}")
    else:
        print("\n❌ 테스트 실패")


if __name__ == "__main__":
    main()
