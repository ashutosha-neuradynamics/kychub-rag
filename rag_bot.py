import argparse
import os
from typing import Dict, Any

from dotenv import load_dotenv

from rag_system import RAGSystem


def answer_question(rag: RAGSystem, question: str) -> Dict[str, Any]:
    """
    Thin wrapper around RAGSystem.query to make testing and reuse easier.
    """
    return rag.query(question, top_k=5)


def should_exit(text: str) -> bool:
    """
    Return True if the user input indicates the session should terminate.
    """
    if text is None:
        return True
    stripped = text.strip().lower()
    if not stripped:
        return True
    return stripped in {"exit", "quit", "q"}


def build_rag_from_env(
    collection_name: str | None = None,
    qdrant_url: str | None = None,
    qdrant_api_key: str | None = None,
    openai_api_key: str | None = None,
) -> RAGSystem:
    """
    Construct a RAGSystem instance using explicit parameters or environment variables.
    """
    load_dotenv()

    collection_name = collection_name or os.getenv("RAG_COLLECTION_NAME", "kychub_documents")
    qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
    openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive terminal RAG bot over KYC Hub content stored in Qdrant."
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default=None,
        help="Qdrant collection name (default: kychub_documents or RAG_COLLECTION_NAME env var)",
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        default=None,
        help="Qdrant URL (default: QDRANT_URL env var or http://localhost:6333)",
    )
    parser.add_argument(
        "--qdrant-api-key",
        type=str,
        default=None,
        help="Qdrant API key (default: QDRANT_API_KEY env var)",
    )
    parser.add_argument(
        "--openai-api-key",
        type=str,
        default=None,
        help="OpenAI API key (default: OPENAI_API_KEY env var)",
    )

    args = parser.parse_args()

    try:
        rag = build_rag_from_env(
            collection_name=args.collection_name,
            qdrant_url=args.qdrant_url,
            qdrant_api_key=args.qdrant_api_key,
            openai_api_key=args.openai_api_key,
        )
    except Exception as e:
        print(f"Error initialising RAG system: {e}")
        return

    print("\nKYC Hub RAG Bot (terminal)")
    print("-" * 40)
    print("Type your question and press Enter.")
    print("Type 'exit', 'quit', or just press Enter to leave.\n")

    try:
        while True:
            try:
                user_input = input("RAG> ")
            except EOFError:
                # e.g. Ctrl+D
                print("\nExiting.")
                break

            if should_exit(user_input):
                print("Goodbye.")
                break

            question = user_input.strip()
            if not question:
                continue

            try:
                result = answer_question(rag, question)
            except Exception as e:
                print(f"\nError querying RAG system: {e}\n")
                continue

            answer = result.get("answer") or "No answer generated."
            sources = result.get("sources") or []

            print("\nAnswer:\n")
            print(answer)

            if sources:
                print("\nSources:")
                for idx, src in enumerate(sources[:3], 1):
                    title = src.get("title") or "(no title)"
                    url = src.get("url") or "(no url)"
                    score = src.get("score")
                    if score is not None:
                        print(f"  {idx}. {title}  [score={score:.4f}]")
                    else:
                        print(f"  {idx}. {title}")
                    print(f"     {url}")
            print()

    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye.")


if __name__ == "__main__":
    main()


