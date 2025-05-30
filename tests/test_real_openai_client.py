#!/usr/bin/env python3
"""Test with real OpenAI Python client library."""

from openai import OpenAI
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_openai_client_compatibility():
    """Test KURE API with real OpenAI client."""

    print("🧪 Testing KURE API with Real OpenAI Client")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
    base_url = os.getenv("BASE_URL", "http://localhost:8000")

    print(f"🔑 Using API Key: {api_key[:20]}...")
    print(f"🌐 Base URL: {base_url}")

    # Create OpenAI client pointing to our KURE API
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    print(f"✅ OpenAI client created with base_url: {base_url}")

    # Test 1: Single text embedding
    print("\n1. 🔍 Testing single text embedding...")
    try:
        response = client.embeddings.create(
            input="안녕하세요, 실제 OpenAI 클라이언트로 테스트하고 있습니다.",
            model="nlpai-lab/KURE-v1"
        )

        print(f"✅ Response type: {type(response)}")
        print(f"✅ Model used: {response.model}")
        print(f"✅ Number of embeddings: {len(response.data)}")
        print(f"✅ Embedding dimension: {len(response.data[0].embedding)}")
        print(f"✅ First embedding index: {response.data[0].index}")
        print(f"✅ Usage tokens: {response.usage.total_tokens}")
        print(f"✅ First few embedding values: {response.data[0].embedding[:5]}")

    except Exception as e:
        print(f"❌ Single embedding test failed: {e}")
        return False

    # Test 2: Batch embeddings
    print("\n2. 📦 Testing batch embeddings...")
    try:
        texts = [
            "첫 번째 한국어 문장입니다.",
            "두 번째 문장은 조금 더 길게 작성해보겠습니다.",
            "세 번째 문장에서는 KURE 모델의 성능을 테스트합니다.",
            "마지막 문장으로 배치 처리를 확인합니다."
        ]

        response = client.embeddings.create(
            input=texts,
            model="nlpai-lab/KURE-v1"
        )

        print(f"✅ Batch size: {len(response.data)}")
        print(f"✅ Model used: {response.model}")
        print(f"✅ Total usage tokens: {response.usage.total_tokens}")

        for i, embedding in enumerate(response.data):
            print(f"✅ Embedding {i}: index={embedding.index}, dim={len(embedding.embedding)}")

        # Verify indices are correct
        indices = [emb.index for emb in response.data]
        expected_indices = list(range(len(texts)))
        assert indices == expected_indices, f"Indices mismatch: {indices} != {expected_indices}"
        print("✅ All embedding indices are correct")

    except Exception as e:
        print(f"❌ Batch embedding test failed: {e}")
        return False

    # Test 3: Models list
    print("\n3. 📋 Testing models list...")
    try:
        models = client.models.list()

        print(f"✅ Models response type: {type(models)}")
        print(f"✅ Number of available models: {len(models.data)}")

        for model in models.data:
            print(f"✅ Model: {model.id} (owned by: {model.owned_by})")
            print(f"   Created: {time.ctime(model.created)}")

    except Exception as e:
        print(f"❌ Models list test failed: {e}")
        return False

    # Test 4: Different encoding formats
    print("\n4. 🔧 Testing different encoding formats...")
    try:
        response = client.embeddings.create(
            input="인코딩 형식 테스트",
            model="nlpai-lab/KURE-v1",
            encoding_format="float"
        )

        print(f"✅ Encoding format 'float' works")
        print(f"✅ Embedding type: {type(response.data[0].embedding[0])}")

    except Exception as e:
        print(f"❌ Encoding format test failed: {e}")
        return False

    # Test 5: Additional OpenAI parameters
    print("\n5. ⚙️ Testing additional OpenAI parameters...")
    try:
        response = client.embeddings.create(
            input="추가 파라미터 테스트",
            model="nlpai-lab/KURE-v1",
            dimensions=1024,  # This should be ignored gracefully
            user="test-user-123"
        )

        print(f"✅ Additional parameters accepted")
        print(f"✅ Actual embedding dimension: {len(response.data[0].embedding)}")

    except Exception as e:
        print(f"❌ Additional parameters test failed: {e}")
        return False

    # Test 6: Error handling
    print("\n6. ⚠️ Testing error handling...")
    try:
        # Try with too many inputs to trigger validation error
        large_batch = ["테스트 문장"] * 50  # Exceeds our limit of 32

        response = client.embeddings.create(
            input=large_batch,
            model="nlpai-lab/KURE-v1"
        )

        print("❌ Expected error but request succeeded")
        return False

    except Exception as e:
        print(f"✅ Error handling works correctly: {type(e).__name__}")
        print(f"✅ Error message: {str(e)[:100]}...")

    # Test 7: KoE5 model (if available)
    print("\n7. 🔄 Testing KoE5 model...")
    try:
        response = client.embeddings.create(
            input="KoE5 모델 테스트입니다.",
            model="nlpai-lab/KoE5"
        )

        print(f"✅ KoE5 model works")
        print(f"✅ Model used: {response.model}")
        print(f"✅ Embedding dimension: {len(response.data[0].embedding)}")

    except Exception as e:
        print(f"⚠️ KoE5 model test failed (might not be available): {e}")

    print("\n🎉 All OpenAI Client Compatibility Tests Completed Successfully!")
    return True


def test_openai_client_advanced():
    """Test advanced OpenAI client features."""

    print("\n🚀 Advanced OpenAI Client Features Test")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
    base_url = os.getenv("BASE_URL", "http://localhost:8000")

    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    # Test async-like behavior (though we're using sync client)
    print("\n1. 🔄 Testing multiple sequential requests...")
    try:
        texts = [
            "첫 번째 요청입니다.",
            "두 번째 요청입니다.",
            "세 번째 요청입니다."
        ]

        responses = []
        for i, text in enumerate(texts):
            print(f"   Sending request {i+1}/3...")
            response = client.embeddings.create(
                input=text,
                model="nlpai-lab/KURE-v1"
            )
            responses.append(response)

        print(f"✅ All {len(responses)} requests completed successfully")

        # Verify all responses are valid
        for i, resp in enumerate(responses):
            assert len(resp.data) == 1
            assert len(resp.data[0].embedding) > 0
            print(f"✅ Response {i+1}: {len(resp.data[0].embedding)} dimensions")

    except Exception as e:
        print(f"❌ Sequential requests test failed: {e}")

    # Test with different text lengths
    print("\n2. 📏 Testing different text lengths...")
    try:
        test_texts = [
            "짧은 텍스트",
            "중간 길이의 텍스트로 임베딩 성능을 테스트해보겠습니다.",
            "매우 긴 텍스트입니다. " * 20 + "이렇게 긴 텍스트도 잘 처리되는지 확인해보겠습니다. 한국어 임베딩 모델인 KURE의 성능을 다양한 길이의 텍스트로 테스트하고 있습니다."
        ]

        for i, text in enumerate(test_texts):
            response = client.embeddings.create(
                input=text,
                model="nlpai-lab/KURE-v1"
            )
            print(f"✅ Text {i+1} (length: {len(text)}): {len(response.data[0].embedding)} dimensions")

    except Exception as e:
        print(f"❌ Different text lengths test failed: {e}")

    print("\n✨ Advanced tests completed!")


if __name__ == "__main__":
    success = test_openai_client_compatibility()
    if success:
        test_openai_client_advanced()
    else:
        print("\n❌ Basic compatibility tests failed. Skipping advanced tests.")
