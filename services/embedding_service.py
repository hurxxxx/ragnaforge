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
            "dragonkue/snowflake-arctic-embed-l-v2.0-ko": {
                "id": "dragonkue/snowflake-arctic-embed-l-v2.0-ko",
                "owned_by": "dragonkue",
                "created": int(time.time()),
                "description": "Snowflake Arctic Embed L v2.0 Korean - High-performance multilingual embedding model optimized for Korean"
            },
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
                # GPU 최적화 설정
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Using device: {device}")

                if device == "cuda":
                    # GPU 메모리 최적화
                    torch.cuda.empty_cache()
                    logger.info(f"GPU memory before loading: {torch.cuda.memory_allocated() / 1024**3:.2f}GB")

                model = SentenceTransformer(
                    model_name,
                    cache_folder=settings.cache_dir,
                    device=device
                )

                # GPU 최적화 설정 적용
                if device == "cuda":
                    model.to(device)
                    if settings.torch_cudnn_benchmark:
                        torch.backends.cudnn.benchmark = True
                    logger.info(f"GPU memory after loading: {torch.cuda.memory_allocated() / 1024**3:.2f}GB")

                self._models[model_name] = model
                logger.info(f"Successfully loaded model: {model_name} on {device}")
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

    def encode_texts(self, texts: List[str], model_name: Optional[str] = None, batch_size: Optional[int] = None) -> np.ndarray:
        """Encode texts to embeddings with optimized batch processing and GPU memory management."""
        model = self.get_model(model_name)
        target_model = model_name or settings.default_model

        # 배치 크기 최적화
        if batch_size is None:
            batch_size = min(settings.optimal_batch_size, len(texts))

        # Handle KoE5 prefix requirement
        if target_model == "nlpai-lab/KoE5":
            processed_texts = [f"query: {text}" for text in texts]
        else:
            processed_texts = texts

        # GPU 메모리 부족 시 배치 크기를 동적으로 줄이는 재시도 로직
        original_batch_size = batch_size
        retry_count = 0
        max_retries = 3

        while retry_count <= max_retries:
            try:
                # GPU 메모리 모니터링
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info(f"GPU 메모리 상태 - 할당됨: {torch.cuda.memory_allocated() / 1024**3:.2f}GB, "
                              f"예약됨: {torch.cuda.memory_reserved() / 1024**3:.2f}GB")

                logger.info(f"임베딩 생성 시도 - 배치 크기: {batch_size}, 텍스트 수: {len(processed_texts)}")

                embeddings = model.encode(
                    processed_texts,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,  # API에서는 진행바 비활성화
                    device=model.device if hasattr(model, 'device') else None
                )

                # GPU 메모리 정리
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                if retry_count > 0:
                    logger.info(f"임베딩 생성 성공 - 재시도 {retry_count}회 후 배치 크기 {batch_size}로 성공")

                return embeddings

            except torch.cuda.OutOfMemoryError as e:
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f"GPU 메모리 부족으로 최대 재시도 횟수 초과: {str(e)}")
                    raise

                # 배치 크기를 절반으로 줄임
                batch_size = max(1, batch_size // 2)
                logger.warning(f"GPU 메모리 부족 감지 - 배치 크기를 {batch_size}로 줄여서 재시도 ({retry_count}/{max_retries})")

                # GPU 메모리 정리
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                continue

            except Exception as e:
                logger.error(f"Failed to encode texts with model {target_model}: {str(e)}")
                # GPU 메모리 정리 (오류 시에도)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
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

    def get_memory_info(self) -> dict:
        """Get current memory usage information."""
        info = {
            "loaded_models": list(self._models.keys()),
            "current_model": self._current_model
        }

        if torch.cuda.is_available():
            info.update({
                "gpu_available": True,
                "gpu_memory_allocated": f"{torch.cuda.memory_allocated() / 1024**3:.2f}GB",
                "gpu_memory_reserved": f"{torch.cuda.memory_reserved() / 1024**3:.2f}GB",
                "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f}GB",
                "gpu_device_name": torch.cuda.get_device_name(0)
            })
        else:
            info["gpu_available"] = False

        return info

    def cleanup_memory(self):
        """Clean up GPU memory."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU memory cache cleared")

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
