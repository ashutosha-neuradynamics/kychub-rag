## Feature: Terminal RAG Bot for KYC Hub Knowledge

### Goal
Provide an interactive command-line “RAG bot” that lets a user type natural-language questions and receive answers grounded only in the content scraped from `https://www.kychub.com/` and stored in Qdrant.

### Functional Requirements
- **Interactive loop**:  
  - Run in the terminal as a script (e.g. `python rag_bot.py`).  
  - Continuously prompt the user for a question until the user exits.  
  - Support simple exit commands such as `exit`, `quit`, or an empty line.
- **RAG-backed answers**:  
  - For each user question, call the existing `RAGSystem` to retrieve relevant chunks from Qdrant and generate an answer.  
  - Display the final answer clearly in the terminal.  
  - Optionally show basic metadata (e.g. top source URL and score) so the user can see where the answer came from.
- **Configuration**:  
  - Reuse the existing Qdrant and OpenAI configuration (`QDRANT_URL`, `QDRANT_API_KEY`, `OPENAI_API_KEY`) via environment variables or `.env`.  
  - Allow overriding the collection name with a command-line flag or sensible default (e.g. `kychub_documents`).
- **Error handling**:  
  - If Qdrant is unreachable or empty, print a clear, user-friendly message instead of crashing.  
  - If the RAG system reports no relevant results, return a graceful “no answer found” message.  
  - Handle keyboard interrupts (`Ctrl+C`) by exiting cleanly.

### Non-Functional Requirements
- **Usability**:  
  - Clear, minimal terminal UI (prompt text, separators) suitable for quick experimentation.  
  - No excessive logging noise in normal usage (keep detailed logs via `logging` if enabled, but default output should be clean).
- **Dependencies**:  
  - Reuse existing project dependencies; do not introduce heavy new libraries just for the CLI.  
  - The script should run inside the existing virtual environment.
- **Security**:  
  - Do not hard-code API keys in the script.  
  - Rely on environment variables or `.env` loading (already in the project).

### Out of Scope (for this feature)
- Web UI or GUI chat interface.  
- Streaming token-by-token answers.  
- Multi-user session management or conversation history persistence beyond the current session.


