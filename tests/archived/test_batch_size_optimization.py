#!/usr/bin/env python3
"""Test optimal batch size for KURE v1 embeddings."""

import time
import requests
import json
import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BatchSizeOptimizer:
    """Test different batch sizes for optimal performance."""
    
    def __init__(self):
        self.kure_api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
        self.kure_base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        self.kure_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.kure_api_key}"
        }
        
        print(f"🔑 KURE API Key: {self.kure_api_key[:20]}...")
        print(f"🌐 KURE Base URL: {self.kure_base_url}")

    def generate_test_texts(self, count: int) -> List[str]:
        """Generate test texts for batch processing."""
        base_texts = [
            "인공지능 기술이 빠르게 발전하고 있습니다.",
            "기업의 디지털 전환이 가속화되고 있습니다.",
            "클라우드 컴퓨팅이 비즈니스 혁신을 이끌고 있습니다.",
            "데이터 분석을 통한 인사이트 도출이 중요합니다.",
            "자동화 기술이 업무 효율성을 크게 향상시킵니다.",
            "사이버 보안의 중요성이 날로 증가하고 있습니다.",
            "원격 근무 환경에서의 협업 도구가 필수가 되었습니다.",
            "고객 경험 개선을 위한 개인화 서비스가 확산됩니다.",
            "지속 가능한 경영이 기업의 핵심 과제입니다.",
            "블록체인 기술이 다양한 산업에 적용되고 있습니다."
        ]
        
        # Repeat and modify texts to reach desired count
        texts = []
        for i in range(count):
            base_text = base_texts[i % len(base_texts)]
            # Add variation to make each text unique
            modified_text = f"{base_text} (변형 {i+1})"
            texts.append(modified_text)
        
        return texts

    def test_batch_size(self, texts: List[str], batch_size: int) -> Dict:
        """Test embedding generation with specific batch size."""
        try:
            # Split texts into batches
            batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
            
            total_time = 0
            total_embeddings = 0
            
            for batch in batches:
                start_time = time.time()
                
                payload = {
                    "input": batch,
                    "model": "nlpai-lab/KURE-v1"
                }
                
                response = requests.post(
                    f"{self.kure_base_url}/embeddings",
                    json=payload,
                    headers=self.kure_headers
                )
                
                end_time = time.time()
                batch_time = end_time - start_time
                total_time += batch_time
                
                if response.status_code == 200:
                    data = response.json()
                    total_embeddings += len(data['data'])
                else:
                    print(f"❌ Batch failed: {response.status_code}")
                    return None
            
            return {
                "batch_size": batch_size,
                "total_texts": len(texts),
                "total_batches": len(batches),
                "total_time": total_time,
                "avg_time_per_batch": total_time / len(batches),
                "texts_per_second": len(texts) / total_time,
                "embeddings_generated": total_embeddings
            }
            
        except Exception as e:
            print(f"❌ Error testing batch size {batch_size}: {e}")
            return None

    def run_optimization_test(self):
        """Run comprehensive batch size optimization test."""
        print("\n🚀 Batch Size Optimization Test")
        print("=" * 80)
        
        # Test parameters
        total_texts = 100  # Total number of texts to process
        batch_sizes = [1, 4, 8, 16, 32, 64]  # Different batch sizes to test
        
        print(f"📊 Testing with {total_texts} texts")
        print(f"🔧 Batch sizes to test: {batch_sizes}")
        
        # Generate test texts
        test_texts = self.generate_test_texts(total_texts)
        print(f"✅ Generated {len(test_texts)} test texts")
        
        results = []
        
        for batch_size in batch_sizes:
            print(f"\n🔍 Testing batch size: {batch_size}")
            
            result = self.test_batch_size(test_texts, batch_size)
            
            if result:
                results.append(result)
                print(f"   ✅ Time: {result['total_time']:.2f}s, "
                      f"Speed: {result['texts_per_second']:.1f} texts/s, "
                      f"Batches: {result['total_batches']}")
            else:
                print(f"   ❌ Failed")
        
        return results

    def analyze_results(self, results: List[Dict]):
        """Analyze and recommend optimal batch size."""
        print("\n📊 Batch Size Analysis")
        print("=" * 80)
        
        if not results:
            print("❌ No results to analyze")
            return
        
        # Performance table
        print(f"\n🏆 Performance Comparison:")
        print("-" * 80)
        print(f"{'Batch Size':<12} {'Total Time':<12} {'Texts/Sec':<12} {'Batches':<10} {'Avg/Batch':<12}")
        print("-" * 80)
        
        for result in results:
            print(f"{result['batch_size']:<12} "
                  f"{result['total_time']:<12.2f} "
                  f"{result['texts_per_second']:<12.1f} "
                  f"{result['total_batches']:<10} "
                  f"{result['avg_time_per_batch']:<12.2f}")
        
        # Find optimal batch size
        fastest_result = max(results, key=lambda x: x['texts_per_second'])
        most_efficient = min(results, key=lambda x: x['total_time'])
        
        print(f"\n🎯 Optimization Results:")
        print(f"   Fastest processing: Batch size {fastest_result['batch_size']} "
              f"({fastest_result['texts_per_second']:.1f} texts/sec)")
        print(f"   Most efficient: Batch size {most_efficient['batch_size']} "
              f"({most_efficient['total_time']:.2f}s total)")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        
        # Find sweet spot (good balance of speed and efficiency)
        efficiency_scores = []
        for result in results:
            # Score based on texts per second and reasonable batch count
            score = result['texts_per_second'] * (1 - (result['total_batches'] - 1) * 0.01)
            efficiency_scores.append((result['batch_size'], score))
        
        best_balance = max(efficiency_scores, key=lambda x: x[1])
        
        print(f"   🥇 Recommended batch size: {best_balance[0]} (best balance)")
        print(f"   ⚡ For maximum speed: {fastest_result['batch_size']}")
        print(f"   🔧 For minimum latency: 1-4 (real-time scenarios)")
        print(f"   📊 For batch processing: {fastest_result['batch_size']}-64")
        
        # Memory considerations
        print(f"\n🧠 Memory Considerations:")
        print(f"   Current setting (32): Good balance for most scenarios")
        print(f"   Higher batch sizes: Better throughput, more memory usage")
        print(f"   Lower batch sizes: Lower memory, higher latency")


def main():
    """Main optimization test."""
    try:
        optimizer = BatchSizeOptimizer()
        results = optimizer.run_optimization_test()
        optimizer.analyze_results(results)
        
        print("\n🎉 Batch Size Optimization Test Completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    main()
