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
- Docker (optional, for containerized setup)

## Setup Instructions

### Step 1: Clone/Navigate to Project

```bash
cd kychub
```

### Step 2: Set Up Python Virtual Environment

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Qdrant Vector Database

**Option A: Local Qdrant (Docker) - Recommended**

```bash
# Start Qdrant container
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

Verify Qdrant is running:
```bash
# Check container status
docker ps --filter name=qdrant

# Or visit in browser
# http://localhost:6333/dashboard
```

**Option B: Qdrant Cloud**

1. Sign up at https://cloud.qdrant.io/
2. Create a cluster and get your API key and cluster URL
3. Use the URL and API key in your `.env` file (see Step 5)

### Step 5: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required: OpenAI API Key for embeddings
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Qdrant Cloud configuration (if not using local Qdrant)
# QDRANT_URL=https://your-cluster.qdrant.io
# QDRANT_API_KEY=your-qdrant-api-key-here

# Optional: Custom collection name
# RAG_COLLECTION_NAME=kychub_documents
```

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key (get it from https://platform.openai.com/api-keys)

**Optional:**
- `QDRANT_URL`: Qdrant server URL (defaults to `http://localhost:6333` for local)
- `QDRANT_API_KEY`: Qdrant API key (only needed for Qdrant Cloud)
- `RAG_COLLECTION_NAME`: Collection name in Qdrant (defaults to `kychub_documents`)

## Usage

### Scraping and Storing Content in Vector Database

**Important:** Make sure your virtual environment is activated and Qdrant is running before proceeding.

#### Option 1: Full Pipeline (Recommended - Scrape + Store in One Command)

This command will scrape pages from kychub.com, chunk the text, generate embeddings, and store everything in Qdrant:

```bash
# Scrape up to 30 pages and store in vector database
python main.py --mode full --max-pages 30

# Scrape more pages (e.g., 100 pages)
python main.py --mode full --max-pages 100

# Custom chunk size and overlap
python main.py --mode full --max-pages 30 --chunk-size 500 --chunk-overlap 50
```

**What this does:**
1. Scrapes content from https://www.kychub.com/ (follows internal links)
2. Extracts text from each page (removes navigation, scripts, etc.)
3. Splits text into chunks (default: 500 tokens with 50 token overlap)
4. Generates OpenAI embeddings for each chunk
5. Stores chunks with embeddings in Qdrant vector database

#### Option 2: Step-by-Step Execution

If you prefer to run scraping and storage separately:

**Step 1: Scrape pages and save to JSON file**
```bash
python main.py --mode scrape --max-pages 30 --output-file scraped_content.json
```

**Step 2: Process JSON file and store in Qdrant**
```bash
python main.py --mode process --input-file scraped_content.json --chunk-size 500 --chunk-overlap 50
```

### Querying the RAG System

Once you have data stored in Qdrant, you can query it:

**Using main.py:**
```bash
python main.py --mode query --question "What is KYC Hub?" --top-k 5
```

**Using the interactive terminal bot:**
```bash
python rag_bot.py
```

**Using the REST API:**
```bash
# Start the API server
uvicorn api:app --reload --port 8000

# Then query via HTTP (or use the React frontend)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is KYC Hub?", "mode": "semantic"}'
```

### Command Line Options for main.py

- `--mode`: Operation mode (`scrape`, `process`, `query`, or `full`)
  - `scrape`: Only scrape pages and save to JSON file
  - `process`: Process existing JSON file and store in Qdrant
  - `query`: Query the RAG system with a question
  - `full`: Complete pipeline (scrape → process → store)
- `--max-pages`: Maximum number of pages to scrape (default: 1)
- `--chunk-size`: Size of text chunks in tokens (default: 500)
- `--chunk-overlap`: Overlap between chunks in tokens (default: 50)
- `--input-file`: Input JSON file with scraped content (required for `process` mode)
- `--output-file`: Output file for scraped content (default: `scraped_content.json`)
- `--question`: Question to ask the RAG system (required for `query` mode)
- `--top-k`: Number of top results to retrieve (default: 5)
- `--collection-name`: Qdrant collection name (default: `kychub_documents`)
- `--qdrant-url`: Qdrant server URL (overrides environment variable)
- `--qdrant-api-key`: Qdrant API key (overrides environment variable)
- `--openai-api-key`: OpenAI API key (overrides environment variable)

## Example Commands

### Scraping Examples

```bash
# Scrape 30 pages and store in vector database
python main.py --mode full --max-pages 30

# Scrape 100 pages with custom chunking
python main.py --mode full --max-pages 100 --chunk-size 1000 --chunk-overlap 100

# Only scrape (no storage)
python main.py --mode scrape --max-pages 50 --output-file my_scraped_data.json
```

### Query Examples

```bash
# What is KYC Hub?
python main.py --mode query --question "What is KYC Hub?"

# What features does it offer?
python main.py --mode query --question "What features does KYC Hub offer?" --top-k 10

# How does it help with compliance?
python main.py --mode query --question "How does KYC Hub help with compliance?"

# About AML screening
python main.py --mode query --question "Tell me about AML screening capabilities"
```

### Using Docker

If you prefer to run everything in Docker:

```bash
# Start Qdrant
docker-compose up -d qdrant

# Set OpenAI API key (PowerShell)
$env:OPENAI_API_KEY = "your-key-here"

# Run scraping and storage in Docker
docker-compose run --rm backend python main.py --mode full --max-pages 30
```

## Project Structure

```
kychub/
├── scraper.py          # Web scraping module
├── chunker.py          # Text chunking module
├── vector_store.py     # Qdrant integration and vector operations
├── bm25_retriever.py   # BM25 keyword retrieval implementation
├── rag_system.py       # RAG query system (semantic, keyword, hybrid)
├── rag_bot.py          # Interactive terminal RAG bot
├── api.py              # FastAPI REST API server
├── main.py             # Main orchestration script (scrape, process, query)
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image for backend
├── docker-compose.yml  # Docker Compose configuration
├── README.md           # This file
├── .env                # Environment variables (create this)
├── .gitignore          # Git ignore rules
└── frontend/           # React frontend application
    ├── src/
    │   ├── App.jsx     # Main React component
    │   └── styles.css  # Styling
    ├── package.json
    └── vite.config.mjs
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
- Generates embeddings using OpenAI API
- Handles document storage and semantic retrieval
- Provides method to fetch all documents for BM25 indexing

### bm25_retriever.py
- `BM25Retriever`: Implements BM25 keyword-based retrieval
- Builds BM25 index from all stored documents
- Provides keyword search functionality

### rag_system.py
- `RAGSystem`: Main RAG interface
- Supports three retrieval modes:
  - `semantic`: OpenAI embeddings + vector search
  - `keyword`: BM25 keyword search
  - `hybrid`: Combines semantic and keyword with weighted scoring
- Generates answers and returns sources with confidence scores

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

## Running the Full Stack

### Backend API Server

```bash
# Make sure Qdrant is running and .env is configured
uvicorn api:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

**Endpoints:**
- `POST /query` - Query the RAG system
  ```json
  {
    "question": "What is KYC Hub?",
    "mode": "semantic"  // or "keyword" or "hybrid"
  }
  ```
- `GET /health` - Health check

### Frontend React Application

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port Vite assigns)

