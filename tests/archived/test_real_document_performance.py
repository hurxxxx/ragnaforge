#!/usr/bin/env python3
"""Real document performance comparison between OpenAI and KURE v1."""

import time
import requests
import json
import os
import numpy as np
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
import random

# Load environment variables
load_dotenv()


class RealDocumentPerformanceTest:
    """Test performance with real enterprise documents."""
    
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

    def load_sample_document(self) -> str:
        """Load the sample enterprise document."""
        try:
            with open('sample_docs/기업 문서 검색 도구 분석.md', 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            print("❌ Sample document not found!")
            return None

    def chunk_document(self, text: str, strategy: str = "recursive", chunk_size: int = 380) -> List[str]:
        """Chunk document using KURE API."""
        try:
            payload = {
                "text": text,
                "strategy": strategy,
                "chunk_size": chunk_size,
                "overlap": 70,
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
                print(f"✅ Document chunked into {len(chunks)} pieces")
                return chunks
            else:
                print(f"❌ Chunking failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Chunking error: {e}")
            return []

    def get_openai_embeddings_batch(self, texts: List[str], model: str) -> Tuple[List[List[float]], float]:
        """Get embeddings from OpenAI API in batch."""
        start_time = time.time()
        embeddings = []
        
        try:
            # OpenAI API has limits, so we process in smaller batches
            batch_size = 100  # OpenAI limit
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = self.openai_client.embeddings.create(
                    input=batch,
                    model=model
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                
                # Small delay to respect rate limits
                time.sleep(0.1)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            return embeddings, elapsed_time
            
        except Exception as e:
            print(f"❌ OpenAI batch embedding error: {e}")
            return [], 0

    def get_kure_embeddings_batch(self, texts: List[str]) -> Tuple[List[List[float]], float]:
        """Get embeddings from KURE API in batch."""
        start_time = time.time()
        
        try:
            payload = {
                "input": texts,
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
                embeddings = [item['embedding'] for item in data['data']]
                return embeddings, elapsed_time
            else:
                print(f"❌ KURE batch embedding error: {response.status_code}")
                return [], 0
                
        except Exception as e:
            print(f"❌ KURE batch embedding error: {e}")
            return [], 0

    def calculate_similarity_matrix(self, embeddings: List[List[float]]) -> np.ndarray:
        """Calculate similarity matrix for embeddings."""
        if not embeddings:
            return np.array([])
        
        embeddings_array = np.array(embeddings)
        similarity_matrix = cosine_similarity(embeddings_array)
        return similarity_matrix

    def analyze_similarity_patterns(self, similarity_matrix: np.ndarray, chunks: List[str]) -> Dict[str, Any]:
        """Analyze similarity patterns in the document."""
        if similarity_matrix.size == 0:
            return {}
        
        # Remove diagonal (self-similarity)
        mask = ~np.eye(similarity_matrix.shape[0], dtype=bool)
        similarities = similarity_matrix[mask]
        
        # Find most similar pairs
        n = similarity_matrix.shape[0]
        similar_pairs = []
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = similarity_matrix[i, j]
                similar_pairs.append((i, j, similarity))
        
        # Sort by similarity
        similar_pairs.sort(key=lambda x: x[2], reverse=True)
        
        return {
            "avg_similarity": np.mean(similarities),
            "max_similarity": np.max(similarities),
            "min_similarity": np.min(similarities),
            "std_similarity": np.std(similarities),
            "top_similar_pairs": similar_pairs[:5],
            "total_comparisons": len(similarities)
        }

    def test_document_processing(self) -> Dict[str, Any]:
        """Test complete document processing pipeline."""
        print("\n🚀 Real Document Performance Test")
        print("=" * 80)
        
        # Load document
        document = self.load_sample_document()
        if not document:
            return {}
        
        print(f"📄 Document loaded: {len(document)} characters")
        
        # Chunk document
        chunks = self.chunk_document(document)
        if not chunks:
            return {}
        
        print(f"📋 Testing with {len(chunks)} chunks")
        
        # Limit chunks for testing (to avoid API costs and time)
        max_chunks = 20
        if len(chunks) > max_chunks:
            chunks = random.sample(chunks, max_chunks)
            print(f"📊 Randomly selected {max_chunks} chunks for testing")
        
        results = {}
        
        # Test OpenAI Small
        print(f"\n🔍 Testing OpenAI text-embedding-3-small...")
        openai_small_embeddings, openai_small_time = self.get_openai_embeddings_batch(
            chunks, "text-embedding-3-small"
        )
        
        if openai_small_embeddings:
            openai_small_similarity = self.analyze_similarity_patterns(
                self.calculate_similarity_matrix(openai_small_embeddings), chunks
            )
            results["openai_small"] = {
                "processing_time": openai_small_time,
                "similarity_analysis": openai_small_similarity,
                "chunks_processed": len(chunks)
            }
            print(f"✅ OpenAI Small: {openai_small_time:.2f}s, Avg similarity: {openai_small_similarity.get('avg_similarity', 0):.4f}")
        
        # Test OpenAI Large
        print(f"\n🔍 Testing OpenAI text-embedding-3-large...")
        openai_large_embeddings, openai_large_time = self.get_openai_embeddings_batch(
            chunks, "text-embedding-3-large"
        )
        
        if openai_large_embeddings:
            openai_large_similarity = self.analyze_similarity_patterns(
                self.calculate_similarity_matrix(openai_large_embeddings), chunks
            )
            results["openai_large"] = {
                "processing_time": openai_large_time,
                "similarity_analysis": openai_large_similarity,
                "chunks_processed": len(chunks)
            }
            print(f"✅ OpenAI Large: {openai_large_time:.2f}s, Avg similarity: {openai_large_similarity.get('avg_similarity', 0):.4f}")
        
        # Test KURE v1
        print(f"\n🔍 Testing KURE v1...")
        kure_embeddings, kure_time = self.get_kure_embeddings_batch(chunks)
        
        if kure_embeddings:
            kure_similarity = self.analyze_similarity_patterns(
                self.calculate_similarity_matrix(kure_embeddings), chunks
            )
            results["kure_v1"] = {
                "processing_time": kure_time,
                "similarity_analysis": kure_similarity,
                "chunks_processed": len(chunks)
            }
            print(f"✅ KURE v1: {kure_time:.2f}s, Avg similarity: {kure_similarity.get('avg_similarity', 0):.4f}")
        
        return results

    def print_detailed_analysis(self, results: Dict[str, Any]):
        """Print detailed performance analysis."""
        print("\n📊 Detailed Performance Analysis")
        print("=" * 80)
        
        if not results:
            print("❌ No results to analyze")
            return
        
        # Performance comparison table
        print("\n🏆 Performance Comparison:")
        print("-" * 80)
        print(f"{'Model':<15} {'Time (s)':<10} {'Avg Sim':<10} {'Max Sim':<10} {'Std Dev':<10}")
        print("-" * 80)
        
        for model_name, data in results.items():
            if 'similarity_analysis' in data:
                sim_data = data['similarity_analysis']
                print(f"{model_name:<15} {data['processing_time']:<10.2f} "
                      f"{sim_data.get('avg_similarity', 0):<10.4f} "
                      f"{sim_data.get('max_similarity', 0):<10.4f} "
                      f"{sim_data.get('std_similarity', 0):<10.4f}")
        
        # Speed comparison
        print(f"\n⚡ Speed Analysis:")
        times = {name: data['processing_time'] for name, data in results.items() if 'processing_time' in data}
        if times:
            fastest = min(times.values())
            print(f"   Fastest: {fastest:.2f}s")
            for name, time_val in times.items():
                speedup = time_val / fastest
                print(f"   {name}: {time_val:.2f}s ({speedup:.1f}x slower than fastest)")
        
        # Similarity quality analysis
        print(f"\n🎯 Similarity Quality Analysis:")
        for model_name, data in results.items():
            if 'similarity_analysis' in data:
                sim_data = data['similarity_analysis']
                print(f"\n   {model_name.upper()}:")
                print(f"     Average similarity: {sim_data.get('avg_similarity', 0):.4f}")
                print(f"     Similarity range: {sim_data.get('min_similarity', 0):.4f} - {sim_data.get('max_similarity', 0):.4f}")
                print(f"     Standard deviation: {sim_data.get('std_similarity', 0):.4f}")
                print(f"     Total comparisons: {sim_data.get('total_comparisons', 0)}")


def main():
    """Main test function."""
    try:
        tester = RealDocumentPerformanceTest()
        results = tester.test_document_processing()
        tester.print_detailed_analysis(results)
        
        print("\n🎉 Real Document Performance Test Completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    main()
