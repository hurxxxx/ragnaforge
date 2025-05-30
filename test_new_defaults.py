#!/usr/bin/env python3
"""Test new default chunking settings."""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_new_defaults():
    """Test KURE API with new default chunking settings."""
    
    print("🧪 Testing New Default Chunking Settings")
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
    
    # Sample text for testing
    sample_text = """
    이것은 기업 문서 청킹 테스트를 위한 샘플 텍스트입니다.
    새로운 기본값은 recursive 전략을 사용하며, 청크 크기는 380토큰, 오버랩은 70토큰입니다.
    이 설정은 기업 업무 문서에 최적화되어 있습니다.
    구조화된 문서의 계층과 논리적 흐름을 보존하면서도 적절한 크기의 청크를 생성합니다.
    """
    
    # Test 1: Default settings (no parameters provided)
    print("\n1. 📋 Testing with default settings (no parameters)...")
    try:
        payload = {
            "text": sample_text
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strategy used: {data['strategy']} (should be 'recursive')")
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Total tokens: {data['total_tokens']}")
            
            # Show first chunk
            if data['data']:
                chunk = data['data'][0]
                print(f"✅ First chunk tokens: {chunk['token_count']} (target ~380)")
                print(f"✅ First chunk text: {chunk['text'][:100]}...")
        else:
            print(f"❌ Default settings test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Default settings test error: {e}")
    
    # Test 2: Override strategy only
    print("\n2. 🔄 Testing with strategy override (sentence)...")
    try:
        payload = {
            "text": sample_text,
            "strategy": "sentence"
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strategy used: {data['strategy']} (should be 'sentence')")
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Total tokens: {data['total_tokens']}")
        else:
            print(f"❌ Strategy override test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Strategy override test error: {e}")
    
    # Test 3: Override chunk_size only
    print("\n3. 📏 Testing with chunk_size override (500)...")
    try:
        payload = {
            "text": sample_text,
            "chunk_size": 500
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strategy used: {data['strategy']} (should be 'recursive')")
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Total tokens: {data['total_tokens']}")
            
            if data['data']:
                chunk = data['data'][0]
                print(f"✅ First chunk tokens: {chunk['token_count']} (target ~500)")
        else:
            print(f"❌ Chunk size override test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Chunk size override test error: {e}")
    
    # Test 4: Override multiple parameters
    print("\n4. 🎯 Testing with multiple overrides...")
    try:
        payload = {
            "text": sample_text,
            "strategy": "token",
            "chunk_size": 200,
            "overlap": 30,
            "language": "ko"
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strategy used: {data['strategy']} (should be 'token')")
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Total tokens: {data['total_tokens']}")
            
            if data['data']:
                chunk = data['data'][0]
                print(f"✅ First chunk tokens: {chunk['token_count']} (target ~200)")
        else:
            print(f"❌ Multiple overrides test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Multiple overrides test error: {e}")
    
    # Test 5: Test with longer text to see default behavior
    print("\n5. 📄 Testing with longer text (default settings)...")
    try:
        longer_text = sample_text * 10  # Repeat to make it longer
        
        payload = {
            "text": longer_text
        }
        
        response = requests.post(f"{base_url}/v1/chunk", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Strategy used: {data['strategy']} (should be 'recursive')")
            print(f"✅ Total chunks: {data['total_chunks']}")
            print(f"✅ Total tokens: {data['total_tokens']}")
            print(f"✅ Original length: {data['original_length']} chars")
            
            # Show chunk statistics
            token_counts = [chunk['token_count'] for chunk in data['data']]
            if token_counts:
                print(f"✅ Avg tokens per chunk: {sum(token_counts) / len(token_counts):.1f}")
                print(f"✅ Min tokens: {min(token_counts)}")
                print(f"✅ Max tokens: {max(token_counts)}")
        else:
            print(f"❌ Longer text test failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Longer text test error: {e}")
    
    print("\n🎉 New Default Settings Test Completed!")
    print("\n📋 Expected Defaults:")
    print("  - Strategy: recursive")
    print("  - Chunk Size: 380 tokens")
    print("  - Overlap: 70 tokens")
    print("  - Language: auto")
    return True


if __name__ == "__main__":
    test_new_defaults()
