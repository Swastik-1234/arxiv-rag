import logging
from typing import List

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500  # words per chunk
CHUNK_OVERLAP = 100  # overlapping words between chunks


class TextChunker:
    """Splits paper text into overlapping chunks."""

    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, arxiv_id: str) -> List[dict]:
        """
        Split text into overlapping chunks.

        Args:
            text: Full paper text
            arxiv_id: Paper ID for metadata

        Returns:
            List of chunks with metadata
        """
        if not text or not text.strip():
            return []

        words = text.split()
        chunks = []
        chunk_index = 0
        start = 0

        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            chunks.append(
                {
                    "arxiv_id": arxiv_id,
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "word_count": len(chunk_words),
                    "start_word": start,
                    "end_word": min(end, len(words)),
                }
            )

            chunk_index += 1
            start += self.chunk_size - self.overlap

            # stop if we've covered all words
            if end >= len(words):
                break

        logger.info(f"Split paper {arxiv_id} into {len(chunks)} chunks")
        return chunks


text_chunker = TextChunker()
