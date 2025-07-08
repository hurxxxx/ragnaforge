"""
모델 성능 비교 테스트: 새로운 Arctic 모델과 기존 모델들 비교
"""

import time
import requests
import json
from typing import List, Dict

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_KEY = "sk-kure-v1-test-key-12345"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

class ModelComparisonTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.test_texts = [
            "안녕하세요",
            "한국어 자연어 처리",
            "인공지능과 머신러닝",
            "문서 검색 시스템",
            "벡터 임베딩 기술",
            "RAG 시스템 구현",
            "MCP 프로토콜 지원",
            "하이브리드 검색 엔진"
        ]
        self.models = [
            "dragonkue/snowflake-arctic-embed-l-v2.0-ko",
            "nlpai-lab/KURE-v1",
            "nlpai-lab/KoE5"
        ]
        
    def test_embedding_performance(self, model: str, texts: List[str]) -> Dict:
        """특정 모델의 임베딩 성능 테스트"""
        start_time = time.time()
        
        try:
            payload = {
                "input": texts,
                "model": model
            }
            
            response = requests.post(f"{self.base_url}/embeddings", 
                                   headers=self.headers, json=payload)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                embeddings = data.get("data", [])
                
                if embeddings:
                    embedding_dim = len(embeddings[0]["embedding"])
                    throughput = len(texts) / duration
                    
                    return {
                        "success": True,
                        "model": model,
                        "duration": duration,
                        "throughput": throughput,
                        "embedding_dim": embedding_dim,
                        "num_texts": len(texts),
                        "avg_time_per_text": duration / len(texts)
                    }
                else:
                    return {"success": False, "error": "No embeddings returned"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            duration = time.time() - start_time
            return {"success": False, "error": str(e), "duration": duration}
    
    def test_embedding_quality(self, model: str) -> Dict:
        """임베딩 품질 테스트 (유사도 계산)"""
        try:
            # 유사한 의미의 텍스트 쌍
            similar_pairs = [
                ("안녕하세요", "안녕"),
                ("인공지능", "AI"),
                ("머신러닝", "기계학습"),
                ("문서 검색", "문서 찾기")
            ]
            
            # 다른 의미의 텍스트 쌍
            different_pairs = [
                ("안녕하세요", "컴퓨터"),
                ("인공지능", "음식"),
                ("검색", "운동"),
                ("기술", "날씨")
            ]
            
            similar_scores = []
            different_scores = []
            
            # 유사한 쌍들의 유사도 계산
            for text1, text2 in similar_pairs:
                payload = {
                    "text1": text1,
                    "text2": text2,
                    "model": model
                }
                
                response = requests.post(f"{self.base_url}/similarity", 
                                       headers=self.headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    similar_scores.append(data.get("similarity", 0))
            
            # 다른 쌍들의 유사도 계산
            for text1, text2 in different_pairs:
                payload = {
                    "text1": text1,
                    "text2": text2,
                    "model": model
                }
                
                response = requests.post(f"{self.base_url}/similarity", 
                                       headers=self.headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    different_scores.append(data.get("similarity", 0))
            
            if similar_scores and different_scores:
                avg_similar = sum(similar_scores) / len(similar_scores)
                avg_different = sum(different_scores) / len(different_scores)
                discrimination = avg_similar - avg_different
                
                return {
                    "success": True,
                    "model": model,
                    "avg_similar_score": avg_similar,
                    "avg_different_score": avg_different,
                    "discrimination": discrimination,
                    "similar_scores": similar_scores,
                    "different_scores": different_scores
                }
            else:
                return {"success": False, "error": "Failed to calculate similarities"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_comparison(self):
        """모든 모델 비교 실행"""
        print("🔍 모델 성능 비교 테스트 시작")
        print("=" * 70)
        
        performance_results = []
        quality_results = []
        
        for model in self.models:
            print(f"\n📊 {model} 테스트 중...")
            
            # 성능 테스트
            perf_result = self.test_embedding_performance(model, self.test_texts)
            performance_results.append(perf_result)
            
            if perf_result["success"]:
                print(f"  ⏱️  처리 시간: {perf_result['duration']:.3f}초")
                print(f"  🚀 처리량: {perf_result['throughput']:.2f} texts/sec")
                print(f"  📏 임베딩 차원: {perf_result['embedding_dim']}")
                print(f"  ⚡ 텍스트당 평균 시간: {perf_result['avg_time_per_text']:.3f}초")
            else:
                print(f"  ❌ 성능 테스트 실패: {perf_result.get('error')}")
            
            # 품질 테스트
            quality_result = self.test_embedding_quality(model)
            quality_results.append(quality_result)
            
            if quality_result["success"]:
                print(f"  🎯 유사 텍스트 평균 점수: {quality_result['avg_similar_score']:.3f}")
                print(f"  🎯 다른 텍스트 평균 점수: {quality_result['avg_different_score']:.3f}")
                print(f"  📈 판별력: {quality_result['discrimination']:.3f}")
            else:
                print(f"  ❌ 품질 테스트 실패: {quality_result.get('error')}")
        
        # 결과 요약
        print("\n" + "=" * 70)
        print("📊 성능 비교 요약")
        print("=" * 70)
        
        successful_perf = [r for r in performance_results if r["success"]]
        if successful_perf:
            print("\n🚀 처리 성능 순위:")
            sorted_perf = sorted(successful_perf, key=lambda x: x["throughput"], reverse=True)
            for i, result in enumerate(sorted_perf, 1):
                print(f"  {i}. {result['model']}")
                print(f"     처리량: {result['throughput']:.2f} texts/sec")
                print(f"     처리 시간: {result['duration']:.3f}초")
        
        successful_quality = [r for r in quality_results if r["success"]]
        if successful_quality:
            print("\n🎯 임베딩 품질 순위:")
            sorted_quality = sorted(successful_quality, key=lambda x: x["discrimination"], reverse=True)
            for i, result in enumerate(sorted_quality, 1):
                print(f"  {i}. {result['model']}")
                print(f"     판별력: {result['discrimination']:.3f}")
                print(f"     유사 텍스트 점수: {result['avg_similar_score']:.3f}")
                print(f"     다른 텍스트 점수: {result['avg_different_score']:.3f}")
        
        # 추천 모델
        if successful_perf and successful_quality:
            best_perf_model = sorted_perf[0]["model"]
            best_quality_model = sorted_quality[0]["model"]
            
            print(f"\n🏆 최고 성능 모델: {best_perf_model}")
            print(f"🎯 최고 품질 모델: {best_quality_model}")
            
            if best_perf_model == best_quality_model:
                print(f"🌟 종합 추천 모델: {best_perf_model}")
            else:
                print("⚖️  성능과 품질 간 트레이드오프가 있습니다.")
        
        print("\n✅ 모델 비교 테스트 완료!")
        return performance_results, quality_results

if __name__ == "__main__":
    tester = ModelComparisonTest()
    tester.run_comparison()
