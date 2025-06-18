#!/usr/bin/env python3
"""
임베딩 성능 및 정확도 비교 테스트
KURE 모델과 OpenAI 임베딩 모델의 속도와 정확도를 비교합니다.
"""

import os
import time
import json
import requests
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import statistics
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


# Load environment variables
load_dotenv()


class EmbeddingPerformanceComparator:
    """임베딩 모델 성능 비교 클래스"""
    
    def __init__(self):
        # API 설정
        self.kure_api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
        self.kure_base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # KURE API 헤더
        self.kure_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.kure_api_key}"
        }
        
        # OpenAI 클라이언트 초기화
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            print("⚠️ OpenAI API key not found. OpenAI tests will be skipped.")
            self.openai_client = None
        
        # 테스트 결과 저장
        self.results = {}
        self.test_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
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

    def test_kure_embedding(self, chunks: List[str]) -> Dict[str, Any]:
        """KURE 임베딩 성능을 테스트합니다."""
        print(f"\n🔍 KURE v1 임베딩 테스트 시작...")
        
        start_time = time.time()
        embeddings = []
        batch_times = []
        
        try:
            batch_size = 32  # KURE 최적 배치 크기
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
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
                
                if response.status_code == 200:
                    data = response.json()
                    batch_embeddings = [item['embedding'] for item in data['data']]
                    embeddings.extend(batch_embeddings)
                    
                    print(f"   배치 {i//batch_size + 1}: {len(batch)}개 청크, {batch_time:.2f}초")
                else:
                    print(f"❌ KURE 배치 실패: {response.status_code}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            print(f"❌ KURE 임베딩 오류: {e}")
            return {"success": False, "error": str(e)}
        
        total_time = time.time() - start_time
        
        result = {
            "success": True,
            "model": "KURE-v1",
            "total_chunks": len(chunks),
            "total_time": total_time,
            "avg_time_per_chunk": total_time / len(chunks),
            "chunks_per_second": len(chunks) / total_time,
            "batch_times": batch_times,
            "avg_batch_time": statistics.mean(batch_times),
            "embeddings": embeddings,
            "embedding_dimension": len(embeddings[0]) if embeddings else 0
        }
        
        print(f"✅ KURE 테스트 완료: {len(chunks)}개 청크, {total_time:.2f}초")
        print(f"   평균 속도: {result['chunks_per_second']:.2f} 청크/초")
        
        return result

    def test_openai_embedding(self, chunks: List[str], model: str) -> Dict[str, Any]:
        """OpenAI 임베딩 성능을 테스트합니다."""
        if not self.openai_client:
            return {"success": False, "error": "OpenAI client not available"}
        
        print(f"\n🔍 OpenAI {model} 임베딩 테스트 시작...")
        
        start_time = time.time()
        embeddings = []
        batch_times = []
        total_tokens = 0
        
        try:
            batch_size = 100  # OpenAI API 제한 고려
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_start = time.time()
                
                response = self.openai_client.embeddings.create(
                    input=batch,
                    model=model
                )
                
                batch_end = time.time()
                batch_time = batch_end - batch_start
                batch_times.append(batch_time)
                
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                total_tokens += response.usage.total_tokens
                
                print(f"   배치 {i//batch_size + 1}: {len(batch)}개 청크, {batch_time:.2f}초")
                
                # API 제한 준수
                time.sleep(0.1)
        
        except Exception as e:
            print(f"❌ OpenAI 임베딩 오류: {e}")
            return {"success": False, "error": str(e)}
        
        total_time = time.time() - start_time
        
        result = {
            "success": True,
            "model": model,
            "total_chunks": len(chunks),
            "total_time": total_time,
            "avg_time_per_chunk": total_time / len(chunks),
            "chunks_per_second": len(chunks) / total_time,
            "batch_times": batch_times,
            "avg_batch_time": statistics.mean(batch_times),
            "embeddings": embeddings,
            "embedding_dimension": len(embeddings[0]) if embeddings else 0,
            "total_tokens": total_tokens
        }
        
        print(f"✅ OpenAI {model} 테스트 완료: {len(chunks)}개 청크, {total_time:.2f}초")
        print(f"   평균 속도: {result['chunks_per_second']:.2f} 청크/초")
        print(f"   총 토큰: {total_tokens}")
        
        return result

    def analyze_embedding_quality(self, embeddings: List[List[float]], model_name: str) -> Dict[str, Any]:
        """임베딩 품질을 분석합니다."""
        print(f"\n📊 {model_name} 임베딩 품질 분석...")

        embeddings_array = np.array(embeddings)

        # 1. 기본 통계
        norms = np.linalg.norm(embeddings_array, axis=1)

        # 2. 유사도 분포 분석
        similarity_matrix = cosine_similarity(embeddings_array)
        # 대각선 제외 (자기 자신과의 유사도)
        upper_triangle = np.triu(similarity_matrix, k=1)
        similarities = upper_triangle[upper_triangle != 0]

        # 3. 차원별 분산 분석
        dimension_variances = np.var(embeddings_array, axis=0)

        # 4. 클러스터링 분석 (샘플이 충분한 경우)
        clustering_score = None
        if len(embeddings) >= 10:
            try:
                n_clusters = min(5, len(embeddings) // 2)
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(embeddings_array)

                # 실루엣 스코어 계산
                from sklearn.metrics import silhouette_score
                clustering_score = silhouette_score(embeddings_array, cluster_labels)
            except Exception as e:
                print(f"   클러스터링 분석 실패: {e}")

        quality_metrics = {
            "embedding_count": len(embeddings),
            "dimension": len(embeddings[0]),
            "norm_stats": {
                "mean": float(np.mean(norms)),
                "std": float(np.std(norms)),
                "min": float(np.min(norms)),
                "max": float(np.max(norms))
            },
            "similarity_stats": {
                "mean": float(np.mean(similarities)),
                "std": float(np.std(similarities)),
                "min": float(np.min(similarities)),
                "max": float(np.max(similarities)),
                "median": float(np.median(similarities))
            },
            "dimension_variance_stats": {
                "mean": float(np.mean(dimension_variances)),
                "std": float(np.std(dimension_variances)),
                "min": float(np.min(dimension_variances)),
                "max": float(np.max(dimension_variances))
            },
            "clustering_score": clustering_score
        }

        print(f"   임베딩 개수: {quality_metrics['embedding_count']}")
        print(f"   차원: {quality_metrics['dimension']}")
        print(f"   평균 노름: {quality_metrics['norm_stats']['mean']:.4f}")
        print(f"   평균 유사도: {quality_metrics['similarity_stats']['mean']:.4f}")
        if clustering_score:
            print(f"   클러스터링 점수: {clustering_score:.4f}")

        return quality_metrics

    def compare_models(self, chunks: List[str]) -> Dict[str, Any]:
        """모든 모델을 비교합니다."""
        print(f"\n🚀 임베딩 모델 성능 비교 시작")
        print(f"📄 총 {len(chunks)}개 청크로 테스트")
        print("=" * 80)

        results = {}

        # KURE v1 테스트
        kure_result = self.test_kure_embedding(chunks)
        if kure_result["success"]:
            kure_result["quality"] = self.analyze_embedding_quality(
                kure_result["embeddings"], "KURE v1"
            )
            results["kure_v1"] = kure_result

        # OpenAI text-embedding-3-small 테스트
        if self.openai_client:
            openai_small_result = self.test_openai_embedding(chunks, "text-embedding-3-small")
            if openai_small_result["success"]:
                openai_small_result["quality"] = self.analyze_embedding_quality(
                    openai_small_result["embeddings"], "OpenAI text-embedding-3-small"
                )
                results["openai_small"] = openai_small_result

            # OpenAI text-embedding-3-large 테스트
            openai_large_result = self.test_openai_embedding(chunks, "text-embedding-3-large")
            if openai_large_result["success"]:
                openai_large_result["quality"] = self.analyze_embedding_quality(
                    openai_large_result["embeddings"], "OpenAI text-embedding-3-large"
                )
                results["openai_large"] = openai_large_result

        return results

    def generate_performance_report(self, results: Dict[str, Any], chunks: List[str]) -> Dict[str, Any]:
        """성능 비교 리포트를 생성합니다."""
        print(f"\n📋 성능 비교 리포트 생성...")

        report = {
            "test_info": {
                "timestamp": self.test_timestamp,
                "total_chunks": len(chunks),
                "chunk_sample": chunks[0][:100] + "..." if chunks else "",
                "models_tested": list(results.keys())
            },
            "performance_comparison": {},
            "quality_comparison": {},
            "summary": {}
        }

        # 성능 비교
        for model_name, result in results.items():
            if result["success"]:
                report["performance_comparison"][model_name] = {
                    "total_time": result["total_time"],
                    "avg_time_per_chunk": result["avg_time_per_chunk"],
                    "chunks_per_second": result["chunks_per_second"],
                    "embedding_dimension": result["embedding_dimension"]
                }

                if "total_tokens" in result:
                    report["performance_comparison"][model_name]["total_tokens"] = result["total_tokens"]

                # 품질 비교
                if "quality" in result:
                    report["quality_comparison"][model_name] = result["quality"]

        # 요약 생성
        if results:
            fastest_model = min(results.keys(),
                              key=lambda x: results[x]["total_time"] if results[x]["success"] else float('inf'))

            report["summary"] = {
                "fastest_model": fastest_model,
                "speed_comparison": {},
                "quality_insights": {}
            }

            # 속도 비교
            fastest_time = results[fastest_model]["total_time"]
            for model_name, result in results.items():
                if result["success"]:
                    speed_ratio = result["total_time"] / fastest_time
                    report["summary"]["speed_comparison"][model_name] = {
                        "relative_speed": speed_ratio,
                        "speed_description": f"{speed_ratio:.1f}x slower" if speed_ratio > 1 else "fastest"
                    }

            # 품질 인사이트
            if all("quality" in results[k] for k in results.keys() if results[k]["success"]):
                quality_scores = {}
                for model_name, result in results.items():
                    if result["success"] and "quality" in result:
                        quality_scores[model_name] = result["quality"]["similarity_stats"]["mean"]

                best_quality_model = max(quality_scores.keys(), key=lambda x: quality_scores[x])
                report["summary"]["quality_insights"] = {
                    "best_quality_model": best_quality_model,
                    "quality_scores": quality_scores
                }

        return report

    def save_results(self, report: Dict[str, Any]) -> str:
        """결과를 파일로 저장합니다."""
        # 결과 디렉토리 생성
        output_dir = f"test_outputs/{self.test_timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        # JSON 리포트 저장
        json_file = f"{output_dir}/embedding_performance_comparison.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 요약 리포트 저장
        summary_file = f"{output_dir}/performance_summary.md"
        self.generate_markdown_report(report, summary_file)

        print(f"✅ 결과 저장 완료:")
        print(f"   📄 JSON 리포트: {json_file}")
        print(f"   📄 요약 리포트: {summary_file}")

        return output_dir

    def generate_markdown_report(self, report: Dict[str, Any], file_path: str):
        """마크다운 형식의 요약 리포트를 생성합니다."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# 임베딩 성능 비교 리포트\n\n")
            f.write(f"**테스트 시간**: {report['test_info']['timestamp']}\n")
            f.write(f"**총 청크 수**: {report['test_info']['total_chunks']}\n")
            f.write(f"**테스트 모델**: {', '.join(report['test_info']['models_tested'])}\n\n")

            # 성능 비교
            f.write("## 🚀 성능 비교\n\n")
            f.write("| 모델 | 총 시간(초) | 청크/초 | 차원 | 토큰 수 |\n")
            f.write("|------|-------------|---------|------|--------|\n")

            for model_name, perf in report["performance_comparison"].items():
                tokens = perf.get("total_tokens", "N/A")
                f.write(f"| {model_name} | {perf['total_time']:.2f} | {perf['chunks_per_second']:.2f} | {perf['embedding_dimension']} | {tokens} |\n")

            # 품질 비교
            f.write("\n## 📊 품질 비교\n\n")
            f.write("| 모델 | 평균 유사도 | 유사도 표준편차 | 클러스터링 점수 |\n")
            f.write("|------|-------------|----------------|----------------|\n")

            for model_name, quality in report["quality_comparison"].items():
                clustering = quality.get("clustering_score", "N/A")
                if clustering != "N/A" and clustering is not None:
                    clustering = f"{clustering:.4f}"
                f.write(f"| {model_name} | {quality['similarity_stats']['mean']:.4f} | {quality['similarity_stats']['std']:.4f} | {clustering} |\n")

            # 요약
            if "summary" in report and report["summary"]:
                f.write("\n## 📋 요약\n\n")
                f.write(f"**가장 빠른 모델**: {report['summary']['fastest_model']}\n\n")

                if "quality_insights" in report["summary"]:
                    f.write(f"**가장 높은 품질**: {report['summary']['quality_insights']['best_quality_model']}\n\n")

                f.write("### 속도 비교\n")
                for model_name, speed_info in report["summary"]["speed_comparison"].items():
                    f.write(f"- **{model_name}**: {speed_info['speed_description']}\n")

    def run_full_test(self, document_path: str) -> str:
        """전체 테스트를 실행합니다."""
        print("🧪 임베딩 성능 및 정확도 비교 테스트 시작")
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

        # 3. 모델 비교
        results = self.compare_models(chunks)
        if not results:
            print("❌ 모델 비교 실패")
            return ""

        # 4. 리포트 생성
        report = self.generate_performance_report(results, chunks)

        # 5. 결과 저장
        output_dir = self.save_results(report)

        # 6. 결과 출력
        self.print_summary(report)

        return output_dir

    def print_summary(self, report: Dict[str, Any]):
        """결과 요약을 출력합니다."""
        print(f"\n🎉 테스트 완료!")
        print("=" * 80)

        print(f"\n📊 성능 요약:")
        for model_name, perf in report["performance_comparison"].items():
            print(f"  {model_name}:")
            print(f"    - 총 시간: {perf['total_time']:.2f}초")
            print(f"    - 처리 속도: {perf['chunks_per_second']:.2f} 청크/초")
            print(f"    - 임베딩 차원: {perf['embedding_dimension']}")
            if "total_tokens" in perf:
                print(f"    - 총 토큰: {perf['total_tokens']}")

        print(f"\n📈 품질 요약:")
        for model_name, quality in report["quality_comparison"].items():
            print(f"  {model_name}:")
            print(f"    - 평균 유사도: {quality['similarity_stats']['mean']:.4f}")
            print(f"    - 유사도 표준편차: {quality['similarity_stats']['std']:.4f}")
            if quality.get("clustering_score"):
                print(f"    - 클러스터링 점수: {quality['clustering_score']:.4f}")

        if "summary" in report and report["summary"]:
            print(f"\n🏆 최종 결과:")
            print(f"  가장 빠른 모델: {report['summary']['fastest_model']}")
            if "quality_insights" in report["summary"]:
                print(f"  가장 높은 품질: {report['summary']['quality_insights']['best_quality_model']}")


def main():
    """메인 함수"""
    # 문서 경로
    document_path = "sample_docs/P02_01_01_001_20210101_marker.md"

    # 테스트 실행
    comparator = EmbeddingPerformanceComparator()
    output_dir = comparator.run_full_test(document_path)

    if output_dir:
        print(f"\n📁 결과 저장 위치: {output_dir}")
    else:
        print("\n❌ 테스트 실패")


if __name__ == "__main__":
    main()
