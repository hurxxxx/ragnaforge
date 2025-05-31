"""Embedding service for KURE models."""

import logging
import time
from typing import Dict, List, Optional
from sentence_transformers import SentenceTransformer
import torch
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Manages KURE embedding models and provides embedding functionality."""

    def __init__(self):
        self._models: Dict[str, SentenceTransformer] = {}
        self._current_model: Optional[str] = None
        self._model_info = {
            "nlpai-lab/KURE-v1": {
                "id": "nlpai-lab/KURE-v1",
                "owned_by": "nlpai-lab",
                "created": int(time.time()),
                "description": "KURE v1 - Korean University Retrieval Embedding model"
            },
            "nlpai-lab/KoE5": {
                "id": "nlpai-lab/KoE5",
                "owned_by": "nlpai-lab",
                "created": int(time.time()),
                "description": "KoE5 - Korean E5 embedding model (requires prefix)"
            }
        }

    def load_model(self, model_name: str) -> SentenceTransformer:
        """Load a model if not already loaded."""
        if model_name not in settings.available_models:
            raise ValueError(f"Model {model_name} not available. Available models: {settings.available_models}")

        if model_name not in self._models:
            logger.info(f"Loading model: {model_name}")
            try:
                model = SentenceTransformer(
                    model_name,
                    cache_folder=settings.cache_dir
                )
                self._models[model_name] = model
                logger.info(f"Successfully loaded model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}")
                raise

        self._current_model = model_name
        return self._models[model_name]

    def get_model(self, model_name: Optional[str] = None) -> SentenceTransformer:
        """Get a loaded model."""
        target_model = model_name or settings.default_model

        if target_model not in self._models:
            return self.load_model(target_model)

        self._current_model = target_model
        return self._models[target_model]

    def encode_texts(self, texts: List[str], model_name: Optional[str] = None) -> np.ndarray:
        """Encode texts to embeddings."""
        model = self.get_model(model_name)
        target_model = model_name or settings.default_model

        # Handle KoE5 prefix requirement
        if target_model == "nlpai-lab/KoE5":
            # For KoE5, we need to add prefixes
            # Assuming these are queries by default, but this could be configurable
            processed_texts = [f"query: {text}" for text in texts]
        else:
            processed_texts = texts

        try:
            embeddings = model.encode(
                processed_texts,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode texts with model {target_model}: {str(e)}")
            raise

    def calculate_similarity(self, texts: List[str], model_name: Optional[str] = None) -> np.ndarray:
        """Calculate similarity matrix between texts."""
        embeddings = self.encode_texts(texts, model_name)

        # Calculate cosine similarity matrix
        similarity_matrix = np.dot(embeddings, embeddings.T)

        return similarity_matrix

    def get_available_models(self) -> List[dict]:
        """Get list of available models."""
        return [
            {
                "id": model_id,
                "object": "model",
                "created": info["created"],
                "owned_by": info["owned_by"]
            }
            for model_id, info in self._model_info.items()
            if model_id in settings.available_models
        ]

    def is_model_loaded(self, model_name: Optional[str] = None) -> bool:
        """Check if a model is loaded."""
        target_model = model_name or settings.default_model
        return target_model in self._models

    def get_current_model(self) -> Optional[str]:
        """Get currently active model."""
        return self._current_model

    def unload_model(self, model_name: str):
        """Unload a model to free memory."""
        if model_name in self._models:
            del self._models[model_name]
            if self._current_model == model_name:
                self._current_model = None
            logger.info(f"Unloaded model: {model_name}")


# Global embedding service instance
embedding_service = EmbeddingService()
