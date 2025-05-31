"""Chunking service for text processing."""

import re
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk."""
    text: str
    start_char: int
    end_char: int
    token_count: int


class ChunkingService:
    """Handles text chunking with multiple strategies."""

    def __init__(self):
        self._kss_available = False
        self._nltk_available = False
        self._tiktoken_available = False

        # Try to import optional dependencies
        try:
            import kss
            self._kss = kss
            self._kss_available = True
            logger.info("KSS (Korean Sentence Splitter) loaded successfully")
        except ImportError:
            logger.warning("KSS not available. Korean sentence splitting will use fallback method.")

        try:
            import nltk
            self._nltk = nltk
            self._nltk_available = True
            # Download required NLTK data if not present
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                logger.info("Downloading NLTK punkt tokenizer...")
                nltk.download('punkt', quiet=True)
            logger.info("NLTK loaded successfully")
        except ImportError:
            logger.warning("NLTK not available. English sentence splitting will use fallback method.")

        try:
            import tiktoken
            self._tiktoken = tiktoken
            self._tiktoken_available = True
            logger.info("TikToken loaded successfully")
        except ImportError:
            logger.warning("TikToken not available. Token counting will use approximation.")

    def detect_language(self, text: str) -> str:
        """Detect if text is primarily Korean or English."""
        korean_chars = len(re.findall(r'[가-힣]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = korean_chars + english_chars

        if total_chars == 0:
            return "en"  # Default to English for non-alphabetic text

        korean_ratio = korean_chars / total_chars
        return "ko" if korean_ratio > 0.3 else "en"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        if self._tiktoken_available:
            try:
                # Use cl100k_base encoding (GPT-4 tokenizer) as approximation
                encoding = self._tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            except Exception as e:
                logger.warning(f"TikToken estimation failed: {e}")

        # Fallback: rough approximation
        # Korean: ~1.5 chars per token, English: ~4 chars per token
        korean_chars = len(re.findall(r'[가-힣]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        other_chars = len(text) - korean_chars - english_chars

        estimated_tokens = (korean_chars / 1.5) + (english_chars / 4) + (other_chars / 3)
        return max(1, int(estimated_tokens))

    def split_sentences(self, text: str, language: str = "auto") -> List[str]:
        """Split text into sentences based on language."""
        if language == "auto":
            language = self.detect_language(text)

        if language == "ko" and self._kss_available:
            try:
                return self._kss.split_sentences(text)
            except Exception as e:
                logger.warning(f"KSS sentence splitting failed: {e}")

        if language == "en" and self._nltk_available:
            try:
                return self._nltk.sent_tokenize(text)
            except Exception as e:
                logger.warning(f"NLTK sentence splitting failed: {e}")

        # Fallback: simple regex-based sentence splitting
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_by_sentences(self, text: str, chunk_size: int, overlap: int, language: str = "auto") -> List[Chunk]:
        """Chunk text by sentences."""
        sentences = self.split_sentences(text, language)
        chunks = []
        current_chunk = ""
        current_start = 0

        for sentence in sentences:
            sentence_tokens = self.estimate_tokens(sentence)
            current_tokens = self.estimate_tokens(current_chunk)

            # If adding this sentence would exceed chunk_size, finalize current chunk
            if current_chunk and (current_tokens + sentence_tokens) > chunk_size:
                chunk_end = current_start + len(current_chunk)
                chunks.append(Chunk(
                    text=current_chunk.strip(),
                    start_char=current_start,
                    end_char=chunk_end,
                    token_count=current_tokens
                ))

                # Start new chunk with overlap
                if overlap > 0 and chunks:
                    overlap_text = self._get_overlap_text(current_chunk, overlap)
                    current_chunk = overlap_text + " " + sentence
                    current_start = chunk_end - len(overlap_text)
                else:
                    current_chunk = sentence
                    current_start = text.find(sentence, current_start)
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    current_start = text.find(sentence)

        # Add final chunk
        if current_chunk.strip():
            chunks.append(Chunk(
                text=current_chunk.strip(),
                start_char=current_start,
                end_char=current_start + len(current_chunk),
                token_count=self.estimate_tokens(current_chunk)
            ))

        return chunks

    def chunk_recursively(self, text: str, chunk_size: int, overlap: int, language: str = "auto") -> List[Chunk]:
        """Chunk text recursively by different separators."""
        separators = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]

        def _split_text(text: str, separators: List[str]) -> List[Chunk]:
            if not separators or self.estimate_tokens(text) <= chunk_size:
                return [Chunk(
                    text=text,
                    start_char=0,
                    end_char=len(text),
                    token_count=self.estimate_tokens(text)
                )]

            separator = separators[0]
            remaining_separators = separators[1:]

            if separator not in text:
                return _split_text(text, remaining_separators)

            splits = text.split(separator)
            chunks = []
            current_pos = 0

            for split in splits:
                if split:
                    split_chunks = _split_text(split, remaining_separators)
                    for chunk in split_chunks:
                        chunk.start_char += current_pos
                        chunk.end_char += current_pos
                        chunks.append(chunk)
                current_pos += len(split) + len(separator)

            return chunks

        return _split_text(text, separators)

    def chunk_by_tokens(self, text: str, chunk_size: int, overlap: int, language: str = "auto") -> List[Chunk]:
        """Chunk text by token count."""
        # Simple implementation: split by words and group by token count
        words = text.split()
        chunks = []
        current_chunk_words = []
        current_tokens = 0
        start_pos = 0

        for word in words:
            word_tokens = self.estimate_tokens(word)

            if current_tokens + word_tokens > chunk_size and current_chunk_words:
                # Finalize current chunk
                chunk_text = " ".join(current_chunk_words)
                end_pos = text.find(current_chunk_words[-1], start_pos) + len(current_chunk_words[-1])

                chunks.append(Chunk(
                    text=chunk_text,
                    start_char=start_pos,
                    end_char=end_pos,
                    token_count=current_tokens
                ))

                # Handle overlap
                if overlap > 0:
                    overlap_words = self._get_overlap_words(current_chunk_words, overlap)
                    current_chunk_words = overlap_words + [word]
                    current_tokens = sum(self.estimate_tokens(w) for w in current_chunk_words)
                    start_pos = end_pos - len(" ".join(overlap_words))
                else:
                    current_chunk_words = [word]
                    current_tokens = word_tokens
                    start_pos = text.find(word, end_pos)
            else:
                current_chunk_words.append(word)
                current_tokens += word_tokens

        # Add final chunk
        if current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            end_pos = start_pos + len(chunk_text)
            chunks.append(Chunk(
                text=chunk_text,
                start_char=start_pos,
                end_char=end_pos,
                token_count=current_tokens
            ))

        return chunks

    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Get overlap text from the end of current chunk."""
        words = text.split()
        overlap_words = []
        current_tokens = 0

        for word in reversed(words):
            word_tokens = self.estimate_tokens(word)
            if current_tokens + word_tokens > overlap_tokens:
                break
            overlap_words.insert(0, word)
            current_tokens += word_tokens

        return " ".join(overlap_words)

    def _get_overlap_words(self, words: List[str], overlap_tokens: int) -> List[str]:
        """Get overlap words from the end of current chunk."""
        overlap_words = []
        current_tokens = 0

        for word in reversed(words):
            word_tokens = self.estimate_tokens(word)
            if current_tokens + word_tokens > overlap_tokens:
                break
            overlap_words.insert(0, word)
            current_tokens += word_tokens

        return overlap_words

    def chunk_text(self, text: str, strategy: str = "sentence", chunk_size: int = 512,
                   overlap: int = 50, language: str = "auto") -> List[Chunk]:
        """Main chunking method."""
        if not text.strip():
            return []

        if strategy == "sentence":
            return self.chunk_by_sentences(text, chunk_size, overlap, language)
        elif strategy == "recursive":
            return self.chunk_recursively(text, chunk_size, overlap, language)
        elif strategy == "token":
            return self.chunk_by_tokens(text, chunk_size, overlap, language)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")


# Global chunking service instance
chunking_service = ChunkingService()