import React, { useState } from "react";

const BACKEND_URL = "https://tailortalk-node-backend.onrender.com/chat";

function App() {
  const [messages, setMessages] = useState([]);
  const [context, setContext] = useState({});
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = input.trim();
    setMessages((msgs) => [...msgs, { sender: "user", text: userMsg }]);
    setInput("");
    setLoading(true);

    try {
      const resp = await fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, context }),
      });
      const data = await resp.json();
      setMessages((msgs) => [
        ...msgs,
        { sender: "bot", text: data.response || "(No response from bot)" },
      ]);
      setContext(data.context || {});
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { sender: "bot", text: "Error: " + err.message },
      ]);
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h2>🤖 TailorTalk Chat</h2>
      <div style={{
        background: "#222", color: "#fff", borderRadius: 8, padding: 16, minHeight: 300, marginBottom: 16
      }}>
        {messages.length === 0 && (
          <div style={{ color: "#aaa" }}>
            <b>Example prompts:</b>
            <ul>
              <li>Book a meeting for tomorrow afternoon</li>
              <li>Schedule a call tomorrow at 3pm</li>
              <li>Book a meeting on Friday at 5pm</li>
              <li>Do I have any free time this Friday?</li>
            </ul>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{
            textAlign: msg.sender === "user" ? "right" : "left",
            margin: "8px 0"
          }}>
            <span style={{
              display: "inline-block",
              background: msg.sender === "user" ? "#4f8cff" : "#444",
              color: "#fff",
              borderRadius: 16,
              padding: "8px 16px",
              maxWidth: "80%",
              wordBreak: "break-word"
            }}>
              <b>{msg.sender === "user" ? "You" : "TailorTalk"}:</b> {msg.text}
            </span>
          </div>
        ))}
        {loading && <div style={{ color: "#aaa" }}>TailorTalk is typing...</div>}
      </div>
      <form onSubmit={sendMessage} style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your message..."
          style={{
            flex: 1,
            padding: 12,
            borderRadius: 8,
            border: "1px solid #ccc",
            fontSize: 16
          }}
          disabled={loading}
        />
        <button
          type="submit"
          style={{
            padding: "0 24px",
            borderRadius: 8,
            border: "none",
            background: "#4f8cff",
            color: "#fff",
            fontWeight: "bold",
            fontSize: 16,
            cursor: "pointer"
          }}
          disabled={loading}
        >
          Send
        </button>
      </form>
    </div>
  );
}

export default App;