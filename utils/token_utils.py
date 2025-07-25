"""Token counting utilities for embedding models."""

import logging
from typing import List, Union, Optional, Dict, Any
import re

logger = logging.getLogger(__name__)


class TokenCounter:
    """Token counting utility using actual model tokenizers."""

    def __init__(self):
        self._model_tokenizers: Dict[str, Any] = {}

    def count_tokens_with_embedding_service(self, text: str, embedding_service, model: Optional[str] = None) -> int:
        """
        Count tokens using the embedding service's loaded model tokenizer.

        Args:
            text: Input text to count tokens for
            embedding_service: The embedding service instance
            model: Model name to use for tokenization

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        # Try to use the embedding service's loaded model tokenizer
        if embedding_service and model:
            try:
                # Get the loaded model from embedding service
                sentence_model = embedding_service.get_model(model)
                if sentence_model and hasattr(sentence_model, 'tokenizer'):
                    tokenizer = sentence_model.tokenizer
                    tokens = tokenizer.encode(text, add_special_tokens=True)
                    return len(tokens)
            except Exception as e:
                logger.warning(f"Embedding service tokenizer failed for {model}: {e}, falling back to approximation")

        # Fallback: approximate token counting
        return self._approximate_token_count(text)

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        Count tokens in text using approximation method.

        Args:
            text: Input text to count tokens for
            model: Model name (for compatibility, not used in approximation)

        Returns:
            Number of tokens
        """
        if not text:
            return 0

        # Use approximation method
        return self._approximate_token_count(text)
    
    def _approximate_token_count(self, text: str) -> int:
        """
        Approximate token counting using heuristics.
        
        This is a fallback method when tiktoken is not available.
        Based on OpenAI's approximation: ~4 characters per token for English,
        ~2-3 characters per token for Korean.
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Count Korean characters (Hangul)
        korean_chars = len(re.findall(r'[가-힣]', text))
        
        # Count other characters (excluding spaces)
        other_chars = len(text) - korean_chars - text.count(' ')
        
        # Estimate tokens: Korean chars / 2.5, other chars / 4
        korean_tokens = korean_chars / 2.5
        other_tokens = other_chars / 4
        
        # Add tokens for spaces (roughly 1 token per 4 spaces)
        space_tokens = text.count(' ') / 4
        
        return max(1, int(korean_tokens + other_tokens + space_tokens))
    
    def count_tokens_batch(self, texts: List[str], model: Optional[str] = None) -> List[int]:
        """Count tokens for a batch of texts."""
        return [self.count_tokens(text, model) for text in texts]
    
    def validate_token_limits(self, texts: Union[str, List[str]], 
                            max_tokens_per_input: int = 8192,
                            max_total_tokens: int = 1000000) -> tuple[bool, str]:
        """
        Validate token limits according to OpenAI API constraints.
        
        Args:
            texts: Input text(s) to validate
            max_tokens_per_input: Maximum tokens per individual input
            max_total_tokens: Maximum total tokens for the batch
            
        Returns:
            (is_valid, error_message)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        total_tokens = 0
        for i, text in enumerate(texts):
            token_count = self.count_tokens(text)
            total_tokens += token_count
            
            if token_count > max_tokens_per_input:
                return False, f"Input {i} exceeds maximum token limit of {max_tokens_per_input} tokens (got {token_count})"
        
        if total_tokens > max_total_tokens:
            return False, f"Total tokens exceed maximum limit of {max_total_tokens} tokens (got {total_tokens})"
        
        return True, ""


# Global token counter instance
token_counter = TokenCounter()


def count_tokens(text: str, model: Optional[str] = None) -> int:
    """Convenience function for counting tokens."""
    return token_counter.count_tokens(text, model)


def count_tokens_batch(texts: List[str], model: Optional[str] = None) -> List[int]:
    """Convenience function for counting tokens in batch."""
    return token_counter.count_tokens_batch(texts, model)


def validate_token_limits(texts: Union[str, List[str]], 
                         max_tokens_per_input: int = 8192,
                         max_total_tokens: int = 1000000) -> tuple[bool, str]:
    """Convenience function for validating token limits."""
    return token_counter.validate_token_limits(texts, max_tokens_per_input, max_total_tokens)
