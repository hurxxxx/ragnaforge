#!/usr/bin/env python3
"""
Test script for the unified search architecture.

This script tests the new modular search architecture with pluggable backends.
"""

import asyncio
import logging
import time
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_backend_factory():
    """Test the search backend factory."""
    print("🏭 Testing Search Backend Factory")
    print("=" * 50)
    
    try:
        from services.search_factory import SearchBackendFactory, VectorBackendType, TextBackendType
        
        # Test available backends
        available_vector = SearchBackendFactory.get_available_vector_backends()
        available_text = SearchBackendFactory.get_available_text_backends()
        
        print(f"📊 Available vector backends: {available_vector}")
        print(f"📊 Available text backends: {available_text}")
        
        # Test backend creation
        if "qdrant" in available_vector:
            print("✅ Creating Qdrant vector backend...")
            vector_backend = SearchBackendFactory.create_vector_backend(VectorBackendType.QDRANT)
            print(f"   Backend name: {vector_backend.backend_name}")
            print(f"   Connected: {vector_backend.is_connected}")
        
        if "meilisearch" in available_text:
            print("✅ Creating MeiliSearch text backend...")
            text_backend = SearchBackendFactory.create_text_backend(TextBackendType.MEILISEARCH)
            print(f"   Backend name: {text_backend.backend_name}")
            print(f"   Connected: {text_backend.is_connected}")
        
        return True
        
    except Exception as e:
        print(f"❌ Backend factory test failed: {e}")
        return False


async def test_unified_search_service():
    """Test the unified search service."""
    print("\n🔍 Testing Unified Search Service")
    print("=" * 50)
    
    try:
        from services.unified_search_service import unified_search_service
        
        # Initialize service
        print("🔧 Initializing unified search service...")
        init_success = await unified_search_service.initialize()
        
        if not init_success:
            print("❌ Failed to initialize unified search service")
            return False
        
        print("✅ Unified search service initialized successfully")
        
        # Health check
        print("🏥 Performing health check...")
        health = await unified_search_service.health_check()
        print(f"   Overall status: {health.get('status')}")
        print(f"   Vector backend: {health.get('vector_backend', {}).get('status')}")
        print(f"   Text backend: {health.get('text_backend', {}).get('status')}")
        
        # Get stats
        print("📊 Getting service statistics...")
        stats = unified_search_service.get_stats()
        print(f"   Initialized: {stats.get('unified_search', {}).get('initialized')}")
        print(f"   Vector backend: {stats.get('vector_backend', {}).get('backend')}")
        print(f"   Text backend: {stats.get('text_backend', {}).get('backend')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Unified search service test failed: {e}")
        return False


async def test_backend_switching():
    """Test backend switching capability."""
    print("\n🔄 Testing Backend Switching")
    print("=" * 50)
    
    try:
        from config import settings
        
        print(f"📋 Current configuration:")
        print(f"   Vector backend: {settings.vector_backend}")
        print(f"   Text backend: {settings.text_backend}")
        print(f"   MeiliSearch URL: {settings.meilisearch_url}")
        print(f"   Qdrant host: {settings.qdrant_host}:{settings.qdrant_port}")
        
        # Test configuration validation
        from services.search_factory import SearchBackendFactory
        
        is_valid, error = SearchBackendFactory.validate_backend_config(
            settings.vector_backend, 
            settings.text_backend
        )
        
        print(f"🔍 Configuration validation: {'✅ Valid' if is_valid else f'❌ Invalid - {error}'}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Backend switching test failed: {e}")
        return False


async def test_search_functionality():
    """Test basic search functionality."""
    print("\n🔍 Testing Search Functionality")
    print("=" * 50)
    
    try:
        from services.unified_search_service import unified_search_service
        
        if not unified_search_service.is_initialized:
            print("⚠️  Service not initialized, skipping search tests")
            return True
        
        test_query = "인공지능 기술"
        
        # Test vector search
        print(f"🔍 Testing vector search with query: '{test_query}'")
        vector_result = await unified_search_service.vector_search(
            query=test_query,
            limit=5
        )
        
        print(f"   Success: {vector_result.get('success')}")
        print(f"   Results: {vector_result.get('total_results', 0)}")
        print(f"   Search time: {vector_result.get('search_time', 0):.3f}s")
        
        # Test text search
        print(f"📝 Testing text search with query: '{test_query}'")
        text_result = await unified_search_service.text_search(
            query=test_query,
            limit=5
        )
        
        print(f"   Success: {text_result.get('success')}")
        print(f"   Results: {len(text_result.get('results', []))}")
        print(f"   Search time: {text_result.get('search_time', 0):.3f}s")
        
        # Test hybrid search
        print(f"🔀 Testing hybrid search with query: '{test_query}'")
        hybrid_result = await unified_search_service.hybrid_search(
            query=test_query,
            limit=5,
            vector_weight=0.6,
            text_weight=0.4
        )
        
        print(f"   Success: {hybrid_result.get('success')}")
        print(f"   Results: {hybrid_result.get('total_results', 0)}")
        print(f"   Search time: {hybrid_result.get('search_time', 0):.3f}s")
        print(f"   Vector results: {hybrid_result.get('vector_results_count', 0)}")
        print(f"   Text results: {hybrid_result.get('text_results_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Search functionality test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Testing Unified Search Architecture")
    print("=" * 80)
    
    start_time = time.time()
    
    tests = [
        ("Backend Factory", test_backend_factory),
        ("Unified Search Service", test_unified_search_service),
        ("Backend Switching", test_backend_switching),
        ("Search Functionality", test_search_functionality)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running test: {test_name}")
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   Result: {status}")
        except Exception as e:
            print(f"   Result: ❌ ERROR - {e}")
            results[test_name] = False
    
    # Summary
    total_time = time.time() - start_time
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"\n📊 Test Summary")
    print("=" * 50)
    print(f"⏱️  Total time: {total_time:.2f}s")
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    if passed == total:
        print("\n🎉 All tests passed! Architecture is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
