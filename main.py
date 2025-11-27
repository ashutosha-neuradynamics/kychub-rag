import argparse
import json
import os
from scraper import KychubScraper
from chunker import TextChunker
from vector_store import QdrantVectorStore
from rag_system import RAGSystem
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def scrape_website(max_pages: int = 1, output_file: str = None):
    logger.info("Starting web scraping...")
    scraper = KychubScraper()
    content = scraper.scrape_site(max_pages=max_pages)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        logger.info(f"Scraped content saved to {output_file}")

    logger.info(f"Scraped {len(content)} pages")
    return content


def process_and_store(
    documents: list,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    collection_name: str = "kychub_documents",
    qdrant_url: str = None,
    qdrant_api_key: str = None,
    openai_api_key: str = None,
):
    logger.info("Processing documents and creating chunks...")
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.chunk_documents(documents)

    logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")

    logger.info("Storing chunks in Qdrant...")
    vector_store = QdrantVectorStore(
        collection_name=collection_name,
        qdrant_url=qdrant_url,
        qdrant_api_key=qdrant_api_key,
        openai_api_key=openai_api_key,
    )

    vector_store.add_documents(chunks)

    info = vector_store.get_collection_info()
    if info:
        logger.info(f"Collection stats: {info['points_count']} points stored")

    return chunks


def query_rag(
    question: str,
    top_k: int = 5,
    collection_name: str = "kychub_documents",
    qdrant_url: str = None,
    qdrant_api_key: str = None,
    openai_api_key: str = None,
):
    logger.info(f"Querying RAG system with: {question}")
    rag = RAGSystem(
        collection_name=collection_name,
        qdrant_url=qdrant_url,
        qdrant_api_key=qdrant_api_key,
        openai_api_key=openai_api_key,
    )

    result = rag.query(question, top_k=top_k)

    print(f"\n{'='*60}")
    print(f"Question: {result['question']}")
    print(f"{'='*60}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nConfidence Score: {result['confidence']:.4f}")
    print(f"\nSources ({len(result['sources'])}):")
    for idx, source in enumerate(result["sources"], 1):
        print(f"\n  {idx}. {source['title']}")
        print(f"     Score: {source['score']:.4f}")
        print(f"     URL: {source['url']}")
        print(f"     Content: {source['content'][:200]}...")

    return result


def main():
    parser = argparse.ArgumentParser(description="KYC Hub Web Scraping and RAG System")
    parser.add_argument(
        "--mode",
        choices=["scrape", "process", "query", "full"],
        default="full",
        help="Operation mode",
    )
    parser.add_argument(
        "--max-pages", type=int, default=1, help="Maximum pages to scrape"
    )
    parser.add_argument(
        "--chunk-size", type=int, default=500, help="Chunk size for text splitting"
    )
    parser.add_argument(
        "--chunk-overlap", type=int, default=50, help="Overlap between chunks"
    )
    parser.add_argument(
        "--input-file", type=str, help="Input JSON file with scraped content"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="scraped_content.json",
        help="Output file for scraped content",
    )
    parser.add_argument("--question", type=str, help="Question to ask the RAG system")
    parser.add_argument(
        "--top-k", type=int, default=5, help="Number of top results to retrieve"
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="kychub_documents",
        help="Qdrant collection name",
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        help="Qdrant server URL (default: http://localhost:6333)",
    )
    parser.add_argument("--qdrant-api-key", type=str, help="Qdrant API key (optional)")
    parser.add_argument(
        "--openai-api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)",
    )

    args = parser.parse_args()

    qdrant_url = args.qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = args.qdrant_api_key or os.getenv("QDRANT_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if args.mode == "scrape":
        scrape_website(max_pages=args.max_pages, output_file=args.output_file)

    elif args.mode == "process":
        if not args.input_file:
            logger.error("--input-file is required for process mode")
            return

        with open(args.input_file, "r", encoding="utf-8") as f:
            documents = json.load(f)

        process_and_store(
            documents=documents,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            collection_name=args.collection_name,
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            openai_api_key=openai_api_key,
        )

    elif args.mode == "query":
        if not args.question:
            logger.error("--question is required for query mode")
            return

        query_rag(
            question=args.question,
            top_k=args.top_k,
            collection_name=args.collection_name,
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            openai_api_key=openai_api_key,
        )

    elif args.mode == "full":
        logger.info("Running full pipeline: scrape -> process -> store")

        documents = scrape_website(
            max_pages=args.max_pages, output_file=args.output_file
        )

        if documents:
            process_and_store(
                documents=documents,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                collection_name=args.collection_name,
                qdrant_url=qdrant_url,
                qdrant_api_key=qdrant_api_key,
                openai_api_key=openai_api_key,
            )

            if args.question:
                query_rag(
                    question=args.question,
                    top_k=args.top_k,
                    collection_name=args.collection_name,
                    qdrant_url=qdrant_url,
                    qdrant_api_key=qdrant_api_key,
                    openai_api_key=openai_api_key,
                )
        else:
            logger.error("No documents scraped. Cannot proceed with processing.")


if __name__ == "__main__":
    main()
