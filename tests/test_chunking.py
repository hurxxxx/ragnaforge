#!/usr/bin/env python3
"""Test text chunking functionality."""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_chunking_api():
    """Test KURE API chunking functionality."""
    
    print("🧪 Testing KURE API Text Chunking")
    print("=" * 60)
    
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
    
    # Test 1: Korean text chunking with sentence strategy
    print("\n1. 📝 Testing Korean text chunking (sentence strategy)...")
    try:
        korean_text = """
        안녕하세요, 이것은 한국어 텍스트 청킹 테스트입니다. 
        KURE 모델은 한국어 임베딩에 특화된 모델입니다. 
        이 텍스트는 여러 문장으로 구성되어 있으며, 각 문장은 의미 있는 단위로 분할될 것입니다.
        텍스트 청킹은 긴 문서를 처리할 때 매우 유용한 기능입니다.
        RAG(Retrieval-Augmented Generation) 시스템에서도 자주 사용됩니다.
        이제 이 텍스트가 어떻게 청크로 나뉘는지 확인해보겠습니다.
        """
        
        payload = {
            "text": korean_text.strip(),
            "strategy": "sentence",
            "chunk_size": 100,
            "overlap": 20,
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
            
            for i, chunk in enumerate(data['data'][:3]):  # Show first 3 chunks
                print(f"  Chunk {i}: {chunk['token_count']} tokens, chars {chunk['start_char']}-{chunk['end_char']}")
                print(f"    Text: {chunk['text'][:100]}...")
        else:
            print(f"❌ Korean chunking failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Korean chunking error: {e}")
    
    # Test 2: English text chunking with recursive strategy
    print("\n2. 🔤 Testing English text chunking (recursive strategy)...")
    try:
        english_text = """
        This is an English text chunking test for the KURE API. 
        The KURE model is specialized for Korean embeddings, but it should also handle English text well.
        Text chunking is a crucial feature for processing long documents in natural language processing.
        It helps break down large texts into manageable pieces that can be processed by language models.
        This functionality is particularly useful in RAG systems where documents need to be split into chunks.
        Each chunk should maintain semantic coherence while staying within token limits.
        """
        
        payload = {
            "text": english_text.strip(),
            "strategy": "recursive",
            "chunk_size": 80,
            "overlap": 15,
            "language": "en"
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Strategy used: {data['strategy']}")
            print(f"✅ Original length: {data['original_length']} chars")
            print(f"✅ Total tokens: {data['total_tokens']}")
            
            for i, chunk in enumerate(data['data'][:3]):  # Show first 3 chunks
                print(f"  Chunk {i}: {chunk['token_count']} tokens, chars {chunk['start_char']}-{chunk['end_char']}")
                print(f"    Text: {chunk['text'][:100]}...")
        else:
            print(f"❌ English chunking failed: {response.text}")
            
    except Exception as e:
        print(f"❌ English chunking error: {e}")
    
    # Test 3: Mixed language text with token strategy
    print("\n3. 🌐 Testing mixed language text (token strategy)...")
    try:
        mixed_text = """
        This is a mixed language test. 이것은 혼합 언어 테스트입니다.
        We will test how the chunking algorithm handles both English and Korean text.
        한국어와 영어가 섞인 텍스트에서 청킹이 어떻게 작동하는지 확인해보겠습니다.
        The auto-detection feature should identify the primary language.
        자동 언어 감지 기능이 주요 언어를 식별해야 합니다.
        """
        
        payload = {
            "text": mixed_text.strip(),
            "strategy": "token",
            "chunk_size": 60,
            "overlap": 10,
            "language": "auto"
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Strategy used: {data['strategy']}")
            print(f"✅ Original length: {data['original_length']} chars")
            print(f"✅ Total tokens: {data['total_tokens']}")
            
            for i, chunk in enumerate(data['data']):
                print(f"  Chunk {i}: {chunk['token_count']} tokens, chars {chunk['start_char']}-{chunk['end_char']}")
                print(f"    Text: {chunk['text'][:80]}...")
        else:
            print(f"❌ Mixed language chunking failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Mixed language chunking error: {e}")
    
    # Test 4: Error handling - invalid strategy
    print("\n4. ⚠️ Testing error handling (invalid strategy)...")
    try:
        payload = {
            "text": "Test text for error handling",
            "strategy": "invalid_strategy",
            "chunk_size": 100,
            "overlap": 10,
            "language": "auto"
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Validation error properly handled")
            error_data = response.json()
            print(f"✅ Error details: {error_data}")
        else:
            print(f"❌ Unexpected response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    # Test 5: Large chunk size
    print("\n5. 📏 Testing large chunk size...")
    try:
        large_text = "이것은 큰 청크 크기 테스트입니다. " * 50  # Repeat to make it longer
        
        payload = {
            "text": large_text,
            "strategy": "sentence",
            "chunk_size": 1000,
            "overlap": 50,
            "language": "ko"
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Large text handled successfully")
            print(f"✅ Total tokens: {data['total_tokens']}")
        else:
            print(f"❌ Large chunk test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Large chunk test error: {e}")
    
    print("\n🎉 Text Chunking Test Completed!")
    return True


if __name__ == "__main__":
    test_chunking_api()
