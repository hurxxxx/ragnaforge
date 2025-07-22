"""
Unified search service that orchestrates vector and text search backends.

This service provides a high-level interface for search functionality,
abstracting away the specific backend implementations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any

from .search_factory import SearchBackendFactory, VectorBackendType, TextBackendType
from .interfaces.vector_search_interface import VectorSearchInterface
from .interfaces.text_search_interface import TextSearchInterface
from . import embedding_service
from .rerank_service import rerank_service
from config import settings

logger = logging.getLogger(__name__)


class UnifiedSearchService:
    """Unified search service for hybrid vector and text search."""
    
    def __init__(self):
        self.vector_backend: Optional[VectorSearchInterface] = None
        self.text_backend: Optional[TextSearchInterface] = None
        self._initialized = False
        logger.info("Unified search service initialized")
    
    async def initialize(self) -> bool:
        """Initialize both vector and text backends."""
        try:
            # Create vector backend
            vector_backend_type = VectorBackendType(settings.vector_backend)
            self.vector_backend = SearchBackendFactory.create_vector_backend(vector_backend_type)
            
            # Create text backend
            text_backend_type = TextBackendType(settings.text_backend)
            self.text_backend = SearchBackendFactory.create_text_backend(text_backend_type)
            
            # Initialize backends
            vector_init = await self.vector_backend.initialize()
            text_init = await self.text_backend.initialize()
            
            if not vector_init:
                logger.error("Failed to initialize vector backend")
                return False
            
            if not text_init:
                logger.error("Failed to initialize text backend")
                return False
            
            self._initialized = True
            logger.info(f"Unified search service initialized with {settings.vector_backend} + {settings.text_backend}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize unified search service: {str(e)}")
            self._initialized = False
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of both backends."""
        try:
            if not self._initialized:
                return {"status": "not_initialized", "error": "Service not initialized"}
            
            # Get health from both backends
            vector_health, text_health = await asyncio.gather(
                self.vector_backend.health_check(),
                self.text_backend.health_check(),
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(vector_health, Exception):
                vector_health = {"status": "error", "error": str(vector_health)}
            
            if isinstance(text_health, Exception):
                text_health = {"status": "error", "error": str(text_health)}
            
            overall_status = "healthy"
            if vector_health.get("status") != "healthy" or text_health.get("status") != "healthy":
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "vector_backend": vector_health,
                "text_backend": text_health,
                "backends": {
                    "vector": settings.vector_backend,
                    "text": settings.text_backend
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def store_documents(self, documents: List[Dict[str, Any]], full_document: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store documents using hybrid approach for optimal search performance.

        Args:
            documents: List of chunk documents with embeddings (for vector search)
            full_document: Optional full document for text search. If not provided,
                          will use documents for both backends (legacy behavior)

        Returns:
            bool: True if storage successful, False otherwise
        """
        try:
            if not self._initialized:
                logger.error("Service not initialized")
                return False

            # Hybrid approach: separate storage for vector and text backends
            if full_document is not None:
                # New hybrid approach: chunks for vector, full document for text
                vector_docs = []
                for doc in documents:
                    if 'embedding' in doc:
                        vector_docs.append(doc)

                text_docs = [full_document]
                storage_type = "hybrid"

            else:
                # Legacy approach: same documents for both backends
                vector_docs = []
                text_docs = []

                for doc in documents:
                    # For vector backend - need embeddings
                    if 'embedding' in doc:
                        vector_docs.append(doc)

                    # For text backend - need text content
                    if any(key in doc for key in ['content', 'title']):
                        text_docs.append(doc)

                storage_type = "legacy"

            # Store in both backends concurrently
            tasks = []

            # Add vector storage task if we have vector documents
            if vector_docs and self.vector_backend:
                tasks.append(self.vector_backend.store_embeddings(vector_docs))
            else:
                tasks.append(self._empty_coroutine())

            # Add text storage task if we have text documents
            if text_docs and self.text_backend:
                tasks.append(self.text_backend.index_documents(text_docs))
            else:
                tasks.append(self._empty_coroutine())

            results = await asyncio.gather(*tasks, return_exceptions=True)

            vector_success = bool(results[0]) if not isinstance(results[0], Exception) else False
            text_success = bool(results[1]) if not isinstance(results[1], Exception) else False

            if isinstance(results[0], Exception):
                logger.error(f"Vector storage failed: {results[0]}")

            if isinstance(results[1], Exception):
                logger.error(f"Text indexing failed: {results[1]}")

            success = vector_success and text_success
            logger.info(f"Document storage ({storage_type}): vector={len(vector_docs)} docs, text={len(text_docs)} docs, vector_success={vector_success}, text_success={text_success}, overall={success}")

            return success

        except Exception as e:
            logger.error(f"Error storing documents: {str(e)}")
            return False

    async def _empty_coroutine(self) -> bool:
        """Return True as an awaitable coroutine."""
        return True



    async def check_document_exists_by_hash(self, file_hash: str) -> Optional[str]:
        """
        Check if a document with the given file hash already exists.

        Note: This is a simplified implementation that doesn't perform actual hash-based search
        since it requires specific backend support. For now, it returns None to allow new documents.
        """
        try:
            if not self._initialized:
                logger.error("Service not initialized")
                return None

            # TODO: Implement hash-based duplicate detection when backend supports it
            # For now, we'll skip hash-based duplicate detection and rely on document ID uniqueness
            logger.debug(f"Hash-based duplicate detection not implemented, allowing document with hash: {file_hash}")
            return None

        except Exception as e:
            logger.error(f"Error checking document existence by hash: {str(e)}")
            return None

    async def vector_search(self,
                          query: str,
                          limit: int = 10,
                          score_threshold: float = 0.0,
                          filters: Optional[Dict[str, Any]] = None,
                          embedding_model: Optional[str] = None,
                          rerank: bool = False,
                          rerank_top_k: Optional[int] = None) -> Dict[str, Any]:
        """Perform vector similarity search only."""
        start_time = time.time()
        
        try:
            if not self._initialized:
                return {"success": False, "error": "Service not initialized"}
            
            # Generate query embedding
            model = embedding_model or settings.default_model
            query_embeddings = embedding_service.encode_texts([query], model)
            
            if query_embeddings is None or len(query_embeddings) == 0:
                return {"success": False, "error": "Failed to generate query embedding"}
            
            # Convert to list
            query_vector = query_embeddings[0].tolist() if hasattr(query_embeddings[0], 'tolist') else list(query_embeddings[0])
            
            # Determine search limit (get more results if reranking)
            search_limit = limit
            if rerank and rerank_service.is_enabled():
                search_limit = rerank_top_k or getattr(settings, 'rerank_top_k', 100)
                search_limit = max(search_limit, limit * settings.search_expansion_factor)  # Ensure we get enough results

            # Search in vector backend
            raw_results = await self.vector_backend.search_similar(
                query_vector=query_vector,
                limit=search_limit,
                score_threshold=score_threshold,
                filters=filters
            )

            # Format vector search results to include content field
            results = []
            for result in raw_results:
                formatted_result = result.copy()
                # Extract content from metadata.text for vector search results
                metadata = result.get("metadata", {})
                content = metadata.get("text", metadata.get("content", ""))

                # Filter out results with very short content (likely corrupted data)
                if len(content.strip()) < 10:  # Skip results with less than 10 characters
                    logger.warning(f"Skipping vector result with short content: '{content}' (ID: {result.get('id')})")
                    continue

                formatted_result["content"] = content
                formatted_result["search_source"] = "vector"
                results.append(formatted_result)

            # Apply reranking if requested and enabled
            rerank_applied = False
            rerank_info = {}
            if rerank and rerank_service.is_enabled() and results:
                try:
                    # Convert results to rerank format
                    rerank_docs = []
                    for result in results:
                        # Extract text content properly
                        text_content = result.get("content", "")
                        if not text_content:
                            metadata = result.get("metadata", {})
                            text_content = metadata.get("text", metadata.get("content", ""))

                        doc = {
                            "id": result.get("id", ""),
                            "text": text_content,
                            "score": result.get("score", 0.0),
                            "metadata": result.get("metadata", {})
                        }
                        rerank_docs.append(doc)

                    # Perform reranking
                    logger.info(f"🔄 Rerank 시작: {len(rerank_docs)}개 문서")
                    final_k = getattr(settings, 'rerank_final_k', limit)
                    rerank_result = await rerank_service.rerank_documents(
                        query=query,
                        documents=rerank_docs,
                        top_k=final_k,
                        use_cache=True
                    )
                    logger.info(f"✅ Rerank 완료: {rerank_result.get('processing_time', 0):.3f}초")

                    if rerank_result.get("success", False):
                        # Convert reranked results back to original format
                        reranked_results = []
                        for doc in rerank_result["documents"]:
                            # Find original result and update with rerank score
                            original_result = next(
                                (r for r in results if r.get("id") == doc.get("id")),
                                None
                            )
                            if original_result:
                                updated_result = original_result.copy()
                                updated_result["score"] = doc.get("rerank_score", doc.get("score", 0.0))
                                updated_result["original_score"] = doc.get("original_score", 0.0)
                                updated_result["rerank_score"] = doc.get("rerank_score", 0.0)
                                updated_result["rank_position"] = doc.get("rank_position", 1)
                                reranked_results.append(updated_result)

                        results = reranked_results
                        rerank_applied = True
                        rerank_info = {
                            "processing_time": rerank_result.get("processing_time", 0.0),
                            "original_count": rerank_result.get("original_count", 0),
                            "reranked_count": rerank_result.get("reranked_count", 0),
                            "model_info": rerank_result.get("model_info", {}),
                            "from_cache": rerank_result.get("from_cache", False)
                        }

                        logger.info(f"Reranking applied: {len(rerank_docs)} -> {len(results)} results")

                except Exception as e:
                    logger.error(f"Reranking failed, using original results: {str(e)}")

            search_time = time.time() - start_time

            response = {
                "success": True,
                "results": results,
                "search_type": "vector",
                "query": query,
                "total_results": len(results),
                "search_time": search_time,
                "backend": self.vector_backend.backend_name,
                "rerank_applied": rerank_applied
            }

            # Add rerank info if applied
            if rerank_applied:
                response["rerank_info"] = rerank_info

            return response
            
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "search_time": time.time() - start_time
            }
    
    async def text_search(self,
                         query: str,
                         limit: int = 10,
                         offset: int = 0,
                         filters: Optional[Dict[str, Any]] = None,
                         sort: Optional[List[str]] = None,
                         highlight: bool = False) -> Dict[str, Any]:
        """Perform text search only."""
        start_time = time.time()

        try:
            if not self._initialized:
                return {"success": False, "error": "Service not initialized"}

            # Search in text backend
            results = await self.text_backend.search_text(
                query=query,
                limit=limit,
                offset=offset,
                filters=filters,
                sort=sort,
                highlight=highlight
            )

            search_time = time.time() - start_time

            # Convert raw results to SearchResult format
            formatted_results = []
            for item in results.get("hits", []):

                # Extract highlights if available and convert to proper format
                highlights = None
                if highlight and "_formatted" in item:
                    formatted_data = item["_formatted"]
                    highlights = {}
                    # Convert MeiliSearch formatted fields to List[str] format
                    for field, value in formatted_data.items():
                        if isinstance(value, str):
                            # Convert all string values to list format as expected by SearchResult model
                            highlights[field] = [value]

                formatted_result = {
                    "id": str(item.get("id", item.get("document_id", ""))),
                    "score": 1.0,  # Text search might not have explicit scores
                    "metadata": item,
                    "content": item.get("content", item.get("text", "")),
                    "highlights": highlights,
                    "search_source": "text"
                }
                formatted_results.append(formatted_result)

            return {
                "success": True,
                "results": formatted_results,
                "total_results": results.get("total", 0),
                "search_type": "text",
                "query": query,
                "search_time": search_time,
                "backend": self.text_backend.backend_name
            }

        except Exception as e:
            logger.error(f"Text search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "search_time": time.time() - start_time
            }





    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from both backends."""
        try:
            if not self._initialized:
                logger.error("Service not initialized")
                return False

            # Delete from both backends concurrently
            results = await asyncio.gather(
                self.vector_backend.delete_document(document_id),
                self.text_backend.delete_document(document_id),
                return_exceptions=True
            )

            vector_success = results[0] if not isinstance(results[0], Exception) else False
            text_success = results[1] if not isinstance(results[1], Exception) else False

            if isinstance(results[0], Exception):
                logger.error(f"Vector deletion failed: {results[0]}")

            if isinstance(results[1], Exception):
                logger.error(f"Text deletion failed: {results[1]}")

            success = vector_success and text_success
            logger.info(f"Document deletion: vector={vector_success}, text={text_success}, overall={success}")

            return success

        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False



    @property
    def is_initialized(self) -> bool:
        """Return initialization status."""
        return self._initialized


# Global unified search service instance
unified_search_service = UnifiedSearchService()
