"""Search service for RAG functionality using unified search architecture."""

import logging
import time
from typing import Dict, List, Optional, Any
from services.qdrant_service import qdrant_service
from services import embedding_service
from config import settings

logger = logging.getLogger(__name__)


class SearchService:
    """Service for semantic search and RAG functionality."""

    def __init__(self):
        self._unified_service = None
        logger.info("Search service initialized")

    @property
    def unified_service(self):
        """Lazy load unified search service."""
        if self._unified_service is None:
            from services.unified_search_service import unified_search_service
            self._unified_service = unified_search_service
        return self._unified_service
    
    async def vector_search(self, query: str, limit: int = 10,
                          score_threshold: float = 0.0,
                          document_filter: Optional[Dict] = None,
                          embedding_model: Optional[str] = None) -> Dict:
        """Perform vector similarity search using unified search service."""
        try:
            # Use unified search service if available and initialized
            if self.unified_service.is_initialized:
                logger.info(f"Using unified search service for vector search: '{query[:50]}...'")
                result = await self.unified_service.vector_search(
                    query=query,
                    limit=limit,
                    score_threshold=score_threshold,
                    filters=document_filter,
                    embedding_model=embedding_model
                )
                return result
            else:
                # Fallback to direct Qdrant search
                logger.warning("Unified search service not initialized, falling back to direct Qdrant search")
                return await self._fallback_vector_search(query, limit, score_threshold, document_filter, embedding_model)

        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            # Fallback to direct Qdrant search
            return await self._fallback_vector_search(query, limit, score_threshold, document_filter, embedding_model)

    async def _fallback_vector_search(self, query: str, limit: int = 10,
                                    score_threshold: float = 0.0,
                                    document_filter: Optional[Dict] = None,
                                    embedding_model: Optional[str] = None) -> Dict:
        """Fallback vector search using direct Qdrant access."""
        start_time = time.time()

        try:
            # Use default model if not specified
            model = embedding_model or settings.default_model

            # Generate query embedding
            logger.info(f"Generating embedding for query: '{query[:50]}...'")
            query_embeddings = embedding_service.encode_texts([query], model)

            if query_embeddings is None or len(query_embeddings) == 0:
                return {
                    "success": False,
                    "error": "Failed to generate query embedding",
                    "search_time": time.time() - start_time
                }

            # Convert numpy array to list
            query_vector = query_embeddings[0].tolist() if hasattr(query_embeddings[0], 'tolist') else list(query_embeddings[0])

            # Search in Qdrant
            logger.info(f"Searching Qdrant with limit={limit}, threshold={score_threshold}")
            search_results = qdrant_service.search_similar_chunks(
                query_vector=query_vector,
                limit=limit,
                document_filter=document_filter,
                score_threshold=score_threshold
            )
            
            # Format results
            formatted_results = []
            for result in search_results:
                payload = result["payload"]
                
                formatted_result = {
                    "id": result["id"],
                    "score": result["score"],
                    "document_id": payload.get("document_id", ""),
                    "chunk_index": payload.get("chunk_index", 0),
                    "text": payload.get("text", ""),
                    "filename": payload.get("filename", ""),
                    "file_type": payload.get("file_type", ""),
                    "metadata": {
                        "token_count": payload.get("token_count", 0),
                        "start_char": payload.get("start_char", 0),
                        "end_char": payload.get("end_char", 0),
                        "conversion_method": payload.get("conversion_method", ""),
                        "created_at": payload.get("created_at", 0),
                        "embedding_model": payload.get("embedding_model", "")
                    }
                }
                formatted_results.append(formatted_result)
            
            search_time = time.time() - start_time
            
            logger.info(f"Vector search completed: {len(formatted_results)} results in {search_time:.3f}s")
            
            return {
                "success": True,
                "query": query,
                "total_results": len(formatted_results),
                "search_time": search_time,
                "results": formatted_results
            }
            
        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"Vector search failed: {str(e)}")
            return {
                "success": False,
                "query": query,
                "total_results": 0,
                "search_time": search_time,
                "results": [],
                "error": str(e)
            }
    
    def get_document_chunks_from_qdrant(self, document_id: str) -> List[Dict]:
        """Get all chunks for a document from Qdrant."""
        try:
            chunks = qdrant_service.get_document_chunks(document_id)
            
            formatted_chunks = []
            for chunk in chunks:
                payload = chunk["payload"]
                formatted_chunk = {
                    "id": chunk["id"],
                    "chunk_index": payload.get("chunk_index", 0),
                    "text": payload.get("text", ""),
                    "token_count": payload.get("token_count", 0),
                    "start_char": payload.get("start_char", 0),
                    "end_char": payload.get("end_char", 0),
                    "metadata": {
                        "filename": payload.get("filename", ""),
                        "file_type": payload.get("file_type", ""),
                        "conversion_method": payload.get("conversion_method", ""),
                        "created_at": payload.get("created_at", 0),
                        "embedding_model": payload.get("embedding_model", "")
                    }
                }
                formatted_chunks.append(formatted_chunk)
            
            return formatted_chunks
            
        except Exception as e:
            logger.error(f"Error getting document chunks from Qdrant: {str(e)}")
            return []
    
    def delete_document_from_qdrant(self, document_id: str) -> bool:
        """Delete document from Qdrant."""
        try:
            success = qdrant_service.delete_document(document_id)
            if success:
                logger.info(f"Document deleted from Qdrant: {document_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting document from Qdrant: {str(e)}")
            return False
    
    async def hybrid_search(self, query: str, limit: int = 10,
                          vector_weight: float = 0.7,
                          text_weight: float = 0.3,
                          document_filter: Optional[Dict] = None) -> Dict:
        """
        Perform hybrid search combining vector similarity and text matching.
        """
        try:
            # Use unified search service if available and initialized
            if self.unified_service.is_initialized:
                logger.info(f"Using unified search service for hybrid search: '{query[:50]}...'")
                result = await self.unified_service.hybrid_search(
                    query=query,
                    limit=limit,
                    vector_weight=vector_weight,
                    text_weight=text_weight,
                    filters=document_filter
                )
                return result
            else:
                # Fallback to vector search only
                logger.warning("Unified search service not initialized, falling back to vector search only")
                return await self.vector_search(
                    query=query,
                    limit=limit,
                    document_filter=document_filter
                )

        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            # Fallback to vector search
            return await self.vector_search(
                query=query,
                limit=limit,
                document_filter=document_filter
            )
    
    def get_search_stats(self) -> Dict:
        """Get search-related statistics."""
        try:
            qdrant_stats = qdrant_service.get_collection_stats()
            
            stats = {
                "vector_database": {
                    "status": "connected",
                    "collection_name": qdrant_stats.get("collection_name", ""),
                    "total_chunks": qdrant_stats.get("points_count", 0),
                    "indexed_vectors": qdrant_stats.get("indexed_vectors_count", 0),
                    "disk_size_mb": qdrant_stats.get("disk_data_size", 0) / (1024 * 1024),
                    "ram_size_mb": qdrant_stats.get("ram_data_size", 0) / (1024 * 1024)
                },
                "search_capabilities": {
                    "vector_search": True,
                    "hybrid_search": self.unified_service.is_initialized,
                    "full_text_search": self.unified_service.is_initialized
                },
                "embedding_models": {
                    "default_model": settings.default_model,
                    "available_models": ["nlpai-lab/KURE-v1", "nlpai-lab/KoE5"]
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting search stats: {str(e)}")
            return {
                "vector_database": {"status": "error", "error": str(e)},
                "search_capabilities": {"vector_search": False},
                "embedding_models": {"default_model": settings.default_model}
            }


# Global service instance
search_service = SearchService()
