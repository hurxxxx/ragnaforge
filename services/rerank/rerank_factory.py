"""
Factory for creating rerank service instances.

This module provides a factory pattern implementation for creating different
types of rerank services, enabling easy switching between models through configuration.
"""

from enum import Enum
from typing import Optional, Dict, Any
import logging

from .rerank_interface import RerankInterface
from config import settings

logger = logging.getLogger(__name__)


class RerankModelType(Enum):
    """Supported rerank model types."""
    BGE_M3_KO = "bge_m3_ko"
    BGE_RERANKER = "bge_reranker"
    CUSTOM = "custom"


class RerankFactory:
    """Factory for creating rerank service instances."""
    
    @staticmethod
    def create_reranker(
        model_type: RerankModelType = RerankModelType.BGE_M3_KO,
        model_name: Optional[str] = None,
        **kwargs
    ) -> RerankInterface:
        """
        Create a rerank service instance.
        
        Args:
            model_type: Type of rerank model to create
            model_name: Specific model name (overrides default)
            **kwargs: Additional arguments for the reranker
            
        Returns:
            RerankInterface: Initialized rerank service instance
            
        Raises:
            ValueError: If model type is not supported
            ImportError: If required dependencies are not installed
        """
        try:
            if model_type == RerankModelType.BGE_M3_KO:
                from .bge_reranker import BGEReranker
                
                # Use provided model name or default
                default_model = getattr(settings, 'rerank_model', 'dragonkue/bge-reranker-v2-m3-ko')
                final_model_name = model_name or default_model
                
                # Get batch size from settings or kwargs
                batch_size = kwargs.get('batch_size') or getattr(settings, 'rerank_batch_size', 32)
                
                return BGEReranker(
                    model_name=final_model_name,
                    batch_size=batch_size,
                    **{k: v for k, v in kwargs.items() if k != 'batch_size'}
                )
            
            elif model_type == RerankModelType.BGE_RERANKER:
                from .bge_reranker import BGEReranker
                
                # Generic BGE reranker with custom model
                final_model_name = model_name or "BAAI/bge-reranker-v2-m3"
                batch_size = kwargs.get('batch_size', 32)
                
                return BGEReranker(
                    model_name=final_model_name,
                    batch_size=batch_size,
                    **{k: v for k, v in kwargs.items() if k != 'batch_size'}
                )
            
            elif model_type == RerankModelType.CUSTOM:
                if not model_name:
                    raise ValueError("Custom rerank model requires model_name parameter")
                
                from .bge_reranker import BGEReranker
                
                # Try to use BGE reranker with custom model
                batch_size = kwargs.get('batch_size', 32)
                
                return BGEReranker(
                    model_name=model_name,
                    batch_size=batch_size,
                    **{k: v for k, v in kwargs.items() if k != 'batch_size'}
                )
            
            else:
                raise ValueError(f"Unsupported rerank model type: {model_type}")
                
        except ImportError as e:
            logger.error(f"Failed to import rerank dependencies: {str(e)}")
            raise ImportError(
                f"Required dependencies for {model_type} are not installed. "
                f"Please install sentence-transformers and torch."
            )
        except Exception as e:
            logger.error(f"Failed to create reranker: {str(e)}")
            raise
    
    @staticmethod
    def get_available_models() -> Dict[str, Dict[str, Any]]:
        """
        Get information about available rerank models.
        
        Returns:
            Dictionary mapping model types to their information
        """
        return {
            "bge_m3_ko": {
                "name": "BGE Reranker v2 M3 Korean",
                "model_id": "dragonkue/bge-reranker-v2-m3-ko",
                "description": "Korean-optimized cross-encoder reranker",
                "language": "Korean",
                "type": "cross_encoder",
                "framework": "sentence_transformers"
            },
            "bge_reranker": {
                "name": "BGE Reranker v2 M3",
                "model_id": "BAAI/bge-reranker-v2-m3",
                "description": "Multilingual cross-encoder reranker",
                "language": "Multilingual",
                "type": "cross_encoder",
                "framework": "sentence_transformers"
            }
        }
    
    @staticmethod
    def create_default_reranker(**kwargs) -> RerankInterface:
        """
        Create a reranker using default settings.
        
        Args:
            **kwargs: Additional arguments for the reranker
            
        Returns:
            RerankInterface: Default rerank service instance
        """
        # Get default model type from settings
        default_model_type = getattr(settings, 'rerank_model_type', 'bge_m3_ko')
        
        try:
            model_type = RerankModelType(default_model_type)
        except ValueError:
            logger.warning(f"Unknown rerank model type: {default_model_type}, using BGE M3 KO")
            model_type = RerankModelType.BGE_M3_KO
        
        return RerankFactory.create_reranker(model_type, **kwargs)


# Convenience function for easy access
def create_reranker(model_type: str = "bge_m3_ko", **kwargs) -> RerankInterface:
    """
    Convenience function to create a reranker.
    
    Args:
        model_type: String representation of model type
        **kwargs: Additional arguments
        
    Returns:
        RerankInterface: Rerank service instance
    """
    try:
        model_enum = RerankModelType(model_type)
        return RerankFactory.create_reranker(model_enum, **kwargs)
    except ValueError:
        logger.warning(f"Unknown model type: {model_type}, using default")
        return RerankFactory.create_default_reranker(**kwargs)
