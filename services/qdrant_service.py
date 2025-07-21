"""Qdrant vector database service for document embeddings and search."""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, 
    MatchValue, SearchRequest, ScrollRequest
)
import numpy as np
from config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for managing document embeddings in Qdrant vector database."""
    
    def __init__(self):
        self.client = None
        self.collection_name = settings.qdrant_collection_name
        self._initialize_client()
        logger.info("Qdrant service initialized")
    
    def _initialize_client(self):
        """Initialize Qdrant client with configuration."""
        try:
            if settings.qdrant_api_key:
                self.client = QdrantClient(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                    api_key=settings.qdrant_api_key,
                    timeout=30,
                    verify=False  # For development - enable in production
                )
            else:
                self.client = QdrantClient(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                    timeout=30,
                    verify=False
                )
            
            # Test connection
            collections = self.client.get_collections()
            logger.info(f"Connected to Qdrant: {len(collections.collections)} collections")
            
            # Initialize collection if needed
            self._ensure_collection_exists()
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {str(e)}")
            raise
    
    def _ensure_collection_exists(self):
        """Ensure the main collection exists with proper configuration."""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.vector_dimension,  # 환경변수에서 설정된 벡터 차원
                        distance=Distance.COSINE
                    )
                )
                
                logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {str(e)}")
            raise
    
    def store_document_chunks(self, document_id: str, chunks: List[Dict], 
                            document_metadata: Dict) -> bool:
        """Store document chunks with embeddings in Qdrant."""
        try:
            if not chunks:
                logger.warning(f"No chunks to store for document {document_id}")
                return True
            
            points = []
            for i, chunk in enumerate(chunks):
                if "embedding" not in chunk:
                    logger.warning(f"Chunk {i} has no embedding, skipping")
                    continue

                # Generate UUID for point ID (Qdrant requirement)
                point_id = str(uuid.uuid4())
                
                # Prepare payload with metadata
                payload = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "chunk_id": f"{document_id}_chunk_{i}",  # Keep original ID for reference
                    "text": chunk["text"],
                    "token_count": chunk.get("token_count", 0),
                    "start_char": chunk.get("start_char", 0),
                    "end_char": chunk.get("end_char", 0),

                    # Document metadata
                    "filename": document_metadata.get("filename", ""),
                    "file_type": document_metadata.get("file_type", ""),
                    "conversion_method": document_metadata.get("conversion_method", ""),
                    "created_at": document_metadata.get("created_at", time.time()),

                    # Search metadata
                    "has_embedding": True,
                    "embedding_model": document_metadata.get("embedding_model", settings.default_model)
                }
                
                point = PointStruct(
                    id=point_id,
                    vector=chunk["embedding"],
                    payload=payload
                )
                points.append(point)
            
            if not points:
                logger.warning(f"No valid points to store for document {document_id}")
                return True
            
            # Batch upsert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Stored {len(points)} chunks for document {document_id} in Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error storing document chunks in Qdrant: {str(e)}")
            return False
    
    def search_similar_chunks(self, query_vector: List[float], limit: int = 10,
                            document_filter: Optional[Dict] = None,
                            score_threshold: float = 0.0) -> List[Dict]:
        """Search for similar chunks using vector similarity."""
        try:
            # Build filter if provided
            query_filter = None
            if document_filter:
                conditions = []
                
                if "document_ids" in document_filter:
                    conditions.append(
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_filter["document_ids"])
                        )
                    )
                
                if "file_types" in document_filter:
                    conditions.append(
                        FieldCondition(
                            key="file_type",
                            match=MatchValue(value=document_filter["file_types"])
                        )
                    )
                
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Perform search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            logger.info(f"Found {len(results)} similar chunks")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            return []
    
    def get_document_chunks(self, document_id: str) -> List[Dict]:
        """Get all chunks for a specific document."""
        try:
            # Scroll through all points for the document
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                ),
                with_payload=True,
                with_vectors=False,
                limit=1000  # Adjust based on expected chunk count
            )
            
            chunks = []
            for point in scroll_result[0]:  # scroll_result is (points, next_page_offset)
                chunks.append({
                    "id": point.id,
                    "payload": point.payload
                })
            
            # Sort by chunk_index
            chunks.sort(key=lambda x: x["payload"].get("chunk_index", 0))
            
            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting document chunks: {str(e)}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document."""
        try:
            # Delete points by filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            
            logger.info(f"Deleted all chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document from Qdrant: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            stats = {
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "status": collection_info.status,
                "optimizer_status": collection_info.optimizer_status,
                "disk_data_size": getattr(collection_info, 'disk_data_size', 0),
                "ram_data_size": getattr(collection_info, 'ram_data_size', 0)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def health_check(self) -> Dict:
        """Check Qdrant service health."""
        try:
            collections = self.client.get_collections()
            collection_exists = self.collection_name in [col.name for col in collections.collections]
            
            return {
                "status": "healthy",
                "connected": True,
                "collection_exists": collection_exists,
                "total_collections": len(collections.collections)
            }
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }


# Global service instance
qdrant_service = QdrantService()
