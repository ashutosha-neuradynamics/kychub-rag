from typing import List, Dict
import tiktoken


class TextChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        if self.encoding:
            return len(self.encoding.encode(text))
        return len(text.split())

    def split_text(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            if current_size + sentence_tokens > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)

                if self.chunk_overlap > 0:
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = (
                        [overlap_text, sentence] if overlap_text else [sentence]
                    )
                    current_size = self.count_tokens(" ".join(current_chunk))
                else:
                    current_chunk = [sentence]
                    current_size = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_size += sentence_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        import re

        sentence_endings = r"[.!?]\s+"
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap_text(self, chunk: List[str]) -> str:
        if not chunk:
            return ""

        overlap_sentences = []
        overlap_size = 0

        for sentence in reversed(chunk):
            sentence_tokens = self.count_tokens(sentence)
            if overlap_size + sentence_tokens <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                overlap_size += sentence_tokens
            else:
                break

        return " ".join(overlap_sentences)

    def chunk_documents(self, documents: List[Dict[str, str]]) -> List[Dict[str, any]]:
        chunked_docs = []

        for doc in documents:
            url = doc.get("url", "")
            title = doc.get("title", "")
            content = doc.get("content", "")

            if not content:
                continue

            chunks = self.split_text(content)

            for idx, chunk in enumerate(chunks):
                chunked_docs.append(
                    {
                        "id": f"{url}_{idx}",
                        "url": url,
                        "title": title,
                        "content": chunk,
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                    }
                )

        return chunked_docs


def main():
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)

    test_docs = [
        {
            "url": "https://www.kychub.com/",
            "title": "KYC Hub Home",
            "content": "This is a test document. It contains multiple sentences. Each sentence should be properly handled. The chunker should split this into appropriate chunks. Overlap should be maintained between chunks.",
        }
    ]

    chunks = chunker.chunk_documents(test_docs)
    print(f"Created {len(chunks)} chunks from {len(test_docs)} documents")
    for chunk in chunks:
        print(f"\nChunk {chunk['chunk_index']}: {chunk['content'][:100]}...")


if __name__ == "__main__":
    main()
