"""
Main rerank service for document re-ranking functionality.

This service provides a high-level interface for re-ranking search results
using various cross-encoder models, with caching and performance optimization.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Union
import logging
from functools import lru_cache
import hashlib
import json

from .rerank.rerank_interface import RerankInterface, RerankResult
from .rerank.rerank_factory import RerankFactory, RerankModelType
from config import settings

logger = logging.getLogger(__name__)


class RerankService:
    """Main service for document re-ranking operations."""
    
    def __init__(self):
        """Initialize the rerank service."""
        self.reranker: Optional[RerankInterface] = None
        self._initialized = False
        self._cache = {}
        self._cache_enabled = getattr(settings, 'rerank_cache_enabled', True)
        self._cache_size = getattr(settings, 'rerank_cache_size', 1000)
        
        logger.info("Rerank service initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize the rerank service with configured model.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            if not getattr(settings, 'rerank_enabled', True):
                logger.info("Rerank service disabled in configuration")
                return True
            
            start_time = time.time()
            logger.info("Initializing rerank service...")
            
            # Create reranker instance
            self.reranker = RerankFactory.create_default_reranker(
                device=getattr(settings, 'rerank_device', None),
                batch_size=getattr(settings, 'rerank_batch_size', 32)
            )
            
            # Initialize the reranker
            success = await self.reranker.initialize()
            
            if success:
                init_time = time.time() - start_time
                logger.info(f"Rerank service initialized successfully in {init_time:.2f}s")
                logger.info(f"Model info: {self.reranker.get_model_info()}")
                self._initialized = True
            else:
                logger.error("Failed to initialize reranker")
                self._initialized = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error initializing rerank service: {str(e)}")
            self._initialized = False
            return False
    
    async def rerank_documents(self,
                              query: str,
                              documents: List[Dict[str, Any]],
                              top_k: Optional[int] = None,
                              use_cache: bool = True) -> Dict[str, Any]:
        """
        Re-rank documents based on query relevance.
        
        Args:
            query: Search query
            documents: List of documents to re-rank
            top_k: Number of top results to return
            use_cache: Whether to use caching
            
        Returns:
            Dictionary containing reranked documents and metadata
        """
        start_time = time.time()
        
        # Check if rerank is enabled and initialized
        if not self.is_enabled():
            logger.debug("Rerank service not enabled, returning original documents")
            return {
                "success": True,
                "documents": documents[:top_k] if top_k else documents,
                "rerank_applied": False,
                "processing_time": 0.0,
                "message": "Rerank service not enabled"
            }
        
        if not documents:
            return {
                "success": True,
                "documents": [],
                "rerank_applied": False,
                "processing_time": 0.0,
                "message": "No documents to rerank"
            }
        
        try:
            # Check cache if enabled
            cache_key = None
            if use_cache and self._cache_enabled:
                cache_key = self._generate_cache_key(query, documents, top_k)
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    logger.debug("Returning cached rerank result")
                    cached_result["from_cache"] = True
                    return cached_result
            
            # Perform reranking
            reranked_docs = await self.reranker.rerank(query, documents, top_k)
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "documents": reranked_docs,
                "rerank_applied": True,
                "processing_time": processing_time,
                "original_count": len(documents),
                "reranked_count": len(reranked_docs),
                "model_info": self.reranker.get_model_info(),
                "from_cache": False
            }
            
            # Cache the result
            if cache_key and self._cache_enabled:
                self._add_to_cache(cache_key, result)
            
            logger.info(f"Reranked {len(documents)} documents to {len(reranked_docs)} in {processing_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during reranking: {str(e)}")
            return {
                "success": False,
                "documents": documents[:top_k] if top_k else documents,
                "rerank_applied": False,
                "processing_time": time.time() - start_time,
                "error": str(e)
            }
    
    async def batch_rerank_documents(self,
                                   queries: List[str],
                                   documents_list: List[List[Dict[str, Any]]],
                                   top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Batch re-rank multiple query-document sets.
        
        Args:
            queries: List of search queries
            documents_list: List of document lists for each query
            top_k: Number of top results to return per query
            
        Returns:
            List of rerank results for each query
        """
        if not self.is_enabled():
            return [
                {
                    "success": True,
                    "documents": docs[:top_k] if top_k else docs,
                    "rerank_applied": False,
                    "message": "Rerank service not enabled"
                }
                for docs in documents_list
            ]
        
        # Process each query-documents pair
        results = []
        for query, documents in zip(queries, documents_list):
            result = await self.rerank_documents(query, documents, top_k)
            results.append(result)
        
        return results
    
    def _generate_cache_key(self, query: str, documents: List[Dict[str, Any]], top_k: Optional[int]) -> str:
        """Generate cache key for query and documents."""
        # Create a hash of query, document IDs, and top_k
        doc_ids = [doc.get('id', str(i)) for i, doc in enumerate(documents)]
        cache_data = {
            "query": query,
            "doc_ids": doc_ids,
            "top_k": top_k,
            "model": self.reranker.get_model_info().get('model_name', 'unknown')
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache."""
        return self._cache.get(cache_key)
    
    def _add_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Add result to cache with size limit."""
        if len(self._cache) >= self._cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        # Store a copy without 'from_cache' flag
        cached_result = result.copy()
        cached_result.pop('from_cache', None)
        self._cache[cache_key] = cached_result
    
    def clear_cache(self) -> None:
        """Clear the rerank cache."""
        self._cache.clear()
        logger.info("Rerank cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "enabled": self._cache_enabled,
            "size": len(self._cache),
            "max_size": self._cache_size,
            "hit_ratio": getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1)
        }
    
    def is_enabled(self) -> bool:
        """Check if rerank service is enabled and initialized."""
        return (
            getattr(settings, 'rerank_enabled', True) and
            self._initialized and
            self.reranker is not None and
            self.reranker.is_initialized()
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded rerank model."""
        if self.reranker:
            return self.reranker.get_model_info()
        return {"status": "not_initialized"}
    
    async def cleanup(self) -> None:
        """Clean up rerank service resources."""
        try:
            if self.reranker:
                await self.reranker.cleanup()
            
            self.clear_cache()
            self._initialized = False
            logger.info("Rerank service cleaned up")
            
        except Exception as e:
            logger.error(f"Error during rerank service cleanup: {str(e)}")


# Global rerank service instance
rerank_service = RerankService()
