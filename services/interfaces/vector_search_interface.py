"""
Abstract interface for vector search backends.

This interface defines the contract that all vector search backends must implement,
enabling easy switching between different vector databases like Qdrant, Milvus, Chroma, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class VectorSearchInterface(ABC):
    """Abstract interface for vector search backends."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the vector search backend.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the vector search backend.
        
        Returns:
            Dict containing health status information
        """
        pass
    
    @abstractmethod
    async def create_collection(self, collection_name: str, vector_size: int) -> bool:
        """
        Create a new collection/index for storing vectors.
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimension of the vectors
            
        Returns:
            bool: True if creation successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def store_embeddings(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Store document embeddings in the vector database.
        
        Args:
            documents: List of documents with embeddings and metadata
                      Each document should have:
                      - id: unique identifier
                      - embedding: vector representation
                      - metadata: additional information
        
        Returns:
            bool: True if storage successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def search_similar(self, 
                           query_vector: List[float], 
                           limit: int = 10,
                           score_threshold: float = 0.0,
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector for similarity search
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            filters: Optional filters to apply to the search
            
        Returns:
            List of similar documents with scores and metadata
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector database.
        
        Args:
            document_id: Unique identifier of the document to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete an entire collection.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def update_document(self, document_id: str, 
                            embedding: Optional[List[float]] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a document's embedding or metadata.
        
        Args:
            document_id: Unique identifier of the document
            embedding: New embedding vector (optional)
            metadata: New metadata (optional)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dict containing statistics like document count, collection info, etc.
        """
        pass
    
    @abstractmethod
    async def batch_search(self, 
                         query_vectors: List[List[float]], 
                         limit: int = 10,
                         score_threshold: float = 0.0,
                         filters: Optional[Dict[str, Any]] = None) -> List[List[Dict[str, Any]]]:
        """
        Perform batch similarity search for multiple query vectors.
        
        Args:
            query_vectors: List of query vectors
            limit: Maximum number of results per query
            score_threshold: Minimum similarity score threshold
            filters: Optional filters to apply to all searches
            
        Returns:
            List of search results for each query vector
        """
        pass
    
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return the name of the backend (e.g., 'qdrant', 'milvus')."""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the backend is connected and ready."""
        pass
