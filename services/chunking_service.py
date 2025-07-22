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

    def chunk_semantic_recursive(self, text: str, chunk_size: int, overlap: int, language: str = "auto") -> List[Chunk]:
        """Chunk text with semantic awareness - improved paragraph and section detection."""
        import re

        # 1. 먼저 마크다운 구조 기반으로 섹션 분리
        sections = self._split_by_markdown_structure(text)

        all_chunks = []
        current_pos = 0

        for section in sections:
            if not section.strip():
                current_pos += len(section)
                continue

            # 2. 각 섹션 내에서 의미 기반 분리
            section_chunks = self._chunk_section_semantically(section, chunk_size, overlap, current_pos)
            all_chunks.extend(section_chunks)
            current_pos += len(section)

        return all_chunks

    def _split_by_markdown_structure(self, text: str) -> List[str]:
        """Split text by markdown structure (headers, lists, code blocks)."""
        import re

        # 마크다운 구조 패턴들
        patterns = [
            r'^#{1,6}\s+.+$',  # 헤더 (# ## ### 등)
            r'^[-*+]\s+.+$',   # 리스트 항목
            r'^[0-9]+\.\s+.+$', # 번호 리스트
            r'^```[\s\S]*?```$', # 코드 블록
            r'^>\s+.+$',       # 인용문
            r'^---+$',         # 구분선
        ]

        # 문단 분리 (빈 줄 기준)
        paragraphs = re.split(r'\n\s*\n', text)

        sections = []
        current_section = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 마크다운 구조 요소인지 확인
            is_structure = any(re.match(pattern, paragraph, re.MULTILINE) for pattern in patterns)

            # 헤더로 시작하는 경우 새 섹션 시작
            if re.match(r'^#{1,6}\s+', paragraph):
                if current_section:
                    sections.append(current_section)
                current_section = paragraph + "\n\n"
            else:
                current_section += paragraph + "\n\n"

        if current_section:
            sections.append(current_section)

        return sections if sections else [text]

    def _chunk_section_semantically(self, section: str, chunk_size: int, overlap: int, start_pos: int) -> List[Chunk]:
        """Chunk a section with semantic awareness."""
        import re

        # 문장 단위로 분리 (한국어 고려)
        sentences = self._split_sentences_advanced(section)

        chunks = []
        current_chunk = ""
        current_start = start_pos
        sentence_start = start_pos

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                sentence_start += len(sentence) + 1
                continue

            # 현재 청크에 문장을 추가했을 때의 토큰 수 계산
            test_chunk = current_chunk + (" " if current_chunk else "") + sentence
            test_tokens = self.estimate_tokens(test_chunk)

            if test_tokens <= chunk_size:
                # 청크에 추가
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    current_start = sentence_start
            else:
                # 현재 청크 완성
                if current_chunk:
                    chunks.append(Chunk(
                        text=current_chunk,
                        start_char=current_start,
                        end_char=current_start + len(current_chunk),
                        token_count=self.estimate_tokens(current_chunk)
                    ))

                # 새 청크 시작
                current_chunk = sentence
                current_start = sentence_start

            sentence_start += len(sentence) + 1

        # 마지막 청크 추가
        if current_chunk:
            chunks.append(Chunk(
                text=current_chunk,
                start_char=current_start,
                end_char=current_start + len(current_chunk),
                token_count=self.estimate_tokens(current_chunk)
            ))

        return chunks

    def _split_sentences_advanced(self, text: str) -> List[str]:
        """Advanced sentence splitting with Korean support."""
        import re

        # 한국어와 영어 문장 분리 패턴
        patterns = [
            r'[.!?]+\s+(?=[A-Z가-힣])',  # 영어/한국어 문장 끝
            r'[.!?]+\n',                 # 줄바꿈이 있는 문장 끝
            r'[。！？]+\s*',              # 한국어 문장부호
            r'\n\s*\n',                  # 문단 분리
        ]

        sentences = [text]

        for pattern in patterns:
            new_sentences = []
            for sentence in sentences:
                splits = re.split(f'({pattern})', sentence)
                current = ""
                for i, split in enumerate(splits):
                    if re.match(pattern, split):
                        current += split
                        if current.strip():
                            new_sentences.append(current.strip())
                        current = ""
                    else:
                        current += split
                if current.strip():
                    new_sentences.append(current.strip())
            sentences = new_sentences

        return [s for s in sentences if s.strip()]

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

    def _filter_chunks(self, chunks: List[Chunk], min_tokens: int = 15, min_chars: int = 50) -> List[Chunk]:
        """Filter out chunks that are too small to be meaningful."""
        filtered_chunks = []
        for chunk in chunks:
            # Skip chunks that are too small or are just headers/titles
            chunk_text = chunk.text.strip()

            # Check if it's just a markdown header (starts with # and is very short)
            is_just_header = (chunk_text.startswith('#') and
                            len(chunk_text.split('\n')) == 1 and
                            len(chunk_text) < 100)

            if (chunk.token_count >= min_tokens and
                len(chunk_text) >= min_chars and
                not is_just_header and
                chunk_text not in ['', ' ', '\n', '\t']):
                filtered_chunks.append(chunk)
            else:
                logger.debug(f"Filtered out small/header chunk: '{chunk.text[:50]}...' (tokens: {chunk.token_count}, chars: {len(chunk.text)})")

        return filtered_chunks

    def chunk_text(self, text: str, strategy: str = "token", chunk_size: int = 512,
                   overlap: int = 50, language: str = "auto") -> List[Chunk]:
        """Main chunking method."""
        if not text.strip():
            return []

        if strategy == "sentence":
            chunks = self.chunk_by_sentences(text, chunk_size, overlap, language)
        elif strategy == "recursive":
            chunks = self.chunk_recursively(text, chunk_size, overlap, language)
        elif strategy == "semantic":
            chunks = self.chunk_semantic_recursive(text, chunk_size, overlap, language)
        elif strategy == "token":
            chunks = self.chunk_by_tokens(text, chunk_size, overlap, language)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

        # Filter out chunks that are too small
        filtered_chunks = self._filter_chunks(chunks)

        logger.info(f"Chunking completed: {len(chunks)} -> {len(filtered_chunks)} chunks after filtering")
        return filtered_chunks


# Global chunking service instance
chunking_service = ChunkingService()