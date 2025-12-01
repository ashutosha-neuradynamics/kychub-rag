from vector_store import QdrantVectorStore
from bm25_retriever import BM25Retriever
from typing import List, Dict, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGSystem:
    def __init__(
        self,
        collection_name: str = "kychub_documents",
        model_name: str = "text-embedding-3-small",
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        self.vector_store = QdrantVectorStore(
            collection_name=collection_name,
            model_name=model_name,
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            openai_api_key=openai_api_key,
        )
        # Build BM25 retriever from all stored chunks (keyword search)
        all_docs = self.vector_store.get_all_documents()
        self.bm25_retriever = BM25Retriever(all_docs) if all_docs else None

    def query(
        self,
        question: str,
        top_k: int = 5,
        min_score: float = 0.3,
        mode: str = "semantic",
    ) -> Dict[str, any]:
        if mode == "keyword":
            if self.bm25_retriever is None:
                return {
                    "question": question,
                    "answer": "No keyword index available yet. Please index documents first.",
                    "sources": [],
                    "confidence": 0.0,
                }
            filtered_results = self.bm25_retriever.search(question, top_k=top_k)
        elif mode == "hybrid":
            filtered_results = self._hybrid_search(question, top_k=top_k)
        else:
            semantic_results = self.vector_store.search(question, top_k=top_k)
            filtered_results = [
                result for result in semantic_results if result["score"] >= min_score
            ]

        if not filtered_results:
            return {
                "question": question,
                "answer": "I couldn't find relevant information to answer your question.",
                "sources": [],
                "confidence": 0.0,
            }

        context = self._format_context(filtered_results)
        answer = self._generate_answer(question, context)

        return {
            "question": question,
            "answer": answer,
            "sources": filtered_results,
            "confidence": filtered_results[0]["score"] if filtered_results else 0.0,
        }

    def _hybrid_search(self, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.bm25_retriever is None:
            return self.vector_store.search(question, top_k=top_k)

        semantic_results = self.vector_store.search(question, top_k=top_k * 2)
        keyword_results = self.bm25_retriever.search(question, top_k=top_k * 2)

        def _key(r: Dict[str, Any]) -> Any:
            return (r.get("id"), r.get("url"), r.get("chunk_index"))

        def _normalize(scores: Dict[Any, float]) -> Dict[Any, float]:
            if not scores:
                return {}
            values = list(scores.values())
            min_s, max_s = min(values), max(values)
            if max_s == min_s:
                return {k: 1.0 for k in scores}
            return {k: (v - min_s) / (max_s - min_s) for k, v in scores.items()}

        sem_scores = {_key(r): float(r["score"]) for r in semantic_results}
        kw_scores = {_key(r): float(r["score"]) for r in keyword_results}

        sem_norm = _normalize(sem_scores)
        kw_norm = _normalize(kw_scores)

        alpha = 0.6
        combined: Dict[Any, Dict[str, Any]] = {}

        base_index: Dict[Any, Dict[str, Any]] = {}
        for r in semantic_results:
            base_index[_key(r)] = r
        for r in keyword_results:
            k = _key(r)
            if k not in base_index:
                base_index[k] = r

        for k, base in base_index.items():
            sem_s = sem_norm.get(k, 0.0)
            kw_s = kw_norm.get(k, 0.0)
            score = alpha * sem_s + (1 - alpha) * kw_s
            merged = dict(base)
            merged["score"] = score
            combined[k] = merged

        sorted_results = sorted(
            combined.values(), key=lambda r: r["score"], reverse=True
        )
        return sorted_results[:top_k]

    def _format_context(self, results: List[Dict[str, any]]) -> str:
        context_parts = []
        for idx, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {idx} - {result['title']}]\n"
                f"{result['content']}\n"
                f"URL: {result['url']}\n"
            )
        return "\n".join(context_parts)

    def _generate_answer(self, question: str, context: str) -> str:
        answer = self._simple_answer_generation(question, context)
        return answer

    def _simple_answer_generation(self, question: str, context: str) -> str:
        question_lower = question.lower()

        if "what is" in question_lower or "what are" in question_lower:
            if "kyc hub" in question_lower:
                if "offer" in question_lower or "provide" in question_lower:
                    return self._extract_about_kyc_hub(context)
                return "KYC Hub is a cloud-native risk and compliance operating system that provides comprehensive KYC, KYB, AML screening, and fraud prevention solutions."

        if "how" in question_lower:
            if "work" in question_lower or "help" in question_lower:
                return self._extract_how_it_works(context)

        if "feature" in question_lower or "solution" in question_lower:
            return self._extract_features(context)

        relevant_sentences = self._extract_relevant_sentences(question, context)
        if relevant_sentences:
            return " ".join(relevant_sentences[:3])

        return f"Based on the available information: {context[:500]}..."

    def _extract_about_kyc_hub(self, context: str) -> str:
        key_phrases = [
            "KYC Hub is",
            "KYC Hub provides",
            "KYC Hub offers",
            "cloud-native",
            "compliance operating system",
        ]

        sentences = context.split(".")
        relevant = []
        for sentence in sentences:
            if any(phrase.lower() in sentence.lower() for phrase in key_phrases):
                relevant.append(sentence.strip())

        if relevant:
            return ". ".join(relevant[:2]) + "."
        return "KYC Hub is a comprehensive compliance and risk management platform."

    def _extract_how_it_works(self, context: str) -> str:
        key_phrases = ["enable", "leverage", "provides", "automate", "workflow"]

        sentences = context.split(".")
        relevant = []
        for sentence in sentences:
            if any(phrase.lower() in sentence.lower() for phrase in key_phrases):
                relevant.append(sentence.strip())

        if relevant:
            return ". ".join(relevant[:2]) + "."
        return "KYC Hub uses AI and automation to streamline compliance processes."

    def _extract_features(self, context: str) -> str:
        features = []
        feature_keywords = [
            "verification",
            "screening",
            "monitoring",
            "workflow",
            "automation",
            "risk detection",
        ]

        sentences = context.split(".")
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in feature_keywords):
                features.append(sentence.strip())

        if features:
            return ". ".join(features[:3]) + "."
        return "KYC Hub offers various features including identity verification, AML screening, and workflow automation."

    def _extract_relevant_sentences(self, question: str, context: str) -> List[str]:
        question_words = set(question.lower().split())
        sentences = context.split(".")
        scored_sentences = []

        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = len(question_words.intersection(sentence_words))
            if overlap > 0:
                scored_sentences.append((overlap, sentence.strip()))

        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        return [sentence for _, sentence in scored_sentences[:3]]

    def get_collection_stats(self) -> Dict[str, any]:
        return self.vector_store.get_collection_info()


def main():
    rag = RAGSystem()

    questions = [
        "What is KYC Hub?",
        "What features does KYC Hub offer?",
        "How does KYC Hub help with compliance?",
    ]

    for question in questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")

        result = rag.query(question, top_k=3)

        print(f"\nAnswer: {result['answer']}")
        print(f"\nConfidence: {result['confidence']:.4f}")
        print(f"\nSources ({len(result['sources'])}):")
        for idx, source in enumerate(result["sources"], 1):
            print(f"  {idx}. {source['title']} (Score: {source['score']:.4f})")
            print(f"     URL: {source['url']}")


if __name__ == "__main__":
    main()
