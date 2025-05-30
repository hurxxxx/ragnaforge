#!/usr/bin/env python3
"""Simple test client for KURE API."""

import requests
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_api(base_url="http://localhost:8000"):
    """Test the KURE API endpoints."""

    # Get API key from environment
    api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")

    # Headers with Bearer token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    print(f"Testing KURE API at {base_url}")
    print(f"Using API Key: {api_key[:20]}...")
    print("=" * 50)

    # Test health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        return

    # Test models list
    print("2. Testing models list...")
    try:
        response = requests.get(f"{base_url}/models", headers=headers)
        print(f"Status: {response.status_code}")
        models = response.json()
        print(f"Available models: {len(models['data'])}")
        for model in models['data']:
            print(f"  - {model['id']}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        return

    # Test embeddings
    print("3. Testing embeddings...")
    try:
        payload = {
            "input": [
                "안녕하세요, 한국어 임베딩 테스트입니다.",
                "KURE는 한국어에 특화된 임베딩 모델입니다."
            ]
        }
        response = requests.post(f"{base_url}/embeddings", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Generated {len(result['data'])} embeddings")
        print(f"Embedding dimension: {len(result['data'][0]['embedding'])}")
        print(f"Model used: {result['model']}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        return

    # Test similarity
    print("4. Testing similarity...")
    try:
        payload = {
            "texts": [
                "한국어 자연어 처리",
                "Korean natural language processing",
                "머신러닝과 인공지능"
            ]
        }
        response = requests.post(f"{base_url}/similarity", json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        result = response.json()
        print("Similarity matrix:")
        for i, row in enumerate(result['similarities']):
            print(f"  {i}: {[f'{x:.3f}' for x in row]}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        return

    print("All tests completed successfully! ✅")


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_api(base_url)
