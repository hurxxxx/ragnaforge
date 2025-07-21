"""
Qdrant vector search backend implementation.

This module provides a concrete implementation of the VectorSearchInterface
for Qdrant vector database.
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, 
    MatchValue, SearchRequest, ScrollRequest
)
import numpy as np

from ..interfaces.vector_search_interface import VectorSearchInterface
from config import settings

logger = logging.getLogger(__name__)


class QdrantVectorBackend(VectorSearchInterface):
    """Qdrant implementation of vector search backend."""
    
    def __init__(self):
        self.client = None
        self.collection_name = settings.qdrant_collection_name
        self._connected = False
        logger.info("Qdrant vector backend initialized")
    
    async def initialize(self) -> bool:
        """Initialize the Qdrant client and connection."""
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
            
            # Ensure collection exists
            await self._ensure_collection_exists()
            
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {str(e)}")
            self._connected = False
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Qdrant health status."""
        try:
            if not self.client:
                return {"status": "disconnected", "error": "Client not initialized"}
            
            collections = self.client.get_collections()
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "status": "healthy",
                "backend": "qdrant",
                "host": settings.qdrant_host,
                "port": settings.qdrant_port,
                "collections_count": len(collections.collections),
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count
            }
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "backend": "qdrant",
                "error": str(e)
            }
    
    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """Create a new collection in Qdrant."""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {str(e)}")
            return False
    
    async def _ensure_collection_exists(self):
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
    
    async def store_embeddings(self, documents: List[Dict[str, Any]]) -> bool:
        """Store document embeddings in Qdrant."""
        try:
            if not documents:
                logger.warning("No documents provided for storage")
                return True
            
            points = []
            for doc in documents:
                if not all(key in doc for key in ['id', 'embedding']):
                    logger.warning(f"Document missing required fields: {doc.keys()}")
                    continue
                
                # Create point ID
                point_id = str(uuid.uuid4()) if 'point_id' not in doc else doc['point_id']
                
                # Prepare payload (metadata)
                payload = doc.get('metadata', {})
                payload.update({
                    'document_id': doc['id'],
                    'created_at': time.time()
                })
                
                point = PointStruct(
                    id=point_id,
                    vector=doc['embedding'],
                    payload=payload
                )
                points.append(point)
            
            if not points:
                logger.warning("No valid points to store")
                return True
            
            # Batch upsert points
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Stored {len(points)} embeddings in Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error storing embeddings in Qdrant: {str(e)}")
            return False
    
    async def search_similar(self, 
                           query_vector: List[float], 
                           limit: int = 10,
                           score_threshold: float = 0.0,
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors in Qdrant."""
        try:
            # Prepare query filter
            query_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Multiple values - use should match any
                        for v in value:
                            conditions.append(FieldCondition(key=key, match=MatchValue(value=v)))
                    else:
                        conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                
                if conditions:
                    query_filter = Filter(should=conditions)
            
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
                    "metadata": result.payload
                })
            
            logger.info(f"Found {len(results)} similar vectors")
            return results

        except Exception as e:
            logger.error(f"Error searching similar vectors: {str(e)}")
            return []

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from Qdrant."""
        try:
            # Find points with matching document_id
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                ),
                limit=1000,  # Adjust based on expected chunk count per document
                with_payload=False,
                with_vectors=False
            )

            if not scroll_result[0]:
                logger.warning(f"No points found for document_id: {document_id}")
                return True

            # Delete points
            point_ids = [point.id for point in scroll_result[0]]
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids
            )

            logger.info(f"Deleted {len(point_ids)} points for document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete an entire collection."""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {str(e)}")
            return False

    async def update_document(self, document_id: str,
                            embedding: Optional[List[float]] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update a document's embedding or metadata."""
        try:
            # Find points with matching document_id
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                ),
                limit=1000,
                with_payload=True,
                with_vectors=embedding is None
            )

            if not scroll_result[0]:
                logger.warning(f"No points found for document_id: {document_id}")
                return False

            # Update points
            points = []
            for point in scroll_result[0]:
                updated_payload = point.payload.copy() if point.payload else {}
                if metadata:
                    updated_payload.update(metadata)

                updated_point = PointStruct(
                    id=point.id,
                    vector=embedding if embedding else point.vector,
                    payload=updated_payload
                )
                points.append(updated_point)

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"Updated {len(points)} points for document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating document {document_id}: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get Qdrant statistics."""
        try:
            collection_info = self.client.get_collection(self.collection_name)

            return {
                "backend": "qdrant",
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "status": collection_info.status,
                "optimizer_status": collection_info.optimizer_status,
                "disk_data_size": getattr(collection_info, 'disk_data_size', 0),
                "ram_data_size": getattr(collection_info, 'ram_data_size', 0)
            }

        except Exception as e:
            logger.error(f"Error getting Qdrant stats: {str(e)}")
            return {"backend": "qdrant", "error": str(e)}

    async def batch_search(self,
                         query_vectors: List[List[float]],
                         limit: int = 10,
                         score_threshold: float = 0.0,
                         filters: Optional[Dict[str, Any]] = None) -> List[List[Dict[str, Any]]]:
        """Perform batch similarity search."""
        try:
            # Prepare search requests
            search_requests = []
            for query_vector in query_vectors:
                query_filter = None
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if isinstance(value, list):
                            for v in value:
                                conditions.append(FieldCondition(key=key, match=MatchValue(value=v)))
                        else:
                            conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

                    if conditions:
                        query_filter = Filter(should=conditions)

                search_requests.append(SearchRequest(
                    vector=query_vector,
                    filter=query_filter,
                    limit=limit,
                    score_threshold=score_threshold,
                    with_payload=True,
                    with_vector=False
                ))

            # Perform batch search
            batch_results = self.client.search_batch(
                collection_name=self.collection_name,
                requests=search_requests
            )

            # Format results
            formatted_results = []
            for search_result in batch_results:
                results = []
                for result in search_result:
                    results.append({
                        "id": result.id,
                        "score": result.score,
                        "metadata": result.payload
                    })
                formatted_results.append(results)

            logger.info(f"Completed batch search for {len(query_vectors)} queries")
            return formatted_results

        except Exception as e:
            logger.error(f"Error in batch search: {str(e)}")
            return [[] for _ in query_vectors]

    @property
    def backend_name(self) -> str:
        """Return the backend name."""
        return "qdrant"

    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self._connected and self.client is not None
