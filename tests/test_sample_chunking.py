#!/usr/bin/env python3
"""Test text chunking functionality with sample document."""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def load_sample_document():
    """Load the sample document."""
    try:
        with open('sample_docs/기업 문서 검색 도구 분석.md', 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print("❌ Sample document not found!")
        return None


def test_chunking_with_sample():
    """Test KURE API chunking functionality with sample document."""
    
    print("🧪 Testing KURE API Text Chunking with Sample Document")
    print("=" * 70)
    
    # Load sample document
    sample_text = load_sample_document()
    if not sample_text:
        return False
    
    print(f"📄 Loaded sample document: {len(sample_text)} characters")
    print(f"📄 First 200 chars: {sample_text[:200]}...")
    
    # Get configuration from environment
    api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    print(f"🔑 Using API Key: {api_key[:20]}...")
    print(f"🌐 Base URL: {base_url}")
    
    # Headers with Bearer token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Test 1: Korean sentence chunking with medium chunks
    print("\n1. 📝 Testing Korean sentence chunking (medium chunks)...")
    try:
        payload = {
            "text": sample_text,
            "strategy": "sentence",
            "chunk_size": 300,
            "overlap": 50,
            "language": "ko"
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Strategy used: {data['strategy']}")
            print(f"✅ Original length: {data['original_length']} chars")
            print(f"✅ Total tokens: {data['total_tokens']}")
            
            # Show first 3 chunks
            for i, chunk in enumerate(data['data'][:3]):
                print(f"\n  📋 Chunk {i}:")
                print(f"    Tokens: {chunk['token_count']}")
                print(f"    Position: chars {chunk['start_char']}-{chunk['end_char']}")
                print(f"    Text: {chunk['text'][:150]}...")
                
            # Show statistics
            token_counts = [chunk['token_count'] for chunk in data['data']]
            print(f"\n  📊 Chunk Statistics:")
            print(f"    Min tokens: {min(token_counts)}")
            print(f"    Max tokens: {max(token_counts)}")
            print(f"    Avg tokens: {sum(token_counts) / len(token_counts):.1f}")
            
        else:
            print(f"❌ Korean sentence chunking failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Korean sentence chunking error: {e}")
    
    # Test 2: Recursive chunking with smaller chunks
    print("\n2. 🔄 Testing recursive chunking (smaller chunks)...")
    try:
        payload = {
            "text": sample_text,
            "strategy": "recursive",
            "chunk_size": 200,
            "overlap": 30,
            "language": "ko"
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Strategy used: {data['strategy']}")
            print(f"✅ Total tokens: {data['total_tokens']}")
            
            # Show first 3 chunks
            for i, chunk in enumerate(data['data'][:3]):
                print(f"\n  📋 Chunk {i}:")
                print(f"    Tokens: {chunk['token_count']}")
                print(f"    Position: chars {chunk['start_char']}-{chunk['end_char']}")
                print(f"    Text: {chunk['text'][:100]}...")
                
        else:
            print(f"❌ Recursive chunking failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Recursive chunking error: {e}")
    
    # Test 3: Token-based chunking with large chunks
    print("\n3. 🎯 Testing token-based chunking (large chunks)...")
    try:
        payload = {
            "text": sample_text,
            "strategy": "token",
            "chunk_size": 500,
            "overlap": 75,
            "language": "auto"
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Strategy used: {data['strategy']}")
            print(f"✅ Total tokens: {data['total_tokens']}")
            
            # Show first 2 chunks
            for i, chunk in enumerate(data['data'][:2]):
                print(f"\n  📋 Chunk {i}:")
                print(f"    Tokens: {chunk['token_count']}")
                print(f"    Position: chars {chunk['start_char']}-{chunk['end_char']}")
                print(f"    Text: {chunk['text'][:120]}...")
                
        else:
            print(f"❌ Token chunking failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Token chunking error: {e}")
    
    # Test 4: Compare strategies with same chunk size
    print("\n4. 📊 Comparing all strategies with same parameters...")
    try:
        strategies = ["sentence", "recursive", "token"]
        results = {}
        
        for strategy in strategies:
            payload = {
                "text": sample_text[:5000],  # Use first 5000 chars for comparison
                "strategy": strategy,
                "chunk_size": 250,
                "overlap": 40,
                "language": "ko"
            }
            
            response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                results[strategy] = {
                    "total_chunks": data['total_chunks'],
                    "total_tokens": data['total_tokens'],
                    "avg_tokens": data['total_tokens'] / data['total_chunks']
                }
            else:
                results[strategy] = {"error": response.text}
        
        print("\n  📈 Strategy Comparison Results:")
        print("  " + "-" * 60)
        print(f"  {'Strategy':<12} {'Chunks':<8} {'Tokens':<8} {'Avg/Chunk':<10}")
        print("  " + "-" * 60)
        
        for strategy, result in results.items():
            if "error" not in result:
                print(f"  {strategy:<12} {result['total_chunks']:<8} {result['total_tokens']:<8} {result['avg_tokens']:<10.1f}")
            else:
                print(f"  {strategy:<12} ERROR")
                
    except Exception as e:
        print(f"❌ Strategy comparison error: {e}")
    
    # Test 5: Test with section of document (specific content)
    print("\n5. 📑 Testing with specific document section...")
    try:
        # Extract a specific section (market analysis)
        section_start = sample_text.find("## **2. 시장성 분석")
        section_end = sample_text.find("## **3. 기능 개요")
        
        if section_start != -1 and section_end != -1:
            section_text = sample_text[section_start:section_end]
            print(f"📄 Extracted section: {len(section_text)} characters")
            
            payload = {
                "text": section_text,
                "strategy": "sentence",
                "chunk_size": 400,
                "overlap": 60,
                "language": "ko"
            }
            
            response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Section chunks: {data['total_chunks']}")
                print(f"✅ Section tokens: {data['total_tokens']}")
                
                # Show all chunks for this section
                for i, chunk in enumerate(data['data']):
                    print(f"\n  📋 Section Chunk {i}:")
                    print(f"    Tokens: {chunk['token_count']}")
                    print(f"    Text: {chunk['text'][:100]}...")
            else:
                print(f"❌ Section chunking failed: {response.text}")
        else:
            print("❌ Could not find market analysis section")
            
    except Exception as e:
        print(f"❌ Section chunking error: {e}")
    
    print("\n🎉 Sample Document Chunking Test Completed!")
    return True


if __name__ == "__main__":
    test_chunking_with_sample()
