"""
Abstract interface for text search backends.

This interface defines the contract that all text search backends must implement,
enabling easy switching between different search engines like MeiliSearch, OpenSearch, Elasticsearch, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TextSearchInterface(ABC):
    """Abstract interface for text search backends."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the text search backend.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the text search backend.
        
        Returns:
            Dict containing health status information
        """
        pass
    
    @abstractmethod
    async def create_index(self, index_name: str, settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a new index for storing documents.
        
        Args:
            index_name: Name of the index
            settings: Optional index settings (schema, analyzers, etc.)
            
        Returns:
            bool: True if creation successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Index documents for text search.
        
        Args:
            documents: List of documents to index
                      Each document should have:
                      - id: unique identifier
                      - title: document title (optional)
                      - content: main text content
                      - metadata: additional searchable fields
        
        Returns:
            bool: True if indexing successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def search_text(self, 
                         query: str, 
                         limit: int = 10,
                         offset: int = 0,
                         filters: Optional[Dict[str, Any]] = None,
                         sort: Optional[List[str]] = None,
                         highlight: bool = False) -> Dict[str, Any]:
        """
        Search for documents using text query.
        
        Args:
            query: Text query string
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            filters: Optional filters to apply to the search
            sort: Optional sorting criteria
            highlight: Whether to include highlighted snippets
            
        Returns:
            Dict containing search results and metadata
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the text search index.
        
        Args:
            document_id: Unique identifier of the document to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_index(self, index_name: str) -> bool:
        """
        Delete an entire index.
        
        Args:
            index_name: Name of the index to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def update_document(self, document_id: str, 
                            document: Dict[str, Any]) -> bool:
        """
        Update a document in the text search index.
        
        Args:
            document_id: Unique identifier of the document
            document: Updated document data
            
        Returns:
            bool: True if update successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def suggest(self, query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions/autocomplete for a query.
        
        Args:
            query: Partial query string
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested query strings
        """
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID.
        
        Args:
            document_id: Unique identifier of the document
            
        Returns:
            Document data if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the text search index.
        
        Returns:
            Dict containing statistics like document count, index size, etc.
        """
        pass
    
    @abstractmethod
    async def batch_search(self, 
                         queries: List[str], 
                         limit: int = 10,
                         filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform batch text search for multiple queries.
        
        Args:
            queries: List of query strings
            limit: Maximum number of results per query
            filters: Optional filters to apply to all searches
            
        Returns:
            List of search results for each query
        """
        pass
    
    @abstractmethod
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text using the search engine's analyzer.
        
        Args:
            text: Text to analyze
            
        Returns:
            Analysis results (tokens, etc.)
        """
        pass
    
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return the name of the backend (e.g., 'meilisearch', 'opensearch')."""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the backend is connected and ready."""
        pass
