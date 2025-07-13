"""
Abstract interface for rerank services.

This module defines the common interface that all rerank implementations must follow,
enabling easy switching between different rerank models and strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RerankInterface(ABC):
    """Abstract base class for rerank services."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the rerank model and resources.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def rerank(self, 
                    query: str, 
                    documents: List[Dict[str, Any]], 
                    top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Re-rank documents based on their relevance to the query.
        
        Args:
            query: The search query
            documents: List of documents with 'text' and 'score' fields
            top_k: Number of top results to return (None for all)
            
        Returns:
            List of re-ranked documents with updated scores
        """
        pass
    
    @abstractmethod
    async def batch_rerank(self, 
                          queries: List[str], 
                          documents_list: List[List[Dict[str, Any]]], 
                          top_k: Optional[int] = None) -> List[List[Dict[str, Any]]]:
        """
        Re-rank multiple query-document sets in batch.
        
        Args:
            queries: List of search queries
            documents_list: List of document lists for each query
            top_k: Number of top results to return per query
            
        Returns:
            List of re-ranked document lists
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded rerank model.
        
        Returns:
            Dictionary containing model information
        """
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """
        Check if the rerank service is properly initialized.
        
        Returns:
            bool: True if initialized, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources and free memory."""
        pass


class RerankResult:
    """Container for rerank operation results."""
    
    def __init__(self, 
                 documents: List[Dict[str, Any]], 
                 processing_time: float,
                 model_name: str,
                 original_count: int):
        self.documents = documents
        self.processing_time = processing_time
        self.model_name = model_name
        self.original_count = original_count
        self.reranked_count = len(documents)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "documents": self.documents,
            "processing_time": self.processing_time,
            "model_name": self.model_name,
            "original_count": self.original_count,
            "reranked_count": self.reranked_count,
            "improvement_ratio": self.reranked_count / self.original_count if self.original_count > 0 else 0
        }
