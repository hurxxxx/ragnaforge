#!/usr/bin/env python3
"""Test client for document conversion API using real sample documents."""

import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "sk-ragnaforge-v1-test-key-12345"
SAMPLE_DOCS = [
    "sample_docs/doc_sample.pdf",
    "sample_docs/sample2.pdf"
]

def test_api_health():
    """Test API health endpoints."""
    print("🏥 Testing API Health...")

    try:
        # Test main health
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Main API health: OK")
        else:
            print(f"❌ Main API health failed: {response.status_code}")

        # Test conversion health
        response = requests.get(f"{API_BASE_URL}/v1/convert/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Conversion API health: {result.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Conversion API health failed: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_engines_endpoint():
    """Test engines information endpoint."""
    print("\n🔧 Testing Engines Endpoint...")

    try:
        response = requests.get(f"{API_BASE_URL}/v1/convert/engines", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("✅ Engines endpoint working")

            engines = result.get('engines', {})
            for engine_name, engine_info in engines.items():
                print(f"   🔧 {engine_name}: {engine_info.get('description', '')}")
                print(f"      Formats: {', '.join(engine_info.get('supported_formats', []))}")

            return True
        else:
            print(f"❌ Engines endpoint failed: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Engines test failed: {e}")
        return False

def create_test_pdf():
    """Create a simple test PDF using reportlab."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        filename = "test_document.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        
        # Add content
        c.drawString(100, 750, "Test Document for Ragnaforge API")
        c.drawString(100, 720, "This is a test PDF document.")
        c.drawString(100, 690, "")
        c.drawString(100, 660, "Features to test:")
        c.drawString(120, 630, "• Document conversion")
        c.drawString(120, 600, "• Marker engine")
        c.drawString(120, 570, "• Metadata extraction")
        c.drawString(120, 540, "• Text processing")
        
        c.drawString(100, 500, "This document contains multiple lines of text")
        c.drawString(100, 470, "to test the conversion quality.")
        
        c.save()
        print(f"✅ Created test PDF: {filename}")
        return filename
        
    except ImportError:
        print("⚠️ reportlab not available, creating text file instead")
        return create_test_text_file()

def create_test_text_file():
    """Create a test text file."""
    filename = "test_document.txt"
    content = """# Test Document for Ragnaforge API

This is a test document to verify the document conversion API.

## Features
- Document conversion
- Multiple engines (Marker, Docling)
- Metadata extraction
- Text processing

## Content
Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

### Table Example
| Engine | Format | Features |
|--------|--------|----------|
| Marker | PDF | High quality, Images |
| Docling | Multi | Office docs, Metadata |

This document tests the conversion capabilities of Ragnaforge.
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created test text file: {filename}")
    return filename

def test_document_conversion(file_path: str):
    """Test document conversion with different engines."""
    print(f"\n📄 Testing Document Conversion with {file_path}...")

    # Test data - comprehensive testing for PDF files
    if file_path.endswith('.pdf'):
        test_cases = [
            {"engine": "auto", "extract_images": True, "include_image_data": False},
            {"engine": "marker", "extract_images": True, "include_image_data": False},
            {"engine": "docling", "extract_images": False, "include_image_data": False},
            {"engine": "marker", "extract_images": True, "include_image_data": True},  # Test with image data
        ]
    else:
        test_cases = [
            {"engine": "auto", "extract_images": False, "include_image_data": False},
            {"engine": "docling", "extract_images": False, "include_image_data": False},
        ]
    
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        engine = test_case['engine']
        extract_images = test_case['extract_images']
        include_image_data = test_case.get('include_image_data', False)

        print(f"\n{i}️⃣ Testing with {engine} engine (images: {extract_images}, data: {include_image_data})...")

        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                data = {
                    'engine': engine,
                    'extract_images': str(extract_images).lower(),
                    'include_image_data': str(include_image_data).lower()
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{API_BASE_URL}/v1/convert/",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60
                )
                request_time = time.time() - start_time
                
                print(f"   📡 Request time: {request_time:.2f}s")
                print(f"   📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Success with {result.get('engine_used', 'unknown')} engine")
                    print(f"   ⏱️ Conversion time: {result.get('conversion_time', 0):.2f}s")
                    print(f"   📝 Content length: {result.get('content_length', 0):,} chars")
                    print(f"   🖼️ Images: {result.get('images_count', 0)}")
                    
                    # Save result
                    result_file = f"result_{test_case['engine']}.json"
                    with open(result_file, 'w', encoding='utf-8') as rf:
                        json.dump(result, rf, indent=2, ensure_ascii=False)
                    print(f"   💾 Result saved: {result_file}")
                    
                    results.append({
                        'engine': test_case['engine'],
                        'success': True,
                        'conversion_time': result.get('conversion_time', 0),
                        'content_length': result.get('content_length', 0)
                    })
                    
                    # Show content preview
                    content = result.get('markdown_content', '')
                    if content:
                        preview = content[:200] + "..." if len(content) > 200 else content
                        print(f"   📖 Preview: {preview}")
                    
                else:
                    print(f"   ❌ Failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    results.append({
                        'engine': test_case['engine'],
                        'success': False,
                        'error': response.text
                    })
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            results.append({
                'engine': test_case['engine'],
                'success': False,
                'error': str(e)
            })
    
    return results

def print_test_summary(results: list):
    """Print test summary."""
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if successful:
        print("\n🎉 Successful conversions:")
        for result in successful:
            engine = result['engine']
            time_taken = result.get('conversion_time', 0)
            content_len = result.get('content_length', 0)
            print(f"   🔧 {engine}: {time_taken:.2f}s, {content_len:,} chars")
    
    if failed:
        print("\n💥 Failed conversions:")
        for result in failed:
            engine = result['engine']
            error = result.get('error', 'Unknown error')
            print(f"   🔧 {engine}: {error}")
    
    print("="*60)

def main():
    """Main test function."""
    print("🧪 Ragnaforge Document Conversion API Test")
    print("🔑 API Key:", API_KEY)
    print("🌐 API URL:", API_BASE_URL)
    print("="*60)
    
    # Test 1: API Health
    if not test_api_health():
        print("❌ API health check failed. Make sure server is running.")
        return
    
    # Test 2: Engines endpoint
    if not test_engines_endpoint():
        print("❌ Engines endpoint test failed.")
        return
    
    # Test 3: Test with real sample documents
    print("\n📝 Testing with real sample documents...")

    sample_files = SAMPLE_DOCS

    all_results = []

    for sample_file in sample_files:
        if os.path.exists(sample_file):
            print(f"\n{'='*60}")
            print(f"📄 Testing with: {sample_file}")
            print('='*60)

            # Get file info
            file_size = os.path.getsize(sample_file) / (1024 * 1024)  # MB
            print(f"📊 File size: {file_size:.2f} MB")

            # Test 4: Document conversion
            results = test_document_conversion(sample_file)
            all_results.extend(results)

        else:
            print(f"⚠️ Sample file not found: {sample_file}")

    # Test 5: Overall Summary
    if all_results:
        print(f"\n{'='*60}")
        print("📋 OVERALL TEST SUMMARY")
        print('='*60)
        print_test_summary(all_results)
    else:
        print("❌ No sample files found for testing")
    
    print("\n🎉 Test completed!")
    print("💡 Check the result_*.json files for detailed conversion results")

if __name__ == "__main__":
    main()
