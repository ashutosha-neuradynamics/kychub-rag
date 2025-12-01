import React, { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mode, setMode] = useState("semantic");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setError("");
    setLoading(true);
    setInput("");

    const userMessage = { role: "user", text: question };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ question, mode })
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();
      const answerMessage = {
        role: "assistant",
        text: data.answer,
        sources: data.sources || []
      };

      setMessages((prev) => [...prev, answerMessage]);
    } catch (err) {
      console.error(err);
      setError("Failed to get answer from RAG API. Check backend and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="chat-container">
        <header className="chat-header">
          <h1>KYC Hub RAG Chat</h1>
          <div className="chat-header-sub">
            <p>Ask questions grounded in content from kychub.com</p>
            <div className="mode-switch">
              <label htmlFor="mode-select">Mode</label>
              <select
                id="mode-select"
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                disabled={loading}
              >
                <option value="semantic">Semantic</option>
                <option value="keyword">Keyword (BM25)</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </div>
          </div>
        </header>

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              <p>Start by asking a question about KYC Hub, e.g.:</p>
              <ul>
                <li>What is KYC Hub?</li>
                <li>What solutions does KYC Hub provide?</li>
                <li>How does KYC Hub help with AML and fraud?</li>
              </ul>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`chat-message ${msg.role === "user" ? "user" : "assistant"}`}
            >
              <div className="chat-message-role">
                {msg.role === "user" ? "You" : "RAG Bot"}
              </div>
              <div className="chat-message-text">{msg.text}</div>
              {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                <div className="chat-sources">
                  <div className="chat-sources-title">Sources</div>
                  <ul>
                    {msg.sources.slice(0, 3).map((src, i) => (
                      <li key={i}>
                        <a
                          href={src.url || "#"}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {src.title || src.url || "Source"}
                        </a>
                        {typeof src.score === "number" && (
                          <span className="chat-source-score">
                            {src.score.toFixed(3)}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>

        {error && <div className="chat-error">{error}</div>}

        <form className="chat-input-row" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Ask something about KYC Hub..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? "Thinking..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;


