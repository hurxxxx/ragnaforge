#!/usr/bin/env python3
"""GPU Performance Test for KURE v1 API Gateway."""

import time
import requests
import json
import os
import sys
import subprocess
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GPUPerformanceTester:
    """Comprehensive GPU performance testing for KURE v1."""
    
    def __init__(self):
        self.kure_api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
        self.kure_base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        self.kure_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.kure_api_key}"
        }
        
        print("🚀 GPU Performance Test for KURE v1")
        print("=" * 80)
        print(f"🔑 API Key: {self.kure_api_key[:20]}...")
        print(f"🌐 Base URL: {self.kure_base_url}")

    def check_gpu_availability(self) -> Dict[str, Any]:
        """Check GPU availability and specifications."""
        gpu_info = {
            "available": False,
            "count": 0,
            "details": []
        }
        
        try:
            # Check nvidia-smi
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.free,utilization.gpu', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                gpu_info["available"] = True
                lines = result.stdout.strip().split('\n')
                
                for i, line in enumerate(lines):
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 4:
                            gpu_info["details"].append({
                                "id": i,
                                "name": parts[0],
                                "memory_total": f"{parts[1]} MB",
                                "memory_free": f"{parts[2]} MB",
                                "utilization": f"{parts[3]}%"
                            })
                
                gpu_info["count"] = len(gpu_info["details"])
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"⚠️  GPU check failed: {e}")
        
        return gpu_info

    def check_pytorch_gpu(self) -> Dict[str, Any]:
        """Check PyTorch GPU support."""
        pytorch_info = {
            "available": False,
            "cuda_version": None,
            "device_count": 0,
            "current_device": None
        }
        
        try:
            import torch
            pytorch_info["available"] = torch.cuda.is_available()
            
            if pytorch_info["available"]:
                pytorch_info["cuda_version"] = torch.version.cuda
                pytorch_info["device_count"] = torch.cuda.device_count()
                pytorch_info["current_device"] = torch.cuda.current_device()
                
                # Get device names
                pytorch_info["devices"] = []
                for i in range(pytorch_info["device_count"]):
                    device_name = torch.cuda.get_device_name(i)
                    memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
                    pytorch_info["devices"].append({
                        "id": i,
                        "name": device_name,
                        "memory_gb": f"{memory_total:.1f} GB"
                    })
        
        except ImportError:
            print("⚠️  PyTorch not available")
        except Exception as e:
            print(f"⚠️  PyTorch GPU check failed: {e}")
        
        return pytorch_info

    def load_test_document(self) -> str:
        """Load test document for performance testing."""
        try:
            with open('sample_docs/기업 문서 검색 도구 분석.md', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create different sized documents for testing
            return content
            
        except FileNotFoundError:
            # Fallback: generate synthetic document
            print("⚠️  Sample document not found, generating synthetic content")
            return self.generate_synthetic_document()

    def generate_synthetic_document(self, target_chars: int = 32500) -> str:
        """Generate synthetic Korean document for testing."""
        base_sentences = [
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
        
        document = ""
        sentence_idx = 0
        
        while len(document) < target_chars:
            sentence = base_sentences[sentence_idx % len(base_sentences)]
            document += f"{sentence} "
            sentence_idx += 1
        
        return document[:target_chars]

    def chunk_document(self, text: str, chunk_size: int = 380) -> List[str]:
        """Chunk document for testing."""
        try:
            payload = {
                "text": text,
                "strategy": "recursive",
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
                print(f"✅ Document chunked: {len(chunks)} chunks")
                return chunks
            else:
                print(f"❌ Chunking failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Chunking error: {e}")
            return []

    def test_batch_performance(self, chunks: List[str], batch_sizes: List[int]) -> Dict[str, Any]:
        """Test different batch sizes for optimal GPU performance."""
        results = {}
        
        print(f"\n🧪 Testing Batch Performance with {len(chunks)} chunks")
        print("-" * 60)
        
        for batch_size in batch_sizes:
            print(f"\n🔍 Testing batch size: {batch_size}")
            
            try:
                start_time = time.time()
                total_embeddings = 0
                batch_times = []
                
                # Process in batches
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
                        total_embeddings += len(data['data'])
                        print(f"   Batch {i//batch_size + 1}: {len(batch)} chunks in {batch_time:.2f}s")
                    else:
                        print(f"   ❌ Batch {i//batch_size + 1} failed: {response.status_code}")
                        break
                
                end_time = time.time()
                total_time = end_time - start_time
                
                if total_embeddings > 0:
                    results[batch_size] = {
                        "total_time": total_time,
                        "chunks_processed": total_embeddings,
                        "chunks_per_second": total_embeddings / total_time,
                        "avg_batch_time": sum(batch_times) / len(batch_times),
                        "batch_count": len(batch_times),
                        "success": True
                    }
                    print(f"   ✅ Total: {total_time:.2f}s, Speed: {total_embeddings/total_time:.1f} chunks/s")
                else:
                    results[batch_size] = {"success": False}
                    print(f"   ❌ Failed")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[batch_size] = {"success": False, "error": str(e)}
        
        return results

    def test_document_sizes(self) -> Dict[str, Any]:
        """Test performance with different document sizes."""
        document_sizes = [
            ("Small (10 pages)", 6500),
            ("Medium (25 pages)", 16250),
            ("Large (50 pages)", 32500),
            ("XLarge (100 pages)", 65000)
        ]
        
        results = {}
        
        print(f"\n📄 Testing Different Document Sizes")
        print("-" * 60)
        
        for size_name, char_count in document_sizes:
            print(f"\n📋 Testing {size_name}: {char_count:,} characters")
            
            # Generate document of specific size
            if char_count <= 32500:
                base_doc = self.load_test_document()
                if len(base_doc) > char_count:
                    test_doc = base_doc[:char_count]
                else:
                    test_doc = base_doc
            else:
                test_doc = self.generate_synthetic_document(char_count)
            
            # Chunk document
            chunks = self.chunk_document(test_doc)
            if not chunks:
                continue
            
            # Test with optimal batch size (will be determined from previous tests)
            optimal_batch_size = 32  # Default, can be adjusted based on GPU
            
            start_time = time.time()
            
            try:
                total_embeddings = 0
                
                for i in range(0, len(chunks), optimal_batch_size):
                    batch = chunks[i:i + optimal_batch_size]
                    
                    payload = {
                        "input": batch,
                        "model": "nlpai-lab/KURE-v1"
                    }
                    
                    response = requests.post(
                        f"{self.kure_base_url}/embeddings",
                        json=payload,
                        headers=self.kure_headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        total_embeddings += len(data['data'])
                    else:
                        print(f"   ❌ Batch failed: {response.status_code}")
                        break
                
                end_time = time.time()
                total_time = end_time - start_time
                
                results[size_name] = {
                    "char_count": char_count,
                    "chunk_count": len(chunks),
                    "total_time": total_time,
                    "chunks_per_second": total_embeddings / total_time,
                    "chars_per_second": char_count / total_time,
                    "success": True
                }
                
                print(f"   ✅ {total_time:.2f}s, {total_embeddings/total_time:.1f} chunks/s, {char_count/total_time:.0f} chars/s")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[size_name] = {"success": False, "error": str(e)}
        
        return results

    def run_comprehensive_test(self):
        """Run comprehensive GPU performance test."""
        print("\n🔧 System Information")
        print("-" * 60)
        
        # Check GPU availability
        gpu_info = self.check_gpu_availability()
        if gpu_info["available"]:
            print(f"✅ GPU Available: {gpu_info['count']} device(s)")
            for gpu in gpu_info["details"]:
                print(f"   GPU {gpu['id']}: {gpu['name']} ({gpu['memory_total']}, {gpu['memory_free']} free)")
        else:
            print("❌ No GPU detected")
        
        # Check PyTorch GPU support
        pytorch_info = self.check_pytorch_gpu()
        if pytorch_info["available"]:
            print(f"✅ PyTorch CUDA: {pytorch_info['cuda_version']}")
            for device in pytorch_info.get("devices", []):
                print(f"   Device {device['id']}: {device['name']} ({device['memory_gb']})")
        else:
            print("❌ PyTorch CUDA not available")
        
        # Load test document
        print(f"\n📄 Loading Test Document")
        print("-" * 60)
        test_doc = self.load_test_document()
        print(f"✅ Document loaded: {len(test_doc):,} characters")
        
        # Chunk document
        chunks = self.chunk_document(test_doc)
        if not chunks:
            print("❌ Failed to chunk document")
            return
        
        # Test different batch sizes
        batch_sizes = [1, 4, 8, 16, 32, 64, 128]
        if gpu_info["available"]:
            # Add larger batch sizes for GPU
            batch_sizes.extend([256, 512])
        
        batch_results = self.test_batch_performance(chunks[:100], batch_sizes)  # Test with first 100 chunks
        
        # Test different document sizes
        size_results = self.test_document_sizes()
        
        # Print comprehensive analysis
        self.print_analysis(gpu_info, pytorch_info, batch_results, size_results)

    def print_analysis(self, gpu_info: Dict, pytorch_info: Dict, 
                      batch_results: Dict, size_results: Dict):
        """Print comprehensive performance analysis."""
        print(f"\n📊 Performance Analysis")
        print("=" * 80)
        
        # Batch size analysis
        if batch_results:
            print(f"\n🚀 Batch Size Performance:")
            print("-" * 60)
            print(f"{'Batch Size':<12} {'Time (s)':<10} {'Speed':<15} {'Avg/Batch':<12}")
            print("-" * 60)
            
            successful_results = {k: v for k, v in batch_results.items() if v.get("success")}
            
            for batch_size, result in successful_results.items():
                speed = result["chunks_per_second"]
                avg_batch = result["avg_batch_time"]
                total_time = result["total_time"]
                
                print(f"{batch_size:<12} {total_time:<10.2f} {speed:<15.1f} {avg_batch:<12.2f}")
            
            if successful_results:
                # Find optimal batch size
                optimal = max(successful_results.items(), key=lambda x: x[1]["chunks_per_second"])
                print(f"\n🏆 Optimal Batch Size: {optimal[0]} ({optimal[1]['chunks_per_second']:.1f} chunks/s)")
        
        # Document size analysis
        if size_results:
            print(f"\n📄 Document Size Performance:")
            print("-" * 80)
            print(f"{'Document Size':<20} {'Chunks':<8} {'Time (s)':<10} {'Speed':<15}")
            print("-" * 80)
            
            for size_name, result in size_results.items():
                if result.get("success"):
                    chunks = result["chunk_count"]
                    time_val = result["total_time"]
                    speed = result["chunks_per_second"]
                    
                    print(f"{size_name:<20} {chunks:<8} {time_val:<10.2f} {speed:<15.1f}")
        
        # GPU recommendations
        print(f"\n💡 Recommendations:")
        print("-" * 60)
        
        if gpu_info["available"]:
            print("✅ GPU detected - Performance should be optimal")
            if successful_results:
                best_batch = max(successful_results.items(), key=lambda x: x[1]["chunks_per_second"])
                print(f"✅ Use batch size {best_batch[0]} for best performance")
        else:
            print("⚠️  No GPU detected - Consider GPU acceleration for better performance")
            print("💰 Expected GPU improvement: 5-15x faster processing")
        
        if pytorch_info["available"]:
            print("✅ PyTorch CUDA ready for GPU acceleration")
        else:
            print("⚠️  Install PyTorch with CUDA support for GPU acceleration")


def main():
    """Main test function."""
    try:
        tester = GPUPerformanceTester()
        tester.run_comprehensive_test()
        
        print("\n🎉 GPU Performance Test Completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
