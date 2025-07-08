"""
Factory for creating search backend instances.

This module provides a factory pattern implementation for creating vector and text search backends,
enabling easy switching between different search engines through configuration.
"""

from enum import Enum
from typing import Optional
import logging

from .interfaces.vector_search_interface import VectorSearchInterface
from .interfaces.text_search_interface import TextSearchInterface

logger = logging.getLogger(__name__)


class VectorBackendType(Enum):
    """Supported vector search backends."""
    QDRANT = "qdrant"
    MILVUS = "milvus"
    CHROMA = "chroma"
    WEAVIATE = "weaviate"


class TextBackendType(Enum):
    """Supported text search backends."""
    MEILISEARCH = "meilisearch"
    OPENSEARCH = "opensearch"
    ELASTICSEARCH = "elasticsearch"
    SOLR = "solr"


class SearchBackendFactory:
    """Factory for creating search backend instances."""
    
    @staticmethod
    def create_vector_backend(backend_type: VectorBackendType) -> VectorSearchInterface:
        """
        Create a vector search backend instance.
        
        Args:
            backend_type: Type of vector backend to create
            
        Returns:
            VectorSearchInterface implementation
            
        Raises:
            ValueError: If backend type is not supported
            ImportError: If required dependencies are not installed
        """
        try:
            if backend_type == VectorBackendType.QDRANT:
                from .vector_backends.qdrant_backend import QdrantVectorBackend
                return QdrantVectorBackend()
            
            elif backend_type == VectorBackendType.MILVUS:
                from .vector_backends.milvus_backend import MilvusVectorBackend
                return MilvusVectorBackend()
            
            elif backend_type == VectorBackendType.CHROMA:
                from .vector_backends.chroma_backend import ChromaVectorBackend
                return ChromaVectorBackend()
            
            elif backend_type == VectorBackendType.WEAVIATE:
                from .vector_backends.weaviate_backend import WeaviateVectorBackend
                return WeaviateVectorBackend()
            
            else:
                raise ValueError(f"Unsupported vector backend type: {backend_type}")
                
        except ImportError as e:
            logger.error(f"Failed to import vector backend {backend_type}: {e}")
            raise ImportError(
                f"Required dependencies for {backend_type} are not installed. "
                f"Please install the appropriate packages."
            )
    
    @staticmethod
    def create_text_backend(backend_type: TextBackendType) -> TextSearchInterface:
        """
        Create a text search backend instance.
        
        Args:
            backend_type: Type of text backend to create
            
        Returns:
            TextSearchInterface implementation
            
        Raises:
            ValueError: If backend type is not supported
            ImportError: If required dependencies are not installed
        """
        try:
            if backend_type == TextBackendType.MEILISEARCH:
                from .text_backends.meilisearch_backend import MeiliSearchTextBackend
                return MeiliSearchTextBackend()
            
            elif backend_type == TextBackendType.OPENSEARCH:
                from .text_backends.opensearch_backend import OpenSearchTextBackend
                return OpenSearchTextBackend()
            
            elif backend_type == TextBackendType.ELASTICSEARCH:
                from .text_backends.elasticsearch_backend import ElasticsearchTextBackend
                return ElasticsearchTextBackend()
            
            elif backend_type == TextBackendType.SOLR:
                from .text_backends.solr_backend import SolrTextBackend
                return SolrTextBackend()
            
            else:
                raise ValueError(f"Unsupported text backend type: {backend_type}")
                
        except ImportError as e:
            logger.error(f"Failed to import text backend {backend_type}: {e}")
            raise ImportError(
                f"Required dependencies for {backend_type} are not installed. "
                f"Please install the appropriate packages."
            )
    
    @staticmethod
    def get_available_vector_backends() -> list[str]:
        """
        Get list of available vector backends.
        
        Returns:
            List of available backend names
        """
        available = []
        
        for backend_type in VectorBackendType:
            try:
                SearchBackendFactory.create_vector_backend(backend_type)
                available.append(backend_type.value)
            except (ImportError, ValueError):
                continue
                
        return available
    
    @staticmethod
    def get_available_text_backends() -> list[str]:
        """
        Get list of available text backends.
        
        Returns:
            List of available backend names
        """
        available = []
        
        for backend_type in TextBackendType:
            try:
                SearchBackendFactory.create_text_backend(backend_type)
                available.append(backend_type.value)
            except (ImportError, ValueError):
                continue
                
        return available
    
    @staticmethod
    def validate_backend_config(vector_backend: str, text_backend: str) -> tuple[bool, Optional[str]]:
        """
        Validate backend configuration.
        
        Args:
            vector_backend: Vector backend name
            text_backend: Text backend name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate vector backend
            vector_type = VectorBackendType(vector_backend)
            SearchBackendFactory.create_vector_backend(vector_type)
        except (ValueError, ImportError) as e:
            return False, f"Invalid vector backend '{vector_backend}': {e}"
        
        try:
            # Validate text backend
            text_type = TextBackendType(text_backend)
            SearchBackendFactory.create_text_backend(text_type)
        except (ValueError, ImportError) as e:
            return False, f"Invalid text backend '{text_backend}': {e}"
        
        return True, None
