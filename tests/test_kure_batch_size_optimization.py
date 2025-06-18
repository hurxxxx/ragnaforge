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
from typing import List, Dict, Any, Tuple, Optional
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
        self.batch_sizes = [10, 32, 64, 100, 128, 150]
        
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

        # 시간 측정 변수들
        total_start_time = time.time()
        embeddings = []
        batch_times = []
        network_times = []
        processing_times = []
        request_count = 0

        try:
            for i in range(0, len(test_sample), batch_size):
                batch = test_sample[i:i + batch_size]

                # 개별 배치 처리 시간 측정
                batch_start = time.time()

                payload = {
                    "input": batch,
                    "model": "nlpai-lab/KURE-v1"
                }

                # 네트워크 요청 시간 측정
                network_start = time.time()
                response = requests.post(
                    f"{self.kure_base_url}/embeddings",
                    json=payload,
                    headers=self.kure_headers
                )
                network_end = time.time()
                network_time = network_end - network_start
                network_times.append(network_time)

                # 응답 처리 시간 측정
                processing_start = time.time()
                batch_end = time.time()
                batch_time = batch_end - batch_start
                batch_times.append(batch_time)
                request_count += 1

                if response.status_code == 200:
                    data = response.json()
                    batch_embeddings = [item['embedding'] for item in data['data']]
                    embeddings.extend(batch_embeddings)
                    processing_end = time.time()
                    processing_time = processing_end - processing_start
                    processing_times.append(processing_time)

                    if i % (batch_size * 10) == 0:  # 진행상황 출력
                        print(f"   진행: {len(embeddings)}/{len(test_sample)} 청크 완료")
                else:
                    print(f"❌ 배치 실패: {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"   오류 상세: {error_data}")
                    except:
                        print(f"   응답 텍스트: {response.text}")
                    return {"success": False, "error": f"HTTP {response.status_code}", "response_text": response.text}

        except Exception as e:
            print(f"❌ 임베딩 오류: {e}")
            return {"success": False, "error": str(e)}

        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        
        # 상세 시간 분석
        avg_network_time = statistics.mean(network_times) if network_times else 0
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        total_network_time = sum(network_times)
        total_processing_time = sum(processing_times)

        result = {
            "success": True,
            "batch_size": batch_size,
            "test_chunks": len(test_sample),

            # 전체 시간 측정
            "total_time": total_time,
            "total_network_time": total_network_time,
            "total_processing_time": total_processing_time,
            "overhead_time": total_time - total_network_time,

            # 평균 시간 측정
            "avg_time_per_chunk": total_time / len(test_sample),
            "avg_network_time_per_request": avg_network_time,
            "avg_processing_time_per_request": avg_processing_time,
            "avg_batch_time": statistics.mean(batch_times),

            # 처리량 측정
            "chunks_per_second": len(test_sample) / total_time,
            "requests_per_second": request_count / total_time,
            "throughput_per_request": len(test_sample) / request_count,

            # 요청 통계
            "request_count": request_count,
            "batch_time_std": statistics.stdev(batch_times) if len(batch_times) > 1 else 0,
            "min_batch_time": min(batch_times),
            "max_batch_time": max(batch_times),

            # 시간 분포 분석
            "network_time_ratio": total_network_time / total_time if total_time > 0 else 0,
            "processing_time_ratio": total_processing_time / total_time if total_time > 0 else 0,
            "overhead_ratio": (total_time - total_network_time) / total_time if total_time > 0 else 0
        }
        
        print(f"✅ 배치 사이즈 {batch_size} 완료:")
        print(f"   📊 전체 처리 시간: {total_time:.2f}초")
        print(f"   🌐 네트워크 시간: {total_network_time:.2f}초 ({result['network_time_ratio']*100:.1f}%)")
        print(f"   ⚡ 처리 시간: {total_processing_time:.2f}초 ({result['processing_time_ratio']*100:.1f}%)")
        print(f"   🔄 오버헤드: {result['overhead_time']:.2f}초 ({result['overhead_ratio']*100:.1f}%)")
        print(f"   🚀 처리 속도: {result['chunks_per_second']:.2f} 청크/초")
        print(f"   📈 요청 수: {request_count}개 ({result['requests_per_second']:.2f} 요청/초)")
        print(f"   ⏱️  평균 배치 시간: {result['avg_batch_time']:.3f}초")
        
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

    def analyze_time_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """시간 성능을 상세 분석합니다."""
        if not results:
            return {}

        # 시간 분석 데이터 수집
        time_analysis = {
            "batch_sizes": [],
            "total_times": [],
            "network_times": [],
            "processing_times": [],
            "overhead_times": [],
            "network_ratios": [],
            "processing_ratios": [],
            "overhead_ratios": [],
            "efficiency_scores": []
        }

        for result in results.values():
            time_analysis["batch_sizes"].append(result["batch_size"])
            time_analysis["total_times"].append(result["total_time"])
            time_analysis["network_times"].append(result["total_network_time"])
            time_analysis["processing_times"].append(result["total_processing_time"])
            time_analysis["overhead_times"].append(result["overhead_time"])
            time_analysis["network_ratios"].append(result["network_time_ratio"])
            time_analysis["processing_ratios"].append(result["processing_time_ratio"])
            time_analysis["overhead_ratios"].append(result["overhead_ratio"])

            # 효율성 점수 계산 (처리량 / 전체시간)
            efficiency = result["chunks_per_second"] / result["total_time"]
            time_analysis["efficiency_scores"].append(efficiency)

        # 최적/최악 성능 찾기
        min_time_idx = time_analysis["total_times"].index(min(time_analysis["total_times"]))
        max_time_idx = time_analysis["total_times"].index(max(time_analysis["total_times"]))
        max_efficiency_idx = time_analysis["efficiency_scores"].index(max(time_analysis["efficiency_scores"]))

        analysis_summary = {
            "fastest_batch_size": time_analysis["batch_sizes"][min_time_idx],
            "fastest_time": time_analysis["total_times"][min_time_idx],
            "slowest_batch_size": time_analysis["batch_sizes"][max_time_idx],
            "slowest_time": time_analysis["total_times"][max_time_idx],
            "most_efficient_batch_size": time_analysis["batch_sizes"][max_efficiency_idx],
            "max_efficiency_score": time_analysis["efficiency_scores"][max_efficiency_idx],
            "time_improvement": (time_analysis["total_times"][max_time_idx] - time_analysis["total_times"][min_time_idx]) / time_analysis["total_times"][max_time_idx] * 100,
            "avg_network_ratio": statistics.mean(time_analysis["network_ratios"]) * 100,
            "avg_processing_ratio": statistics.mean(time_analysis["processing_ratios"]) * 100,
            "avg_overhead_ratio": statistics.mean(time_analysis["overhead_ratios"]) * 100
        }

        return {
            "time_data": time_analysis,
            "summary": analysis_summary
        }



    def save_results(self, results: Dict[str, Any], analysis: Dict[str, Any], time_analysis: Optional[Dict[str, Any]] = None) -> str:
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
            "analysis": analysis,
            "time_analysis": time_analysis
        }

        json_file = f"{output_dir}/kure_batch_size_optimization.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, ensure_ascii=False, indent=2)

        # 요약 리포트 저장
        summary_file = f"{output_dir}/batch_size_summary.md"
        self.generate_markdown_report(full_report, summary_file, time_analysis)

        print(f"✅ 결과 저장 완료:")
        print(f"   📄 JSON 리포트: {json_file}")
        print(f"   📄 요약 리포트: {summary_file}")

        return output_dir

    def generate_markdown_report(self, report: Dict[str, Any], file_path: str, time_analysis: Optional[Dict[str, Any]] = None):
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
            f.write("| 배치 사이즈 | 전체 시간 (초) | 처리량 (청크/초) | 네트워크 시간 (초) | 처리 시간 (초) | 오버헤드 (초) | 요청/초 |\n")
            f.write("|-------------|---------------|------------------|------------------|---------------|-------------|----------|\n")

            for result in report["detailed_results"].values():
                f.write(f"| {result['batch_size']} | {result['total_time']:.2f} | {result['chunks_per_second']:.2f} | {result['total_network_time']:.2f} | {result['total_processing_time']:.2f} | {result['overhead_time']:.2f} | {result['requests_per_second']:.2f} |\n")

            # 시간 분석 테이블
            f.write("\n## ⏱️ 시간 분석\n\n")
            f.write("| 배치 사이즈 | 네트워크 비율 | 처리 비율 | 오버헤드 비율 | 평균 배치 시간 | 표준편차 |\n")
            f.write("|-------------|--------------|-----------|-------------|---------------|----------|\n")

            for result in report["detailed_results"].values():
                f.write(f"| {result['batch_size']} | {result['network_time_ratio']*100:.1f}% | {result['processing_time_ratio']*100:.1f}% | {result['overhead_ratio']*100:.1f}% | {result['avg_batch_time']:.3f}초 | {result['batch_time_std']:.3f} |\n")

            # 시간 분석 요약
            if time_analysis and "summary" in time_analysis:
                summary = time_analysis["summary"]
                f.write("\n## ⚡ 시간 성능 분석\n\n")
                f.write(f"**가장 빠른 처리**: 배치 사이즈 {summary['fastest_batch_size']} ({summary['fastest_time']:.2f}초)\n")
                f.write(f"**가장 느린 처리**: 배치 사이즈 {summary['slowest_batch_size']} ({summary['slowest_time']:.2f}초)\n")
                f.write(f"**시간 개선율**: {summary['time_improvement']:.1f}%\n")
                f.write(f"**가장 효율적**: 배치 사이즈 {summary['most_efficient_batch_size']} (효율성 점수: {summary['max_efficiency_score']:.2f})\n\n")

                f.write("**평균 시간 분포:**\n")
                f.write(f"- 네트워크 시간: {summary['avg_network_ratio']:.1f}%\n")
                f.write(f"- 처리 시간: {summary['avg_processing_ratio']:.1f}%\n")
                f.write(f"- 오버헤드: {summary['avg_overhead_ratio']:.1f}%\n\n")

            # 권장사항
            f.write("## 💡 권장사항\n\n")
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

        # 5. 시간 성능 분석
        time_analysis = self.analyze_time_performance(results)

        # 6. 결과 저장
        output_dir = self.save_results(results, analysis, time_analysis)

        # 7. 결과 출력
        self.print_summary(results, analysis, time_analysis)

        return output_dir

    def print_summary(self, results: Dict[str, Any], analysis: Dict[str, Any], time_analysis: Optional[Dict[str, Any]] = None):
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

        # 시간 분석 요약 출력
        if time_analysis and "summary" in time_analysis:
            summary = time_analysis["summary"]
            print(f"\n⚡ 시간 성능 분석:")
            print(f"  🏃 가장 빠른 처리: 배치 사이즈 {summary['fastest_batch_size']} ({summary['fastest_time']:.2f}초)")
            print(f"  🐌 가장 느린 처리: 배치 사이즈 {summary['slowest_batch_size']} ({summary['slowest_time']:.2f}초)")
            print(f"  📈 시간 개선율: {summary['time_improvement']:.1f}%")
            print(f"  ⚡ 가장 효율적: 배치 사이즈 {summary['most_efficient_batch_size']} (효율성: {summary['max_efficiency_score']:.2f})")
            print(f"\n📊 평균 시간 분포:")
            print(f"  🌐 네트워크: {summary['avg_network_ratio']:.1f}%")
            print(f"  ⚙️  처리: {summary['avg_processing_ratio']:.1f}%")
            print(f"  🔄 오버헤드: {summary['avg_overhead_ratio']:.1f}%")

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
