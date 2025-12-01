import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag_system import RAGSystem


class QueryRequest(BaseModel):
    question: str
    mode: str | None = "semantic"  # "semantic", "keyword", or "hybrid"


class Source(BaseModel):
    score: float | None = None
    url: str | None = None
    title: str | None = None
    content: str | None = None
    chunk_index: int | None = None
    total_chunks: int | None = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    sources: List[Source]


def build_rag_from_env() -> RAGSystem:
    """
    Construct a RAGSystem instance using environment variables.
    """
    load_dotenv()

    collection_name = os.getenv("RAG_COLLECTION_NAME", "kychub_documents")
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please export it in your environment or .env file."
        )

    rag = RAGSystem(
        collection_name=collection_name,
        qdrant_url=qdrant_url,
        qdrant_api_key=qdrant_api_key,
        openai_api_key=openai_api_key,
    )
    return rag


app = FastAPI(title="KYC Hub RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


try:
    rag_system = build_rag_from_env()
except Exception as e:  # pragma: no cover - startup failure path
    # Defer raising until first request so docs still load.
    rag_system = None
    startup_error = e
else:
    startup_error = None


@app.post("/query", response_model=QueryResponse)
def query_rag(req: QueryRequest) -> Dict[str, Any]:
    """
    Query the RAG system with a natural language question.
    """
    if rag_system is None:
        raise RuntimeError(f"RAG system not initialised: {startup_error}")

    result = rag_system.query(
        req.question,
        top_k=5,
        mode=(req.mode or "semantic"),
    )
    # Ensure we only return serialisable data
    sources_clean: List[Dict[str, Any]] = []
    for src in result.get("sources", []):
        sources_clean.append(
            {
                "score": float(src.get("score")) if src.get("score") is not None else None,
                "url": src.get("url"),
                "title": src.get("title"),
                "content": src.get("content"),
                "chunk_index": src.get("chunk_index"),
                "total_chunks": src.get("total_chunks"),
            }
        )

    return {
        "question": result.get("question", req.question),
        "answer": result.get("answer", ""),
        "confidence": float(result.get("confidence", 0.0)),
        "sources": sources_clean,
    }


@app.get("/health")
def health() -> Dict[str, str]:
    """
    Simple health-check endpoint.
    """
    status = "ok" if rag_system is not None else "error"
    return {"status": status}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


