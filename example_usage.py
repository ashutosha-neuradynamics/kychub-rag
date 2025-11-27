"""
Example usage script for the KYC Hub RAG system.

This script demonstrates how to use the system step by step.
"""

from scraper import KychubScraper
from chunker import TextChunker
from vector_store import QdrantVectorStore
from rag_system import RAGSystem


def example_scrape():
    print("=" * 60)
    print("Example 1: Scraping the website")
    print("=" * 60)

    scraper = KychubScraper()
    content = scraper.scrape_site(max_pages=5)

    print(f"\nScraped {len(content)} pages")
    for item in content[:2]:
        print(f"\n- {item['title']}")
        print(f"  URL: {item['url']}")
        print(f"  Content length: {len(item['content'])} chars")

    return content


def example_chunking(documents):
    print("\n" + "=" * 60)
    print("Example 2: Chunking documents")
    print("=" * 60)

    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    chunks = chunker.chunk_documents(documents)

    print(f"\nCreated {len(chunks)} chunks from {len(documents)} documents")
    print(f"\nSample chunk:")
    if chunks:
        print(f"  Content: {chunks[0]['content'][:200]}...")
        print(f"  Chunk {chunks[0]['chunk_index'] + 1} of {chunks[0]['total_chunks']}")

    return chunks


def example_store(chunks):
    print("\n" + "=" * 60)
    print("Example 3: Storing in Qdrant")
    print("=" * 60)

    import os

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("\nError: OPENAI_API_KEY environment variable not set")
        return

    vector_store = QdrantVectorStore(openai_api_key=openai_api_key)
    vector_store.add_documents(chunks)

    info = vector_store.get_collection_info()
    if info:
        print(f"\nCollection stats:")
        print(f"  Points stored: {info['points_count']}")
        print(f"  Vectors: {info['vectors_count']}")


def example_query():
    print("\n" + "=" * 60)
    print("Example 4: Querying the RAG system")
    print("=" * 60)

    import os

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("\nError: OPENAI_API_KEY environment variable not set")
        return

    rag = RAGSystem(openai_api_key=openai_api_key)

    questions = [
        "What is KYC Hub?",
        "What features does KYC Hub offer?",
    ]

    for question in questions:
        print(f"\n{'─' * 60}")
        print(f"Q: {question}")
        print(f"{'─' * 60}")

        result = rag.query(question, top_k=3)

        print(f"\nA: {result['answer']}")
        print(f"\nConfidence: {result['confidence']:.4f}")
        print(f"\nSources ({len(result['sources'])}):")
        for idx, source in enumerate(result["sources"], 1):
            print(f"  {idx}. {source['title']} (score: {result['confidence']:.4f})")


if __name__ == "__main__":
    print("\nKYC Hub RAG System - Example Usage\n")

    try:
        documents = example_scrape()

        if documents:
            chunks = example_chunking(documents)

            if chunks:
                example_store(chunks)
                example_query()
        else:
            print("\nNo documents scraped. Cannot proceed with examples.")

    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nMake sure:")
        print("  1. You have internet connection")
        print("  2. Qdrant is running (docker run -p 6333:6333 qdrant/qdrant)")
        print("  3. All dependencies are installed (pip install -r requirements.txt)")
