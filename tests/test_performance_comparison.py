#!/usr/bin/env python3
"""Performance comparison between OpenAI and KURE v1 embedding models."""

import time
import requests
import json
import os
import numpy as np
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables
load_dotenv()


class PerformanceComparator:
    """Compare performance between OpenAI and KURE v1 models."""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.kure_api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
        self.kure_base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # KURE API headers
        self.kure_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.kure_api_key}"
        }
        
        print(f"🔑 OpenAI API Key: {self.openai_api_key[:20]}...")
        print(f"🔑 KURE API Key: {self.kure_api_key[:20]}...")
        print(f"🌐 KURE Base URL: {self.kure_base_url}")

    def get_openai_embedding(self, text: str, model: str) -> tuple[List[float], float]:
        """Get embedding from OpenAI API and measure time."""
        start_time = time.time()
        
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=model
            )
            end_time = time.time()
            
            embedding = response.data[0].embedding
            elapsed_time = end_time - start_time
            
            return embedding, elapsed_time
            
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return None, 0

    def get_kure_embedding(self, text: str) -> tuple[List[float], float]:
        """Get embedding from KURE API and measure time."""
        start_time = time.time()
        
        try:
            payload = {
                "input": [text],
                "model": "nlpai-lab/KURE-v1"
            }
            
            response = requests.post(
                f"{self.kure_base_url}/embeddings",
                json=payload,
                headers=self.kure_headers
            )
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                embedding = data['data'][0]['embedding']
                return embedding, elapsed_time
            else:
                print(f"❌ KURE API error: {response.status_code} - {response.text}")
                return None, 0
                
        except Exception as e:
            print(f"❌ KURE API error: {e}")
            return None, 0

    def calculate_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        if emb1 is None or emb2 is None:
            return 0.0
        
        emb1_array = np.array(emb1).reshape(1, -1)
        emb2_array = np.array(emb2).reshape(1, -1)
        
        similarity = cosine_similarity(emb1_array, emb2_array)[0][0]
        return float(similarity)

    def test_similarity_pairs(self, test_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test similarity for given text pairs."""
        results = {
            "openai_small": {"similarities": [], "times": []},
            "openai_large": {"similarities": [], "times": []},
            "kure_v1": {"similarities": [], "times": []}
        }
        
        print("\n🧪 Testing Similarity Pairs...")
        print("=" * 80)
        
        for i, pair in enumerate(test_pairs):
            text1, text2 = pair["text1"], pair["text2"]
            description = pair["description"]
            
            print(f"\n📋 Test {i+1}: {description}")
            print(f"   Text 1: {text1[:50]}...")
            print(f"   Text 2: {text2[:50]}...")
            
            # OpenAI text-embedding-3-small
            print("   🔍 OpenAI Small...", end=" ")
            emb1_small, time1_small = self.get_openai_embedding(text1, "text-embedding-3-small")
            emb2_small, time2_small = self.get_openai_embedding(text2, "text-embedding-3-small")
            
            if emb1_small and emb2_small:
                similarity_small = self.calculate_similarity(emb1_small, emb2_small)
                total_time_small = time1_small + time2_small
                results["openai_small"]["similarities"].append(similarity_small)
                results["openai_small"]["times"].append(total_time_small)
                print(f"✅ Similarity: {similarity_small:.4f}, Time: {total_time_small:.2f}s")
            else:
                print("❌ Failed")
            
            # OpenAI text-embedding-3-large
            print("   🔍 OpenAI Large...", end=" ")
            emb1_large, time1_large = self.get_openai_embedding(text1, "text-embedding-3-large")
            emb2_large, time2_large = self.get_openai_embedding(text2, "text-embedding-3-large")
            
            if emb1_large and emb2_large:
                similarity_large = self.calculate_similarity(emb1_large, emb2_large)
                total_time_large = time1_large + time2_large
                results["openai_large"]["similarities"].append(similarity_large)
                results["openai_large"]["times"].append(total_time_large)
                print(f"✅ Similarity: {similarity_large:.4f}, Time: {total_time_large:.2f}s")
            else:
                print("❌ Failed")
            
            # KURE v1
            print("   🔍 KURE v1...", end=" ")
            emb1_kure, time1_kure = self.get_kure_embedding(text1)
            emb2_kure, time2_kure = self.get_kure_embedding(text2)
            
            if emb1_kure and emb2_kure:
                similarity_kure = self.calculate_similarity(emb1_kure, emb2_kure)
                total_time_kure = time1_kure + time2_kure
                results["kure_v1"]["similarities"].append(similarity_kure)
                results["kure_v1"]["times"].append(total_time_kure)
                print(f"✅ Similarity: {similarity_kure:.4f}, Time: {total_time_kure:.2f}s")
            else:
                print("❌ Failed")
        
        return results

    def print_summary(self, results: Dict[str, Any]):
        """Print performance summary."""
        print("\n📊 Performance Summary")
        print("=" * 80)
        
        for model_name, data in results.items():
            if data["similarities"] and data["times"]:
                avg_similarity = np.mean(data["similarities"])
                avg_time = np.mean(data["times"])
                min_time = np.min(data["times"])
                max_time = np.max(data["times"])
                
                print(f"\n🤖 {model_name.upper()}:")
                print(f"   Average Similarity: {avg_similarity:.4f}")
                print(f"   Average Time: {avg_time:.2f}s")
                print(f"   Min Time: {min_time:.2f}s")
                print(f"   Max Time: {max_time:.2f}s")
                print(f"   Total Tests: {len(data['similarities'])}")
            else:
                print(f"\n🤖 {model_name.upper()}: No successful tests")


def main():
    """Main performance comparison test."""
    print("🚀 OpenAI vs KURE v1 Performance Comparison")
    print("=" * 80)
    
    try:
        comparator = PerformanceComparator()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Test pairs for similarity comparison
    test_pairs = [
        {
            "description": "한국어 유사 문장",
            "text1": "안녕하세요, 오늘 날씨가 정말 좋네요.",
            "text2": "안녕하세요, 오늘 날씨가 매우 좋습니다."
        },
        {
            "description": "한국어 다른 주제",
            "text1": "인공지능 기술이 빠르게 발전하고 있습니다.",
            "text2": "오늘 점심으로 김치찌개를 먹었습니다."
        },
        {
            "description": "영어 유사 문장",
            "text1": "The weather is beautiful today.",
            "text2": "Today's weather is really nice."
        },
        {
            "description": "영어 다른 주제",
            "text1": "Artificial intelligence is advancing rapidly.",
            "text2": "I had kimchi stew for lunch today."
        },
        {
            "description": "한영 번역 쌍",
            "text1": "인공지능 기술이 빠르게 발전하고 있습니다.",
            "text2": "Artificial intelligence technology is advancing rapidly."
        },
        {
            "description": "기업 문서 유사",
            "text1": "회사의 매출이 전년 대비 15% 증가했습니다.",
            "text2": "기업의 수익이 작년에 비해 15% 상승했습니다."
        },
        {
            "description": "기술 문서 유사",
            "text1": "이 API는 RESTful 아키텍처를 따릅니다.",
            "text2": "해당 API는 REST 아키텍처 기반으로 설계되었습니다."
        }
    ]
    
    # Run similarity tests
    results = comparator.test_similarity_pairs(test_pairs)
    
    # Print summary
    comparator.print_summary(results)
    
    print("\n🎉 Performance Comparison Completed!")


if __name__ == "__main__":
    main()