**Features:**
- Interactive chat interface
- Mode selection (Semantic, Keyword, Hybrid)
- Source citations with URLs
- Real-time querying

### Using Docker Compose (All Services)

```bash
# Set OpenAI API key
$env:OPENAI_API_KEY = "your-key-here"  # PowerShell
# or
export OPENAI_API_KEY="your-key-here"  # Linux/Mac

# Start all services (Qdrant + Backend)
docker-compose up --build

# In another terminal, scrape and store data
docker-compose run --rm backend python main.py --mode full --max-pages 30
```

## Retrieval Modes

The RAG system supports three retrieval modes:

1. **Semantic** (default): Uses OpenAI embeddings and cosine similarity in Qdrant
   - Best for: Conceptual questions, understanding meaning
   - Example: "What is KYC Hub?" or "How does compliance automation work?"

2. **Keyword (BM25)**: Uses BM25 algorithm for keyword matching
   - Best for: Specific terms, exact phrase matching
   - Example: "AML screening sanctions PEPs" or "identity verification"

3. **Hybrid**: Combines semantic (60%) and keyword (40%) scores
   - Best for: General use, balances both approaches
   - Example: "How does KYC Hub help with fraud prevention?"

## Future Enhancements

- **Document Processing Service**: Introduction of a service that can consume data as PDF, Word documents and have OCR support for extracting text from images and scanned documents
- **RAG Pipeline Evaluation**: Improving the RAG pipeline using evaluations with [RAGAS.io](https://ragas.io/) to improve context recall and precision. Also deciding thresholds depending on tradeoff between precision and recall
- Add support for JavaScript-rendered content (Selenium/Playwright)
- Integrate with LLM APIs (OpenAI GPT, Anthropic Claude) for better answer generation
- Implement incremental updates (re-scrape changed pages only)
- Add support for multiple websites
- Enhanced answer generation with better prompt engineering

## License

This project is for educational and research purposes.

## Support

For issues or questions, please check the code comments or create an issue in the repository.

