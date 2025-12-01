from typing import List, Dict, Any

from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return text.lower().split()


class BM25Retriever:
    def __init__(self, documents: List[Dict[str, Any]]):
        self.documents = documents
        self.corpus_tokens = [
            _tokenize(doc.get("content", "")) for doc in documents
        ]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.documents:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results: List[Dict[str, Any]] = []
        for idx, score in indexed_scores[:top_k]:
            doc = self.documents[idx]
            result = {
                "id": doc.get("id"),
                "score": float(score),
                "url": doc.get("url", ""),
                "title": doc.get("title", ""),
                "content": doc.get("content", ""),
                "chunk_index": doc.get("chunk_index", 0),
                "total_chunks": doc.get("total_chunks", 1),
            }
            results.append(result)

        return results


