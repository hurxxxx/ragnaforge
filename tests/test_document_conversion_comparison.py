#!/usr/bin/env python3
"""Test script for comparing marker and docling PDF conversion performance."""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_document_conversion_comparison():
    """Test and compare marker vs docling PDF conversion performance."""
    
    print("🔄 PDF Document Conversion Performance Comparison")
    print("=" * 80)
    
    # Configuration
    api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    # Test file path
    test_file = "sample_docs/P02_01_01_001_20210101.pdf"
    output_dir = "test_outputs/conversion_comparison"
    
    print(f"🔑 Using API Key: {api_key[:20]}...")
    print(f"🌐 Base URL: {base_url}")
    print(f"📄 Test File: {test_file}")
    print(f"📁 Output Directory: {output_dir}")
    print()
    
    # Check if test file exists
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Test data
    test_data = {
        "file_path": test_file,
        "output_dir": output_dir,
        "extract_images": True
    }
    
    print("🧪 Starting conversion tests...")
    print()
    
    # Test 1: Marker conversion
    print("1. 🎯 Testing Marker PDF conversion...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/v1/convert/marker",
            headers=headers,
            json=test_data,
            timeout=300  # 5 minutes timeout
        )
        marker_total_time = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            marker_result = response.json()
            print(f"   ✅ Marker conversion successful!")
            print(f"   ⏱️  Conversion time: {marker_result['conversion_time']:.2f}s")
            print(f"   📊 File size: {marker_result['file_size_mb']:.2f} MB")
            print(f"   📝 Markdown length: {marker_result['markdown_length']:,} chars")
            print(f"   🖼️  Images found: {marker_result['images_count']}")
            if marker_result['gpu_memory_used_gb']:
                print(f"   🎮 GPU memory used: {marker_result['gpu_memory_used_gb']:.2f} GB")
            print(f"   💾 Files saved: {len(marker_result['saved_files'])} files")
        else:
            print(f"   ❌ Marker conversion failed: {response.text}")
            marker_result = None
    except Exception as e:
        print(f"   ❌ Marker test error: {e}")
        marker_result = None
        marker_total_time = 0
    
    print()
    
    # Test 2: Docling conversion
    print("2. 🎯 Testing Docling PDF conversion...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/v1/convert/docling",
            headers=headers,
            json=test_data,
            timeout=300  # 5 minutes timeout
        )
        docling_total_time = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            docling_result = response.json()
            print(f"   ✅ Docling conversion successful!")
            print(f"   ⏱️  Conversion time: {docling_result['conversion_time']:.2f}s")
            print(f"   📊 File size: {docling_result['file_size_mb']:.2f} MB")
            print(f"   📝 Markdown length: {docling_result['markdown_length']:,} chars")
            print(f"   🖼️  Images found: {docling_result['images_count']}")
            if docling_result['gpu_memory_used_gb']:
                print(f"   🎮 GPU memory used: {docling_result['gpu_memory_used_gb']:.2f} GB")
            print(f"   💾 Files saved: {len(docling_result['saved_files'])} files")
        else:
            print(f"   ❌ Docling conversion failed: {response.text}")
            docling_result = None
    except Exception as e:
        print(f"   ❌ Docling test error: {e}")
        docling_result = None
        docling_total_time = 0
    
    print()
    
    # Test 3: Direct comparison
    print("3. 🔄 Testing direct comparison API...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/v1/convert/compare",
            headers=headers,
            json=test_data,
            timeout=600  # 10 minutes timeout for both conversions
        )
        comparison_total_time = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            comparison_result = response.json()
            print(f"   ✅ Comparison completed!")
            print(f"   ⏱️  Total comparison time: {comparison_total_time:.2f}s")
            
            # Display comparison results
            comp = comparison_result['comparison']
            print()
            print("   📊 Performance Comparison:")
            print(f"      🎯 Marker time: {comp['speed_comparison']['marker_time']:.2f}s")
            print(f"      🎯 Docling time: {comp['speed_comparison']['docling_time']:.2f}s")
            print(f"      🏆 Faster library: {comp['speed_comparison']['faster_library']}")
            if comp['speed_comparison']['speed_ratio']:
                print(f"      📈 Speed ratio: {comp['speed_comparison']['speed_ratio']:.2f}x")
            
            print()
            print("   📝 Output Comparison:")
            print(f"      📄 Marker markdown: {comp['output_comparison']['marker_markdown_length']:,} chars")
            print(f"      📄 Docling markdown: {comp['output_comparison']['docling_markdown_length']:,} chars")
            print(f"      🖼️  Marker images: {comp['output_comparison']['marker_images']}")
            print(f"      🖼️  Docling images: {comp['output_comparison']['docling_images']}")
            
            if comp['resource_usage']['marker_gpu_memory'] or comp['resource_usage']['docling_gpu_memory']:
                print()
                print("   🎮 GPU Memory Usage:")
                if comp['resource_usage']['marker_gpu_memory']:
                    print(f"      🎯 Marker: {comp['resource_usage']['marker_gpu_memory']:.2f} GB")
                if comp['resource_usage']['docling_gpu_memory']:
                    print(f"      🎯 Docling: {comp['resource_usage']['docling_gpu_memory']:.2f} GB")
            
            # Save comparison results
            results_file = Path(output_dir) / "comparison_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(comparison_result, f, indent=2, ensure_ascii=False)
            print(f"   💾 Results saved to: {results_file}")
            
        else:
            print(f"   ❌ Comparison failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Comparison test error: {e}")
    
    print()
    print("🎉 Document Conversion Comparison Test Completed!")
    
    # Summary
    if marker_result and docling_result:
        print()
        print("📋 Summary:")
        print(f"   📄 Test file: {test_file}")
        print(f"   📊 File size: {marker_result['file_size_mb']:.2f} MB")
        print()
        print("   🎯 Marker Results:")
        print(f"      ⏱️  Time: {marker_result['conversion_time']:.2f}s")
        print(f"      📝 Output: {marker_result['markdown_length']:,} chars")
        print(f"      🖼️  Images: {marker_result['images_count']}")
        print()
        print("   🎯 Docling Results:")
        print(f"      ⏱️  Time: {docling_result['conversion_time']:.2f}s")
        print(f"      📝 Output: {docling_result['markdown_length']:,} chars")
        print(f"      🖼️  Images: {docling_result['images_count']}")
        print()
        
        # Winner determination
        if marker_result['conversion_time'] < docling_result['conversion_time']:
            speed_winner = "Marker"
            speed_ratio = docling_result['conversion_time'] / marker_result['conversion_time']
        else:
            speed_winner = "Docling"
            speed_ratio = marker_result['conversion_time'] / docling_result['conversion_time']
        
        print(f"   🏆 Speed Winner: {speed_winner} ({speed_ratio:.2f}x faster)")
        
        if marker_result['markdown_length'] > docling_result['markdown_length']:
            output_winner = "Marker"
        elif docling_result['markdown_length'] > marker_result['markdown_length']:
            output_winner = "Docling"
        else:
            output_winner = "Tie"
        
        print(f"   📝 Output Length Winner: {output_winner}")


if __name__ == "__main__":
    test_document_conversion_comparison()
