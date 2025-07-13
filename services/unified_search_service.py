"""
Unified search service that orchestrates vector and text search backends.

This service provides a high-level interface for hybrid search functionality,
abstracting away the specific backend implementations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from sklearn.preprocessing import MinMaxScaler

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
    
    async def store_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Store documents in both vector and text backends."""
        try:
            if not self._initialized:
                logger.error("Service not initialized")
                return False
            
            # Prepare documents for vector storage (with embeddings)
            vector_docs = []
            text_docs = []
            
            for doc in documents:
                # For vector backend - need embeddings
                if 'embedding' in doc:
                    vector_docs.append(doc)
                
                # For text backend - need text content
                if any(key in doc for key in ['content', 'title']):
                    text_docs.append(doc)
            
            # Store in both backends concurrently
            results = await asyncio.gather(
                self.vector_backend.store_embeddings(vector_docs) if vector_docs else True,
                self.text_backend.index_documents(text_docs) if text_docs else True,
                return_exceptions=True
            )
            
            vector_success = results[0] if not isinstance(results[0], Exception) else False
            text_success = results[1] if not isinstance(results[1], Exception) else False
            
            if isinstance(results[0], Exception):
                logger.error(f"Vector storage failed: {results[0]}")
            
            if isinstance(results[1], Exception):
                logger.error(f"Text indexing failed: {results[1]}")
            
            success = vector_success and text_success
            logger.info(f"Document storage: vector={vector_success}, text={text_success}, overall={success}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error storing documents: {str(e)}")
            return False
    
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
                search_limit = max(search_limit, limit * 2)  # Ensure we get enough results

            # Search in vector backend
            results = await self.vector_backend.search_similar(
                query_vector=query_vector,
                limit=search_limit,
                score_threshold=score_threshold,
                filters=filters
            )

            # Apply reranking if requested and enabled
            rerank_applied = False
            rerank_info = {}
            if rerank and rerank_service.is_enabled() and results:
                try:
                    # Convert results to rerank format
                    rerank_docs = []
                    for result in results:
                        doc = {
                            "id": result.get("id", ""),
                            "text": result.get("content", result.get("text", "")),
                            "score": result.get("score", 0.0),
                            "metadata": result.get("metadata", {})
                        }
                        rerank_docs.append(doc)

                    # Perform reranking
                    rerank_result = await rerank_service.rerank_documents(
                        query=query,
                        documents=rerank_docs,
                        top_k=limit,
                        use_cache=True
                    )

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
            
            return {
                "success": True,
                "results": results.get("hits", []),
                "total": results.get("total", 0),
                "search_type": "text",
                "query": query,
                "search_time": search_time,
                "backend": self.text_backend.backend_name,
                "processing_time_ms": results.get("processing_time_ms", 0)
            }
            
        except Exception as e:
            logger.error(f"Text search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "search_time": time.time() - start_time
            }

    async def hybrid_search(self,
                          query: str,
                          limit: int = 10,
                          vector_weight: float = 0.6,
                          text_weight: float = 0.4,
                          score_threshold: float = 0.0,
                          filters: Optional[Dict[str, Any]] = None,
                          embedding_model: Optional[str] = None,
                          highlight: bool = False,
                          rerank: bool = False,
                          rerank_top_k: Optional[int] = None) -> Dict[str, Any]:
        """Perform hybrid search combining vector and text search."""
        start_time = time.time()

        try:
            if not self._initialized:
                return {"success": False, "error": "Service not initialized"}

            # Validate weights
            if abs(vector_weight + text_weight - 1.0) > 0.01:
                logger.warning(f"Weights don't sum to 1.0: vector={vector_weight}, text={text_weight}")
                # Normalize weights
                total_weight = vector_weight + text_weight
                vector_weight = vector_weight / total_weight
                text_weight = text_weight / total_weight

            # Perform both searches concurrently
            vector_task = self.vector_search(
                query=query,
                limit=limit * 2,  # Get more results for better fusion
                score_threshold=score_threshold,
                filters=filters,
                embedding_model=embedding_model
            )

            text_task = self.text_search(
                query=query,
                limit=limit * 2,  # Get more results for better fusion
                filters=filters,
                highlight=highlight
            )

            vector_result, text_result = await asyncio.gather(vector_task, text_task, return_exceptions=True)

            # Handle exceptions
            if isinstance(vector_result, Exception):
                logger.error(f"Vector search failed: {vector_result}")
                vector_result = {"success": False, "results": [], "error": str(vector_result)}

            if isinstance(text_result, Exception):
                logger.error(f"Text search failed: {text_result}")
                text_result = {"success": False, "results": [], "error": str(text_result)}

            # Extract results
            vector_results = vector_result.get("results", []) if vector_result.get("success") else []
            text_results = text_result.get("results", []) if text_result.get("success") else []

            # Determine initial limit for merging (get more results if reranking)
            merge_limit = limit
            if rerank and rerank_service.is_enabled():
                merge_limit = rerank_top_k or getattr(settings, 'rerank_top_k', 100)
                merge_limit = max(merge_limit, limit * 2)  # Ensure we get enough results

            # Merge and rank results
            merged_results = self._merge_search_results(
                vector_results=vector_results,
                text_results=text_results,
                vector_weight=vector_weight,
                text_weight=text_weight,
                limit=merge_limit
            )

            # Apply reranking if requested and enabled
            rerank_applied = False
            rerank_info = {}
            if rerank and rerank_service.is_enabled() and merged_results:
                try:
                    # Convert merged results to rerank format
                    rerank_docs = []
                    for result in merged_results:
                        doc = {
                            "id": result.get("id", ""),
                            "text": result.get("content", result.get("text", "")),
                            "score": result.get("hybrid_score", result.get("score", 0.0)),
                            "metadata": result.get("metadata", {})
                        }
                        # Preserve hybrid search metadata
                        doc["metadata"]["hybrid_score"] = result.get("hybrid_score", 0.0)
                        doc["metadata"]["vector_score"] = result.get("vector_score", 0.0)
                        doc["metadata"]["text_score"] = result.get("text_score", 0.0)
                        doc["metadata"]["search_source"] = result.get("search_source", "")
                        rerank_docs.append(doc)

                    # Perform reranking
                    rerank_result = await rerank_service.rerank_documents(
                        query=query,
                        documents=rerank_docs,
                        top_k=limit,
                        use_cache=True
                    )

                    if rerank_result.get("success", False):
                        # Convert reranked results back to original format
                        reranked_results = []
                        for doc in rerank_result["documents"]:
                            # Find original result and update with rerank score
                            original_result = next(
                                (r for r in merged_results if r.get("id") == doc.get("id")),
                                None
                            )
                            if original_result:
                                updated_result = original_result.copy()
                                updated_result["score"] = doc.get("rerank_score", doc.get("score", 0.0))
                                updated_result["rerank_score"] = doc.get("rerank_score", 0.0)
                                updated_result["original_hybrid_score"] = original_result.get("hybrid_score", 0.0)
                                updated_result["rank_position"] = doc.get("rank_position", 1)
                                reranked_results.append(updated_result)

                        merged_results = reranked_results
                        rerank_applied = True
                        rerank_info = {
                            "processing_time": rerank_result.get("processing_time", 0.0),
                            "original_count": rerank_result.get("original_count", 0),
                            "reranked_count": rerank_result.get("reranked_count", 0),
                            "model_info": rerank_result.get("model_info", {}),
                            "from_cache": rerank_result.get("from_cache", False)
                        }

                        logger.info(f"Hybrid search reranking applied: {len(rerank_docs)} -> {len(merged_results)} results")

                except Exception as e:
                    logger.error(f"Hybrid search reranking failed, using original results: {str(e)}")

            search_time = time.time() - start_time

            response = {
                "success": True,
                "results": merged_results,
                "search_type": "hybrid",
                "query": query,
                "total_results": len(merged_results),
                "search_time": search_time,
                "vector_results_count": len(vector_results),
                "text_results_count": len(text_results),
                "weights": {
                    "vector": vector_weight,
                    "text": text_weight
                },
                "backends": {
                    "vector": self.vector_backend.backend_name,
                    "text": self.text_backend.backend_name
                },
                "rerank_applied": rerank_applied
            }

            # Add rerank info if applied
            if rerank_applied:
                response["rerank_info"] = rerank_info

            return response

        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "search_time": time.time() - start_time
            }

    def _merge_search_results(self,
                            vector_results: List[Dict[str, Any]],
                            text_results: List[Dict[str, Any]],
                            vector_weight: float,
                            text_weight: float,
                            limit: int) -> List[Dict[str, Any]]:
        """Merge and rank results from vector and text search."""
        try:
            # Create a mapping of document IDs to combined scores
            combined_scores = {}

            # Process vector results
            vector_scores = []
            for result in vector_results:
                doc_id = self._extract_document_id(result)
                score = result.get("score", 0.0)
                vector_scores.append(score)

                combined_scores[doc_id] = {
                    "vector_score": score,
                    "text_score": 0.0,
                    "result": result,
                    "source": "vector"
                }

            # Process text results
            text_scores = []
            for result in text_results:
                doc_id = self._extract_document_id(result)
                # Text search might not have explicit scores, use relevance
                score = self._calculate_text_relevance_score(result)
                text_scores.append(score)

                if doc_id in combined_scores:
                    # Document found in both searches
                    combined_scores[doc_id]["text_score"] = score
                    combined_scores[doc_id]["source"] = "both"
                else:
                    # Document only in text search
                    combined_scores[doc_id] = {
                        "vector_score": 0.0,
                        "text_score": score,
                        "result": result,
                        "source": "text"
                    }

            # Normalize scores to [0, 1] range
            if vector_scores:
                vector_scaler = MinMaxScaler()
                normalized_vector_scores = vector_scaler.fit_transform(np.array(vector_scores).reshape(-1, 1)).flatten()
            else:
                normalized_vector_scores = []

            if text_scores:
                text_scaler = MinMaxScaler()
                normalized_text_scores = text_scaler.fit_transform(np.array(text_scores).reshape(-1, 1)).flatten()
            else:
                normalized_text_scores = []

            # Update with normalized scores
            vector_idx = 0
            text_idx = 0

            for doc_id, data in combined_scores.items():
                if data["vector_score"] > 0 and vector_idx < len(normalized_vector_scores):
                    data["normalized_vector_score"] = normalized_vector_scores[vector_idx]
                    vector_idx += 1
                else:
                    data["normalized_vector_score"] = 0.0

                if data["text_score"] > 0 and text_idx < len(normalized_text_scores):
                    data["normalized_text_score"] = normalized_text_scores[text_idx]
                    text_idx += 1
                else:
                    data["normalized_text_score"] = 0.0

                # Calculate combined score
                data["combined_score"] = (
                    data["normalized_vector_score"] * vector_weight +
                    data["normalized_text_score"] * text_weight
                )

            # Sort by combined score and return top results
            sorted_results = sorted(
                combined_scores.values(),
                key=lambda x: x["combined_score"],
                reverse=True
            )

            # Format final results
            final_results = []
            for item in sorted_results[:limit]:
                result = item["result"].copy()
                result["hybrid_score"] = item["combined_score"]
                result["vector_score"] = item["normalized_vector_score"]
                result["text_score"] = item["normalized_text_score"]
                result["search_source"] = item["source"]
                final_results.append(result)

            return final_results

        except Exception as e:
            logger.error(f"Error merging search results: {str(e)}")
            # Fallback: return vector results if available, otherwise text results
            return (vector_results or text_results)[:limit]

    def _extract_document_id(self, result: Dict[str, Any]) -> str:
        """Extract document ID from search result."""
        # Try different possible ID fields
        for id_field in ["id", "document_id", "_id"]:
            if id_field in result:
                return str(result[id_field])

        # Try metadata
        metadata = result.get("metadata", {})
        for id_field in ["document_id", "id", "chunk_id"]:
            if id_field in metadata:
                return str(metadata[id_field])

        # Fallback to result ID
        return str(result.get("id", "unknown"))

    def _calculate_text_relevance_score(self, result: Dict[str, Any]) -> float:
        """Calculate relevance score for text search result."""
        # MeiliSearch and other engines might not provide explicit scores
        # We can use various heuristics here

        # If there's an explicit score, use it
        if "score" in result:
            return float(result["score"])

        # Otherwise, use position-based scoring (earlier results are more relevant)
        # This is a simple heuristic - in practice, you might want more sophisticated scoring
        return 1.0  # Default score for text results

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

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from both backends."""
        try:
            if not self._initialized:
                return {"error": "Service not initialized"}

            vector_stats = self.vector_backend.get_stats()
            text_stats = self.text_backend.get_stats()

            return {
                "unified_search": {
                    "initialized": self._initialized,
                    "backends": {
                        "vector": settings.vector_backend,
                        "text": settings.text_backend
                    }
                },
                "vector_backend": vector_stats,
                "text_backend": text_stats
            }

        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"error": str(e)}

    @property
    def is_initialized(self) -> bool:
        """Return initialization status."""
        return self._initialized


# Global unified search service instance
unified_search_service = UnifiedSearchService()
