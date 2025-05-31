#!/usr/bin/env python3
"""GPU vs CPU Performance Comparison for KURE v1."""

import time
import requests
import json
import os
import subprocess
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GPUvsCPUComparison:
    """Compare GPU vs CPU performance for KURE v1."""
    
    def __init__(self):
        self.kure_api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
        self.kure_base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        self.kure_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.kure_api_key}"
        }
        
        print("🚀 GPU vs CPU Performance Comparison")
        print("=" * 80)

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        info = {
            "gpu_available": False,
            "gpu_count": 0,
            "gpu_details": [],
            "cpu_info": "Unknown"
        }
        
        # GPU info
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', 
                                   '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                info["gpu_available"] = True
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 2:
                            info["gpu_details"].append({
                                "name": parts[0],
                                "memory": parts[1]
                            })
                
                info["gpu_count"] = len(info["gpu_details"])
        
        except Exception:
            pass
        
        # CPU info
        try:
            result = subprocess.run(['lscpu'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Model name:' in line:
                        info["cpu_info"] = line.split(':', 1)[1].strip()
                        break
        except Exception:
            pass
        
        return info

    def generate_test_data(self, size: str = "medium") -> List[str]:
        """Generate test data of different sizes."""
        base_texts = [
            "인공지능 기술이 빠르게 발전하고 있으며, 다양한 산업 분야에서 혁신을 이끌고 있습니다.",
            "기업의 디지털 전환이 가속화되면서 클라우드 컴퓨팅과 빅데이터 분석의 중요성이 증대되고 있습니다.",
            "자동화 기술과 로봇 공학의 발전으로 제조업과 서비스업의 패러다임이 변화하고 있습니다.",
            "사이버 보안의 중요성이 날로 증가하면서 기업들은 보안 투자를 확대하고 있습니다.",
            "원격 근무 환경의 확산으로 협업 도구와 커뮤니케이션 플랫폼의 수요가 급증하고 있습니다.",
            "고객 경험 개선을 위한 개인화 서비스와 추천 시스템의 활용이 확대되고 있습니다.",
            "지속 가능한 경영과 ESG 경영이 기업의 핵심 과제로 부상하고 있습니다.",
            "블록체인 기술이 금융, 물류, 헬스케어 등 다양한 분야에 적용되고 있습니다.",
            "메타버스와 가상현실 기술이 교육, 엔터테인먼트, 비즈니스 영역에서 새로운 기회를 창출하고 있습니다.",
            "양자 컴퓨팅과 차세대 반도체 기술이 컴퓨팅 성능의 한계를 뛰어넘고 있습니다."
        ]
        
        sizes = {
            "small": 20,    # 20 texts
            "medium": 50,   # 50 texts  
            "large": 100,   # 100 texts
            "xlarge": 200   # 200 texts
        }
        
        count = sizes.get(size, 50)
        texts = []
        
        for i in range(count):
            base_text = base_texts[i % len(base_texts)]
            # Add variation to make each text unique
            texts.append(f"{base_text} (테스트 {i+1})")
        
        return texts

    def test_embedding_performance(self, texts: List[str], batch_size: int, 
                                 test_name: str) -> Dict[str, Any]:
        """Test embedding performance with given parameters."""
        print(f"\n🔍 Testing {test_name}")
        print(f"   Texts: {len(texts)}, Batch size: {batch_size}")
        
        start_time = time.time()
        total_embeddings = 0
        batch_times = []
        
        try:
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
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
                    print(f"   Batch {i//batch_size + 1}: {len(batch)} texts in {batch_time:.2f}s")
                else:
                    print(f"   ❌ Batch {i//batch_size + 1} failed: {response.status_code}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
            
            end_time = time.time()
            total_time = end_time - start_time
            
            result = {
                "success": True,
                "total_time": total_time,
                "texts_processed": total_embeddings,
                "texts_per_second": total_embeddings / total_time,
                "avg_batch_time": sum(batch_times) / len(batch_times),
                "batch_count": len(batch_times),
                "batch_size": batch_size
            }
            
            print(f"   ✅ Total: {total_time:.2f}s, Speed: {total_embeddings/total_time:.1f} texts/s")
            return result
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"success": False, "error": str(e)}

    def run_comprehensive_comparison(self):
        """Run comprehensive GPU vs CPU comparison."""
        
        # Get system info
        system_info = self.get_system_info()
        
        print(f"\n🖥️  System Information")
        print("-" * 60)
        print(f"CPU: {system_info['cpu_info']}")
        
        if system_info["gpu_available"]:
            print(f"GPU: {system_info['gpu_count']} device(s)")
            for i, gpu in enumerate(system_info["gpu_details"]):
                print(f"  GPU {i}: {gpu['name']} ({gpu['memory']})")
        else:
            print("GPU: Not available")
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Small Load (20 texts)",
                "texts": self.generate_test_data("small"),
                "batch_sizes": [4, 8, 16, 32]
            },
            {
                "name": "Medium Load (50 texts)", 
                "texts": self.generate_test_data("medium"),
                "batch_sizes": [8, 16, 32, 64]
            },
            {
                "name": "Large Load (100 texts)",
                "texts": self.generate_test_data("large"), 
                "batch_sizes": [16, 32, 64, 128]
            }
        ]
        
        all_results = {}
        
        for scenario in test_scenarios:
            print(f"\n📊 {scenario['name']}")
            print("=" * 60)
            
            scenario_results = {}
            
            for batch_size in scenario["batch_sizes"]:
                test_name = f"Batch {batch_size}"
                result = self.test_embedding_performance(
                    scenario["texts"], 
                    batch_size, 
                    test_name
                )
                
                if result["success"]:
                    scenario_results[batch_size] = result
            
            all_results[scenario["name"]] = scenario_results
        
        # Print comprehensive analysis
        self.print_comprehensive_analysis(system_info, all_results)

    def print_comprehensive_analysis(self, system_info: Dict, results: Dict):
        """Print comprehensive performance analysis."""
        print(f"\n📊 Comprehensive Performance Analysis")
        print("=" * 80)
        
        # Performance summary table
        print(f"\n🏆 Performance Summary:")
        print("-" * 80)
        print(f"{'Scenario':<25} {'Best Batch':<12} {'Speed':<15} {'Total Time':<12}")
        print("-" * 80)
        
        best_performances = {}
        
        for scenario_name, scenario_results in results.items():
            if scenario_results:
                # Find best performing batch size
                best_batch = max(scenario_results.items(), 
                               key=lambda x: x[1]["texts_per_second"])
                
                batch_size = best_batch[0]
                performance = best_batch[1]
                
                best_performances[scenario_name] = {
                    "batch_size": batch_size,
                    "speed": performance["texts_per_second"],
                    "total_time": performance["total_time"]
                }
                
                print(f"{scenario_name:<25} {batch_size:<12} "
                      f"{performance['texts_per_second']:<15.1f} "
                      f"{performance['total_time']:<12.2f}")
        
        # Batch size analysis
        print(f"\n📈 Batch Size Performance Analysis:")
        print("-" * 80)
        
        all_batch_results = {}
        for scenario_results in results.values():
            for batch_size, result in scenario_results.items():
                if batch_size not in all_batch_results:
                    all_batch_results[batch_size] = []
                all_batch_results[batch_size].append(result["texts_per_second"])
        
        print(f"{'Batch Size':<12} {'Avg Speed':<15} {'Min Speed':<15} {'Max Speed':<15}")
        print("-" * 80)
        
        for batch_size in sorted(all_batch_results.keys()):
            speeds = all_batch_results[batch_size]
            avg_speed = sum(speeds) / len(speeds)
            min_speed = min(speeds)
            max_speed = max(speeds)
            
            print(f"{batch_size:<12} {avg_speed:<15.1f} {min_speed:<15.1f} {max_speed:<15.1f}")
        
        # Recommendations
        print(f"\n💡 Performance Recommendations:")
        print("-" * 80)
        
        if system_info["gpu_available"]:
            print("✅ GPU detected - Performance should be optimal")
            
            # Find overall best batch size
            if all_batch_results:
                best_overall_batch = max(all_batch_results.items(), 
                                       key=lambda x: sum(x[1])/len(x[1]))
                print(f"✅ Recommended batch size: {best_overall_batch[0]}")
                
                # GPU-specific recommendations
                gpu_memory = system_info["gpu_details"][0]["memory"] if system_info["gpu_details"] else "Unknown"
                print(f"✅ GPU Memory: {gpu_memory}")
                
                if "24" in gpu_memory or "32" in gpu_memory:
                    print("💡 High-end GPU detected: Consider batch sizes 128-256")
                elif "12" in gpu_memory or "16" in gpu_memory:
                    print("💡 Mid-range GPU detected: Optimal batch sizes 64-128")
                elif "8" in gpu_memory:
                    print("💡 Entry-level GPU detected: Optimal batch sizes 32-64")
        else:
            print("⚠️  No GPU detected - Running on CPU")
            print("💰 Expected GPU improvement: 5-15x faster processing")
            print("🔧 Consider GPU upgrade for production workloads")
        
        # Scaling projections
        print(f"\n📈 Scaling Projections:")
        print("-" * 80)
        
        if best_performances:
            # Use medium load as baseline
            medium_perf = best_performances.get("Medium Load (50 texts)")
            if medium_perf:
                speed = medium_perf["speed"]
                
                document_sizes = [
                    ("10-page document", 40, "Small report"),
                    ("25-page document", 100, "Medium document"), 
                    ("50-page document", 200, "Large document"),
                    ("100-page document", 400, "Very large document")
                ]
                
                print(f"{'Document Type':<20} {'Est. Chunks':<12} {'Est. Time':<12} {'Description':<20}")
                print("-" * 80)
                
                for doc_type, chunks, description in document_sizes:
                    est_time = chunks / speed
                    print(f"{doc_type:<20} {chunks:<12} {est_time:<12.1f} {description:<20}")
        
        print(f"\n🎉 Analysis Complete!")


def main():
    """Main comparison function."""
    try:
        comparator = GPUvsCPUComparison()
        comparator.run_comprehensive_comparison()
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
