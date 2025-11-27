## Implementation Plan: Terminal RAG Bot (TDD)

This plan assumes the existing `RAGSystem` and Qdrant/OpenAI integration are already working.

We will add a small CLI-oriented wrapper module (e.g. `rag_bot.py`) that uses `RAGSystem` to answer questions interactively.

---

### Step 1 – Define a thin query helper around `RAGSystem` (Test First)

**Goal**: Have a small, easily-testable function that, given a question string, returns a structured RAG answer (answer text + sources) using `RAGSystem`.

1. **Test**:  
   - Create a test (e.g. `tests/test_rag_bot.py`) for a pure function `answer_question(rag: RAGSystem, question: str) -> dict`.  
   - Use a fake/mocked `RAGSystem` (or a simple stub) so the test does not depend on Qdrant or OpenAI.  
   - Assert that:  
     - When the stub returns a known result, `answer_question` passes through the `answer` and `sources` correctly.  
     - When the stub indicates “no results”, `answer_question` returns a user-friendly fallback message.

2. **Implementation**:  
   - Implement `answer_question` in a new module, e.g. `rag_bot.py`, using the existing `RAGSystem.query` interface.  
   - Keep it pure and free of I/O so it’s easy to test.

3. **Refactor**:  
   - Once the test passes, clean up naming and docstrings, but keep logic minimal.

---

### Step 2 – Implement a single-turn CLI entry point (non-loop) (Test First)

**Goal**: A function that takes a question string, configures `RAGSystem`, and returns an answer dict; this will be used by the interactive loop later.

1. **Test**:  
   - Add tests for a function `run_single_query(question: str, *, collection_name: str, openai_api_key: str | None, qdrant_url: str | None, qdrant_api_key: str | None) -> dict`.  
   - Use dependency injection to pass a fake `RAGSystem` (e.g. via an optional parameter or factory) so the tests do not require network calls.  
   - Assert that:  
     - It calls `answer_question` with the right question.  
     - It handles missing/invalid configuration by raising or returning a clear error structure.

2. **Implementation**:  
   - In `rag_bot.py`, implement `run_single_query` that:  
     - Creates a real `RAGSystem` with the provided configuration (or env vars in production code).  
     - Delegates to `answer_question` and returns its result.

3. **Refactor**:  
   - Ensure environment-variable reading (e.g. `OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`) is centralized and minimal.

---

### Step 3 – Implement the interactive CLI loop (Rag Bot) (Test First where practical)

**Goal**: Create a script (`rag_bot.py` main block) that runs an interactive loop in the terminal.

1. **Test** (lightweight):  
   - Add tests for a small helper function `should_exit(user_input: str) -> bool` that returns `True` for `exit`, `quit`, or empty input, and `False` otherwise.  
   - (Optionally) use dependency injection to unit-test a loop function that reads from a fake “input provider” and writes to a fake “output sink”.

2. **Implementation**:  
   - In `rag_bot.py`, implement a `main()` that:  
     - Prints a short welcome message and basic instructions (how to exit).  
     - Reads configuration from env vars (`OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, and an optional `RAG_COLLECTION_NAME`).  
     - Enters a `while True` loop:  
       - Prompt: e.g. `RAG> `.  
       - If `should_exit(user_input)` is `True`, break gracefully.  
       - Call `run_single_query(...)` with the user’s question.  
       - Pretty-print the answer and optionally top source metadata (e.g. URL + score).  
     - Wrap the loop in a `try/except KeyboardInterrupt` to allow `Ctrl+C` to exit cleanly.

3. **Refactor**:  
   - Keep logging minimal in the interactive path; rely on `logging` module for debug/info if needed.  
   - Ensure there is a clear module-level `if __name__ == "__main__": main()` entrypoint.

---

### Step 4 – Integration and Manual Verification

**Goal**: Verify the end-to-end experience in a real environment.

1. **Run tests**:  
   - Run the test suite (for the new tests) and ensure all pass.

2. **Manual tests in terminal**:  
   - With Qdrant running and data indexed, and `OPENAI_API_KEY` set, run:  
     - `python rag_bot.py`  
   - Ask several questions like:  
     - “What is KYC Hub?”  
     - “What features does KYC Hub provide?”  
     - “How does KYC Hub help with AML compliance?”  
   - Confirm that answers are grounded in the scraped content and that exit commands work.

3. **Update documentation**:  
   - Add a short “Terminal RAG Bot” section to `README.md` with usage instructions.


