#!/usr/bin/env python3
"""Direct comparison between OpenAI and KURE v1 for real document processing."""

import time
import requests
import json
import os
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables
load_dotenv()


class OpenAIvsKUREComparison:
    """Compare OpenAI and KURE v1 for real document processing."""
    
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

    def load_and_prepare_document(self) -> Tuple[str, List[str]]:
        """Load sample document and chunk it."""
        try:
            with open('sample_docs/기업 문서 검색 도구 분석.md', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simulate 50-page document (32,500 chars)
            target_length = 32500
            if len(content) > target_length:
                ratio = target_length / len(content)
                content = content[:int(len(content) * ratio)]
            
            print(f"📄 Document prepared: {len(content)} characters")
            
            # Chunk the document
            chunks = self.chunk_document(content)
            print(f"📋 Document chunked: {len(chunks)} chunks")
            
            return content, chunks
            
        except FileNotFoundError:
            print("❌ Sample document not found!")
            return None, []

    def chunk_document(self, text: str) -> List[str]:
        """Chunk document using KURE API."""
        try:
            payload = {
                "text": text,
                "strategy": "recursive",
                "chunk_size": 380,
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
                return [chunk['text'] for chunk in data['data']]
            else:
                print(f"❌ Chunking failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Chunking error: {e}")
            return []

    def test_openai_embedding(self, chunks: List[str], model: str) -> Dict:
        """Test OpenAI embedding performance."""
        print(f"\n🔍 Testing OpenAI {model}...")
        
        start_time = time.time()
        embeddings = []
        total_tokens = 0
        
        try:
            # OpenAI batch processing (max 2048 inputs per request)
            batch_size = 100  # Conservative batch size for API limits
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_start = time.time()
                
                response = self.openai_client.embeddings.create(
                    input=batch,
                    model=model
                )
                
                batch_end = time.time()
                batch_time = batch_end - batch_start
                
                batch_embeddings = [data.embedding for data in response.data]
                embeddings.extend(batch_embeddings)
                total_tokens += response.usage.total_tokens
                
                print(f"   Batch {i//batch_size + 1}: {len(batch)} chunks in {batch_time:.2f}s")
                
                # Respect rate limits
                time.sleep(0.1)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            return {
                "model": model,
                "total_time": total_time,
                "chunks_processed": len(chunks),
                "embeddings_generated": len(embeddings),
                "tokens_used": total_tokens,
                "chunks_per_second": len(chunks) / total_time,
                "embeddings": embeddings,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ OpenAI {model} error: {e}")
            return {
                "model": model,
                "success": False,
                "error": str(e)
            }

    def test_kure_embedding(self, chunks: List[str]) -> Dict:
        """Test KURE v1 embedding performance."""
        print(f"\n🔍 Testing KURE v1...")
        
        start_time = time.time()
        embeddings = []
        
        try:
            batch_size = 16  # Optimized batch size
            
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
                
                if response.status_code == 200:
                    data = response.json()
                    batch_embeddings = [item['embedding'] for item in data['data']]
                    embeddings.extend(batch_embeddings)
                    
                    print(f"   Batch {i//batch_size + 1}: {len(batch)} chunks in {batch_time:.2f}s")
                else:
                    print(f"❌ KURE batch failed: {response.status_code}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
            
            end_time = time.time()
            total_time = end_time - start_time
            
            return {
                "model": "KURE-v1",
                "total_time": total_time,
                "chunks_processed": len(chunks),
                "embeddings_generated": len(embeddings),
                "tokens_used": 0,  # No token counting for KURE
                "chunks_per_second": len(chunks) / total_time,
                "embeddings": embeddings,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ KURE v1 error: {e}")
            return {
                "model": "KURE-v1",
                "success": False,
                "error": str(e)
            }

    def analyze_embedding_quality(self, embeddings: List[List[float]], model_name: str) -> Dict:
        """Analyze embedding quality through similarity patterns."""
        if not embeddings or len(embeddings) < 2:
            return {}
        
        # Calculate similarity matrix
        embeddings_array = np.array(embeddings)
        similarity_matrix = cosine_similarity(embeddings_array)
        
        # Remove diagonal (self-similarity)
        mask = ~np.eye(similarity_matrix.shape[0], dtype=bool)
        similarities = similarity_matrix[mask]
        
        return {
            "avg_similarity": float(np.mean(similarities)),
            "max_similarity": float(np.max(similarities)),
            "min_similarity": float(np.min(similarities)),
            "std_similarity": float(np.std(similarities)),
            "similarity_distribution": {
                "q25": float(np.percentile(similarities, 25)),
                "q50": float(np.percentile(similarities, 50)),
                "q75": float(np.percentile(similarities, 75))
            }
        }

    def run_comprehensive_comparison(self):
        """Run comprehensive comparison between all models."""
        print("🚀 OpenAI vs KURE v1 Real Document Comparison")
        print("=" * 80)
        
        # Prepare document
        document, chunks = self.load_and_prepare_document()
        if not chunks:
            print("❌ Failed to prepare document")
            return
        
        # Limit chunks for cost control (testing with subset)
        max_chunks = 50  # Reasonable for testing
        if len(chunks) > max_chunks:
            chunks = chunks[:max_chunks]
            print(f"📊 Testing with first {max_chunks} chunks (cost control)")
        
        results = {}
        
        # Test OpenAI Small
        result_small = self.test_openai_embedding(chunks, "text-embedding-3-small")
        if result_small["success"]:
            result_small["quality"] = self.analyze_embedding_quality(
                result_small["embeddings"], "OpenAI Small"
            )
            results["openai_small"] = result_small
        
        # Test OpenAI Large
        result_large = self.test_openai_embedding(chunks, "text-embedding-3-large")
        if result_large["success"]:
            result_large["quality"] = self.analyze_embedding_quality(
                result_large["embeddings"], "OpenAI Large"
            )
            results["openai_large"] = result_large
        
        # Test KURE v1
        result_kure = self.test_kure_embedding(chunks)
        if result_kure["success"]:
            result_kure["quality"] = self.analyze_embedding_quality(
                result_kure["embeddings"], "KURE v1"
            )
            results["kure_v1"] = result_kure
        
        # Print comprehensive analysis
        self.print_comprehensive_analysis(results, len(chunks))

    def print_comprehensive_analysis(self, results: Dict, chunks_count: int):
        """Print detailed comparison analysis."""
        print(f"\n📊 Comprehensive Performance Analysis ({chunks_count} chunks)")
        print("=" * 80)
        
        if not results:
            print("❌ No successful results to analyze")
            return
        
        # Performance comparison table
        print(f"\n🏆 Performance Comparison:")
        print("-" * 90)
        print(f"{'Model':<15} {'Time (s)':<10} {'Speed':<12} {'Tokens':<10} {'Avg Sim':<10} {'Quality':<10}")
        print("-" * 90)
        
        for model_key, data in results.items():
            model_name = data["model"]
            time_val = data["total_time"]
            speed = data["chunks_per_second"]
            tokens = data.get("tokens_used", 0)
            avg_sim = data.get("quality", {}).get("avg_similarity", 0)
            
            # Quality score (higher similarity = better for document coherence)
            quality_score = "High" if avg_sim > 0.3 else "Medium" if avg_sim > 0.2 else "Low"
            
            print(f"{model_name:<15} {time_val:<10.2f} {speed:<12.1f} {tokens:<10} {avg_sim:<10.4f} {quality_score:<10}")
        
        # Speed ranking
        print(f"\n⚡ Speed Ranking:")
        speed_ranking = sorted(results.items(), key=lambda x: x[1]["chunks_per_second"], reverse=True)
        for i, (model_key, data) in enumerate(speed_ranking, 1):
            print(f"   {i}. {data['model']}: {data['chunks_per_second']:.1f} chunks/second")
        
        # Quality ranking
        print(f"\n🎯 Quality Ranking (Similarity Coherence):")
        quality_ranking = sorted(
            [(k, v) for k, v in results.items() if "quality" in v],
            key=lambda x: x[1]["quality"]["avg_similarity"], reverse=True
        )
        for i, (model_key, data) in enumerate(quality_ranking, 1):
            avg_sim = data["quality"]["avg_similarity"]
            print(f"   {i}. {data['model']}: {avg_sim:.4f} average similarity")
        
        # Cost analysis
        print(f"\n💰 Cost Analysis (for {chunks_count} chunks):")
        for model_key, data in results.items():
            model_name = data["model"]
            if "openai" in model_key:
                tokens = data.get("tokens_used", 0)
                if "small" in model_key:
                    cost = tokens * 0.00002 / 1000  # $0.02 per 1M tokens
                else:  # large
                    cost = tokens * 0.00013 / 1000  # $0.13 per 1M tokens
                print(f"   {model_name}: ${cost:.4f} ({tokens:,} tokens)")
            else:
                print(f"   {model_name}: $0.0000 (local processing)")
        
        # Extrapolation to full document
        print(f"\n📈 Extrapolation to Full 50-Page Document:")
        full_doc_chunks = int(chunks_count * (32500 / (chunks_count * 164)))  # Estimate full doc chunks
        
        for model_key, data in results.items():
            model_name = data["model"]
            time_per_chunk = data["total_time"] / chunks_count
            estimated_time = time_per_chunk * full_doc_chunks
            
            print(f"   {model_name}: ~{estimated_time:.1f}s ({estimated_time/60:.1f} minutes)")


def main():
    """Main comparison function."""
    try:
        comparator = OpenAIvsKUREComparison()
        comparator.run_comprehensive_comparison()
        
        print("\n🎉 Comprehensive Comparison Completed!")
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")


if __name__ == "__main__":
    main()
