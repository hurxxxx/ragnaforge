#!/usr/bin/env python3
"""Real API test using requests library."""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_real_api():
    """Test KURE API with real HTTP requests."""
    
    print("🧪 Testing KURE API with Real HTTP Requests")
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
    
    # Test 1: Health check
    print("\n1. 🏥 Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data['status']}")
            print(f"✅ Model loaded: {data['is_model_loaded']}")
            print(f"✅ Version: {data['version']}")
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Models list
    print("\n2. 📋 Testing models list...")
    try:
        response = requests.get(f"{base_url}/models", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Available models: {len(data['data'])}")
            for model in data['data']:
                print(f"  - {model['id']} (owned by: {model['owned_by']})")
        else:
            print(f"❌ Models list failed: {response.text}")
    except Exception as e:
        print(f"❌ Models list error: {e}")
    
    # Test 3: Single embedding
    print("\n3. 🔍 Testing single embedding...")
    try:
        payload = {
            "input": "안녕하세요, KURE v1 API Gateway 테스트입니다.",
            "model": "nlpai-lab/KURE-v1",
            "encoding_format": "float"
        }
        response = requests.post(f"{base_url}/embeddings", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Model: {data['model']}")
            print(f"✅ Embedding dimension: {len(data['data'][0]['embedding'])}")
            print(f"✅ Usage tokens: {data['usage']['total_tokens']}")
            print(f"✅ First few values: {data['data'][0]['embedding'][:5]}")
        else:
            print(f"❌ Single embedding failed: {response.text}")
    except Exception as e:
        print(f"❌ Single embedding error: {e}")
    
    # Test 4: Batch embeddings
    print("\n4. 📦 Testing batch embeddings...")
    try:
        payload = {
            "input": [
                "첫 번째 한국어 문장입니다.",
                "두 번째 문장은 KURE 모델을 테스트합니다.",
                "세 번째 문장으로 배치 처리를 확인합니다."
            ],
            "model": "nlpai-lab/KURE-v1"
        }
        response = requests.post(f"{base_url}/embeddings", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Batch size: {len(data['data'])}")
            print(f"✅ Model: {data['model']}")
            for i, emb in enumerate(data['data']):
                print(f"  - Embedding {i}: index={emb['index']}, dim={len(emb['embedding'])}")
        else:
            print(f"❌ Batch embeddings failed: {response.text}")
    except Exception as e:
        print(f"❌ Batch embeddings error: {e}")
    
    # Test 5: Similarity calculation
    print("\n5. 🔄 Testing similarity calculation...")
    try:
        payload = {
            "texts": [
                "한국어 자연어 처리",
                "Korean natural language processing", 
                "머신러닝과 인공지능",
                "Machine learning and AI"
            ],
            "model": "nlpai-lab/KURE-v1"
        }
        response = requests.post(f"{base_url}/similarity", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Similarity matrix shape: {len(data['similarities'])}x{len(data['similarities'][0])}")
            print(f"✅ Model: {data['model']}")
            print("✅ Similarity matrix:")
            for i, row in enumerate(data['similarities']):
                formatted_row = [f"{x:.3f}" for x in row]
                print(f"  {i}: {formatted_row}")
        else:
            print(f"❌ Similarity calculation failed: {response.text}")
    except Exception as e:
        print(f"❌ Similarity calculation error: {e}")
    
    # Test 6: Authentication test (wrong token)
    print("\n6. 🔐 Testing authentication with wrong token...")
    try:
        wrong_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer wrong-token"
        }
        payload = {"input": "Auth test", "model": "nlpai-lab/KURE-v1"}
        response = requests.post(f"{base_url}/embeddings", json=payload, headers=wrong_headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Authentication properly enforced")
        elif response.status_code == 200:
            print("⚠️ Authentication not enforced (API_KEY not set)")
        else:
            print(f"❌ Unexpected auth response: {response.text}")
    except Exception as e:
        print(f"❌ Auth test error: {e}")
    
    print("\n🎉 Real API Test Completed!")
    return True


if __name__ == "__main__":
    test_real_api()
