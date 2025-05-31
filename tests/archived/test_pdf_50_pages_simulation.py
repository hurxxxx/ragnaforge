#!/usr/bin/env python3
"""Simulate PDF 50 pages document embedding performance."""

import time
import requests
import json
import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PDF50PagesSimulator:
    """Simulate processing of 50-page PDF document."""
    
    def __init__(self):
        self.kure_api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
        self.kure_base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        self.kure_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.kure_api_key}"
        }

    def load_sample_document(self) -> str:
        """Load the sample document."""
        try:
            with open('sample_docs/기업 문서 검색 도구 분석.md', 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            print("❌ Sample document not found!")
            return None

    def simulate_50_page_document(self, base_content: str) -> str:
        """Create a document similar to 50 PDF pages."""
        # Current sample: 49,270 chars
        # Target: ~32,500 chars (typical 50 pages)
        
        # Take about 66% of the sample document
        target_length = 32500
        current_length = len(base_content)
        
        if current_length > target_length:
            # Truncate to simulate 50 pages
            ratio = target_length / current_length
            cut_point = int(len(base_content) * ratio)
            simulated_doc = base_content[:cut_point]
        else:
            # Use full document (it's smaller than 50 pages)
            simulated_doc = base_content
        
        return simulated_doc

    def chunk_document_optimized(self, text: str) -> List[str]:
        """Chunk document with optimized settings."""
        try:
            payload = {
                "text": text,
                "strategy": "recursive",
                "chunk_size": 380,
                "overlap": 70,
                "language": "ko"
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.kure_base_url}/v1/chunk",
                json=payload,
                headers=self.kure_headers
            )
            end_time = time.time()
            
            chunking_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                chunks = [chunk['text'] for chunk in data['data']]
                print(f"✅ Chunking: {len(chunks)} chunks in {chunking_time:.2f}s")
                return chunks, chunking_time
            else:
                print(f"❌ Chunking failed: {response.status_code}")
                return [], 0
                
        except Exception as e:
            print(f"❌ Chunking error: {e}")
            return [], 0

    def embed_chunks_optimized(self, chunks: List[str]) -> float:
        """Embed chunks with optimized batch size 16."""
        try:
            batch_size = 16  # Optimized batch size
            total_time = 0
            total_embeddings = 0
            
            # Process in batches of 16
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
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
                    print(f"   Batch {i//batch_size + 1}: {len(batch)} chunks in {batch_time:.2f}s")
                else:
                    print(f"❌ Embedding batch failed: {response.status_code}")
                    return 0
            
            print(f"✅ Embedding: {total_embeddings} embeddings in {total_time:.2f}s")
            return total_time
            
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            return 0

    def run_simulation(self):
        """Run complete 50-page PDF simulation."""
        print("🚀 PDF 50 Pages Embedding Simulation")
        print("=" * 80)
        
        # Load base document
        base_document = self.load_sample_document()
        if not base_document:
            return
        
        print(f"📄 Base document: {len(base_document)} characters")
        
        # Simulate 50-page document
        simulated_doc = self.simulate_50_page_document(base_document)
        print(f"📋 Simulated 50-page doc: {len(simulated_doc)} characters")
        
        # Start total timing
        total_start_time = time.time()
        
        # Step 1: Chunking
        print(f"\n🔧 Step 1: Document Chunking")
        chunks, chunking_time = self.chunk_document_optimized(simulated_doc)
        
        if not chunks:
            print("❌ Chunking failed, cannot continue")
            return
        
        # Step 2: Embedding
        print(f"\n🧠 Step 2: Embedding Generation (Batch Size 16)")
        embedding_time = self.embed_chunks_optimized(chunks)
        
        if embedding_time == 0:
            print("❌ Embedding failed")
            return
        
        # Calculate total time
        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        
        # Results
        print(f"\n📊 Performance Results")
        print("=" * 80)
        print(f"📄 Document size: {len(simulated_doc):,} characters")
        print(f"📋 Total chunks: {len(chunks)}")
        print(f"🔧 Chunking time: {chunking_time:.2f}s")
        print(f"🧠 Embedding time: {embedding_time:.2f}s")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"⚡ Processing speed: {len(chunks)/total_time:.1f} chunks/second")
        
        # Extrapolation to different document sizes
        print(f"\n📈 Extrapolation to Different Document Sizes")
        print("-" * 80)
        
        chars_per_second = len(simulated_doc) / total_time
        chunks_per_second = len(chunks) / total_time
        
        document_sizes = [
            ("10 pages", 6500, "Small report"),
            ("25 pages", 16250, "Medium document"),
            ("50 pages", 32500, "Large document"),
            ("100 pages", 65000, "Very large document"),
            ("200 pages", 130000, "Book-sized document")
        ]
        
        for name, chars, description in document_sizes:
            estimated_time = chars / chars_per_second
            estimated_chunks = chars / (len(simulated_doc) / len(chunks))
            
            print(f"{name:<12} ({description:<20}): {estimated_time:.1f}s, ~{estimated_chunks:.0f} chunks")
        
        # Cost comparison
        print(f"\n💰 Cost Comparison (50-page document)")
        print("-" * 80)
        print(f"KURE v1:      FREE (local processing)")
        print(f"OpenAI Small: ~$0.02 (API cost)")
        print(f"OpenAI Large: ~$0.13 (API cost)")
        
        print(f"\n🎉 Simulation Completed!")


def main():
    """Main simulation function."""
    try:
        simulator = PDF50PagesSimulator()
        simulator.run_simulation()
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")


if __name__ == "__main__":
    main()
