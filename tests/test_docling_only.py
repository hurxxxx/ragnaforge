#!/usr/bin/env python3
"""Simple test script for docling PDF conversion only."""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_docling_conversion():
    """Test docling PDF conversion performance."""
    
    print("🔄 Docling PDF Conversion Test")
    print("=" * 50)
    
    # Configuration
    api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    # Test file path
    test_file = "sample_docs/P02_01_01_001_20210101.pdf"
    output_dir = "test_outputs/docling_only"
    
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
    
    print("🧪 Starting Docling conversion test...")
    print()
    
    # Test Docling conversion
    print("🎯 Testing Docling PDF conversion...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{base_url}/v1/convert/docling",
            headers=headers,
            json=test_data,
            timeout=600  # 10 minutes timeout
        )
        total_time = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Docling conversion successful!")
            print(f"   ⏱️  Conversion time: {result['conversion_time']:.2f}s")
            print(f"   ⏱️  Total API time: {total_time:.2f}s")
            print(f"   📊 File size: {result['file_size_mb']:.2f} MB")
            print(f"   📝 Markdown length: {result['markdown_length']:,} chars")
            print(f"   🖼️  Images found: {result['images_count']}")
            if result['gpu_memory_used_gb']:
                print(f"   🎮 GPU memory used: {result['gpu_memory_used_gb']:.2f} GB")
            print(f"   💾 Files saved: {len(result['saved_files'])} files")
            
            # Show saved files
            print("   📁 Saved files:")
            for file_path in result['saved_files']:
                file_size = os.path.getsize(file_path) / 1024  # KB
                print(f"      - {file_path} ({file_size:.1f} KB)")
            
            # Save detailed results
            results_file = Path(output_dir) / "docling_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"   💾 Detailed results saved to: {results_file}")
            
            # Performance metrics
            print()
            print("📊 Performance Metrics:")
            print(f"   📄 Processing speed: {result['file_size_mb'] / result['conversion_time']:.2f} MB/s")
            print(f"   📝 Text extraction rate: {result['markdown_length'] / result['conversion_time']:.0f} chars/s")
            if result['gpu_memory_used_gb']:
                print(f"   🎮 GPU efficiency: {result['file_size_mb'] / result['gpu_memory_used_gb']:.2f} MB/GB")
            
        else:
            print(f"   ❌ Docling conversion failed: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Docling test error: {e}")
    
    print()
    print("🎉 Docling Test Completed!")


if __name__ == "__main__":
    test_docling_conversion()
