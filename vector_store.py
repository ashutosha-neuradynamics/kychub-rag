from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from typing import List, Dict, Optional, Any
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_EMBEDDING_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


class QdrantVectorStore:
    def __init__(
        self,
        collection_name: str = "kychub_documents",
        model_name: str = "text-embedding-3-small",
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        self.collection_name = collection_name
        self.model_name = model_name
        self.embedding_dim = OPENAI_EMBEDDING_DIMS.get(
            model_name, OPENAI_EMBEDDING_DIMS["text-embedding-3-small"]
        )

        openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass openai_api_key parameter."
            )

        self.openai_client = OpenAI(api_key=openai_api_key)

        qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")

        if qdrant_api_key:
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        else:
            self.client = QdrantClient(url=qdrant_url)

        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim, distance=Distance.COSINE
                    ),
                )
                logger.info("Created collection: %s", self.collection_name)
            else:
                logger.info("Collection %s already exists", self.collection_name)
        except Exception as e:
            logger.error("Error ensuring collection: %s", str(e))
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self.openai_client.embeddings.create(
                    model=self.model_name, input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                logger.info(
                    "Generated embeddings for batch %d/%d",
                    (i // batch_size) + 1,
                    (len(texts) + batch_size - 1) // batch_size,
                )
            except Exception as e:
                logger.error("Error generating embeddings for batch: %s", str(e))
                raise

        return embeddings

    def add_documents(self, documents: List[Dict[str, Any]]):
        if not documents:
            logger.warning("No documents to add")
            return

        texts = [doc["content"] for doc in documents]
        embeddings = self.generate_embeddings(texts)

        points = []
        for idx, (doc, embedding) in enumerate(zip(documents, embeddings)):
            point = PointStruct(
                id=hash(doc.get("id", f"doc_{idx}")) % (2**63),
                vector=embedding,
                payload={
                    "url": doc.get("url", ""),
                    "title": doc.get("title", ""),
                    "content": doc.get("content", ""),
                    "chunk_index": doc.get("chunk_index", 0),
                    "total_chunks": doc.get("total_chunks", 1),
                },
            )
            points.append(point)

        try:
            self.client.upsert(collection_name=self.collection_name, points=points)
            logger.info("Successfully added %d documents to Qdrant", len(points))
        except Exception as e:
            logger.error("Error adding documents: %s", str(e))
            raise

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            response = self.openai_client.embeddings.create(
                model=self.model_name, input=[query]
            )
            query_embedding = response.data[0].embedding
        except Exception as e:
            logger.error("Error generating query embedding: %s", str(e))
            raise

        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
            )

            search_results = []
            for result in results:
                search_results.append(
                    {
                        "id": result.id,
                        "score": result.score,
                        "url": result.payload.get("url", ""),
                        "title": result.payload.get("title", ""),
                        "content": result.payload.get("content", ""),
                        "chunk_index": result.payload.get("chunk_index", 0),
                        "total_chunks": result.payload.get("total_chunks", 1),
                    }
                )

            return search_results
        except Exception as e:
            logger.error("Error searching: %s", str(e))
            raise

    def get_all_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        documents: List[Dict[str, Any]] = []
        offset = None

        while True:
            points, offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            if not points:
                break

            for p in points:
                payload = p.payload or {}
                documents.append(
                    {
                        "id": p.id,
                        "url": payload.get("url", ""),
                        "title": payload.get("title", ""),
                        "content": payload.get("content", ""),
                        "chunk_index": payload.get("chunk_index", 0),
                        "total_chunks": payload.get("total_chunks", 1),
                    }
                )

                if limit is not None and len(documents) >= limit:
                    return documents

            if offset is None:
                break

        return documents

    def delete_collection(self):
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info("Deleted collection: %s", self.collection_name)
        except Exception as e:
            logger.error("Error deleting collection: %s", str(e))
            raise

    def get_collection_info(self):
        """
        Return basic collection stats without parsing full config.
        Uses `count` API to avoid compatibility issues between client and server.
        """
        try:
            count_resp = self.client.count(self.collection_name, exact=True)
            points_count = getattr(count_resp, "count", None)
            if points_count is None:
                return {"name": self.collection_name}
            return {
                "name": self.collection_name,
                "points_count": points_count,
                "vectors_count": points_count,
            }
        except Exception as e:
            logger.error("Error getting collection info: %s", str(e))
            return None


def main():
    import os

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    vector_store = QdrantVectorStore(openai_api_key=openai_api_key)

    test_docs = [
        {
            "id": "test_1",
            "url": "https://www.kychub.com/test",
            "title": "Test Document",
            "content": "This is a test document about KYC Hub and compliance solutions.",
            "chunk_index": 0,
            "total_chunks": 1,
        }
    ]

    vector_store.add_documents(test_docs)

    results = vector_store.search("KYC compliance", top_k=3)
    print(f"\nSearch results:")
    for result in results:
        print(f"Score: {result['score']:.4f}")
        print(f"Title: {result['title']}")
        print(f"Content: {result['content'][:100]}...\n")


if __name__ == "__main__":
    main()
