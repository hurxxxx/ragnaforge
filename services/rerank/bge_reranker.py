"""
BGE Reranker implementation using dragonkue/bge-reranker-v2-m3-ko model.

This module provides Korean-optimized cross-encoder reranking capabilities
using the BGE (BAAI General Embedding) reranker model.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
import logging
import torch
import numpy as np
from sentence_transformers import CrossEncoder

from .rerank_interface import RerankInterface, RerankResult
from config import settings

logger = logging.getLogger(__name__)


class BGEReranker(RerankInterface):
    """BGE-based reranker implementation for Korean text."""
    
    def __init__(self, 
                 model_name: str = "dragonkue/bge-reranker-v2-m3-ko",
                 device: Optional[str] = None,
                 batch_size: int = 32):
        """
        Initialize BGE Reranker.
        
        Args:
            model_name: Name of the BGE reranker model
            device: Device to run the model on (auto-detect if None)
            batch_size: Batch size for processing
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[CrossEncoder] = None
        self._initialized = False
        
        logger.info(f"Initializing BGE Reranker with model: {model_name}")
        logger.info(f"Target device: {self.device}")
    
    async def initialize(self) -> bool:
        """Initialize the BGE reranker model."""
        try:
            start_time = time.time()
            logger.info(f"Loading BGE reranker model: {self.model_name}")
            
            # Load model in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                self._load_model
            )
            
            # Move to specified device
            if hasattr(self.model, 'model'):
                self.model.model.to(self.device)
            
            load_time = time.time() - start_time
            logger.info(f"BGE reranker model loaded successfully in {load_time:.2f}s")
            logger.info(f"Model device: {self.device}")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize BGE reranker: {str(e)}")
            self._initialized = False
            return False
    
    def _load_model(self) -> CrossEncoder:
        """Load the CrossEncoder model (runs in thread)."""
        return CrossEncoder(
            self.model_name,
            device=self.device,
            trust_remote_code=True
        )
    
    async def rerank(self, 
                    query: str, 
                    documents: List[Dict[str, Any]], 
                    top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Re-rank documents based on query relevance.
        
        Args:
            query: Search query
            documents: List of documents with 'text' field and optional 'score'
            top_k: Number of top results to return
            
        Returns:
            List of re-ranked documents with updated scores
        """
        if not self._initialized or self.model is None:
            logger.warning("BGE reranker not initialized, returning original documents")
            return documents[:top_k] if top_k else documents
        
        if not documents:
            return []
        
        start_time = time.time()
        
        try:
            # Prepare query-document pairs
            pairs = []
            for doc in documents:
                text = doc.get('text', doc.get('content', ''))
                if text:
                    pairs.append([query, text])
            
            if not pairs:
                logger.warning("No valid text found in documents")
                return documents[:top_k] if top_k else documents
            
            # Get rerank scores
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,
                self._predict_scores,
                pairs
            )
            
            # Combine documents with new scores
            reranked_docs = []
            for i, (doc, score) in enumerate(zip(documents, scores)):
                new_doc = doc.copy()
                new_doc['rerank_score'] = float(score)
                new_doc['original_score'] = doc.get('score', 0.0)
                new_doc['rank_position'] = i + 1
                reranked_docs.append(new_doc)
            
            # Sort by rerank score (descending)
            reranked_docs.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            # Update final rankings
            for i, doc in enumerate(reranked_docs):
                doc['final_rank'] = i + 1
                doc['score'] = doc['rerank_score']  # Update main score
            
            # Apply top_k limit
            result_docs = reranked_docs[:top_k] if top_k else reranked_docs
            
            processing_time = time.time() - start_time
            logger.info(f"Reranked {len(documents)} documents in {processing_time:.3f}s")
            
            return result_docs
            
        except Exception as e:
            logger.error(f"Error during reranking: {str(e)}")
            # Return original documents on error
            return documents[:top_k] if top_k else documents
    
    def _predict_scores(self, pairs: List[List[str]]) -> np.ndarray:
        """Predict rerank scores for query-document pairs."""
        return self.model.predict(pairs, batch_size=self.batch_size)
    
    async def batch_rerank(self, 
                          queries: List[str], 
                          documents_list: List[List[Dict[str, Any]]], 
                          top_k: Optional[int] = None) -> List[List[Dict[str, Any]]]:
        """Batch rerank multiple query-document sets."""
        if len(queries) != len(documents_list):
            raise ValueError("Number of queries must match number of document lists")
        
        results = []
        for query, documents in zip(queries, documents_list):
            reranked = await self.rerank(query, documents, top_k)
            results.append(reranked)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get BGE reranker model information."""
        return {
            "model_name": self.model_name,
            "model_type": "cross_encoder",
            "framework": "sentence_transformers",
            "device": self.device,
            "batch_size": self.batch_size,
            "initialized": self._initialized,
            "supports_korean": True,
            "supports_multilingual": True
        }
    
    def is_initialized(self) -> bool:
        """Check if the reranker is initialized."""
        return self._initialized and self.model is not None
    
    async def cleanup(self) -> None:
        """Clean up model resources."""
        try:
            if self.model is not None:
                # Clear model from memory
                del self.model
                self.model = None
            
            # Clear GPU cache if using CUDA
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self._initialized = False
            logger.info("BGE reranker resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error during BGE reranker cleanup: {str(e)}")
