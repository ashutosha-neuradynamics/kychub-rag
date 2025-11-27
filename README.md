# KYC Hub Web Scraping and RAG System

A comprehensive system for scraping content from KYC Hub's website, storing it in a Qdrant vector database, and building a Retrieval-Augmented Generation (RAG) system for querying the content.

## Features

- **Web Scraping**: Automatically scrapes content from kychub.com with intelligent link following
- **Text Chunking**: Splits documents into manageable chunks with configurable overlap
- **Vector Storage**: Stores embeddings in Qdrant vector database
- **RAG System**: Query the scraped content using semantic search and retrieval

## Prerequisites

- Python 3.8 or higher
- Qdrant server (local or cloud)
- OpenAI API key (for embeddings)

## Installation

1. Clone or navigate to the project directory:
```bash
cd kychub
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Qdrant:

   **Option A: Local Qdrant (Docker)**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

   **Option B: Qdrant Cloud**
   - Sign up at https://cloud.qdrant.io/
   - Get your API key and cluster URL
   - Set environment variables (see Configuration section)

## Configuration

Create a `.env` file in the project root:

```env
# Required: OpenAI API Key for embeddings
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Qdrant Cloud configuration (if not using local Qdrant)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key-here
```

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key (required for generating embeddings)

**Optional:**
- `QDRANT_URL`: Qdrant server URL (defaults to `http://localhost:6333` for local)
- `QDRANT_API_KEY`: Qdrant API key (only needed for Qdrant Cloud)

## Usage

### Full Pipeline (Scrape → Process → Store)

Run the complete pipeline to scrape the website and store it in Qdrant:

```bash
python main.py --mode full --max-pages 30
```

### Step-by-Step Execution

1. **Scrape only:**
```bash
python main.py --mode scrape --max-pages 30 --output-file scraped_content.json
```

2. **Process and store:**
```bash
python main.py --mode process --input-file scraped_content.json --chunk-size 500 --chunk-overlap 50
```

3. **Query the RAG system:**
```bash
python main.py --mode query --question "What is KYC Hub?" --top-k 5
```

### Command Line Options

- `--mode`: Operation mode (`scrape`, `process`, `query`, or `full`)
- `--max-pages`: Maximum number of pages to scrape (default: 30)
- `--chunk-size`: Size of text chunks in tokens (default: 500)
- `--chunk-overlap`: Overlap between chunks in tokens (default: 50)
- `--input-file`: Input JSON file with scraped content
- `--output-file`: Output file for scraped content (default: `scraped_content.json`)
- `--question`: Question to ask the RAG system
- `--top-k`: Number of top results to retrieve (default: 5)
- `--collection-name`: Qdrant collection name (default: `kychub_documents`)
- `--qdrant-url`: Qdrant server URL
- `--qdrant-api-key`: Qdrant API key

## Example Queries

```bash
# What is KYC Hub?
python main.py --mode query --question "What is KYC Hub?"

# What features does it offer?
python main.py --mode query --question "What features does KYC Hub offer?"

# How does it help with compliance?
python main.py --mode query --question "How does KYC Hub help with compliance?"

# About AML screening
python main.py --mode query --question "Tell me about AML screening capabilities"
```

## Project Structure

```
kychub/
├── scraper.py          # Web scraping module
├── chunker.py          # Text chunking module
├── vector_store.py     # Qdrant integration
├── rag_system.py       # RAG query system
├── main.py             # Main orchestration script
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .env               # Environment variables (optional)
```

## Module Details

### scraper.py
- `KychubScraper`: Scrapes content from kychub.com
- Handles link following, content extraction, and deduplication
- Removes navigation, scripts, and other non-content elements

### chunker.py
- `TextChunker`: Splits documents into chunks
- Uses token-based chunking with configurable overlap
- Preserves sentence boundaries

### vector_store.py
- `QdrantVectorStore`: Manages Qdrant operations
- Generates embeddings using sentence-transformers
- Handles document storage and retrieval

### rag_system.py
- `RAGSystem`: Main RAG interface
- Performs semantic search and generates answers
- Returns sources and confidence scores

## Customization

### Change Embedding Model

Edit `vector_store.py` and `rag_system.py` to use a different OpenAI model:

```python
vector_store = QdrantVectorStore(model_name="text-embedding-3-large")
```

Available OpenAI models:
- `text-embedding-3-small` (default, 1536 dimensions, cost-effective)
- `text-embedding-3-large` (3072 dimensions, higher quality)
- `text-embedding-ada-002` (1536 dimensions, older model)

### Adjust Chunking Strategy

Modify chunk size and overlap in `chunker.py` or via command line:

```bash
python main.py --chunk-size 1000 --chunk-overlap 100
```

## Troubleshooting

### Qdrant Connection Issues

- Ensure Qdrant is running: `docker ps` (for local)
- Check Qdrant URL and API key in `.env` file
- Verify network connectivity

### Empty Search Results

- Ensure documents are stored: Check collection stats
- Lower the `min_score` threshold in `rag_system.py`
- Increase `top_k` parameter

### Scraping Issues

- Some pages may require JavaScript rendering (not handled by this scraper)
- Check robots.txt compliance
- Adjust `max_pages` if timeout occurs

## Future Enhancements

- Add support for JavaScript-rendered content (Selenium/Playwright)
- Integrate with LLM APIs (OpenAI, Anthropic) for better answer generation
- Add web UI for querying
- Implement incremental updates
- Add support for multiple websites
- Enhanced answer generation with better prompt engineering

## License

This project is for educational and research purposes.

## Support

For issues or questions, please check the code comments or create an issue in the repository.

