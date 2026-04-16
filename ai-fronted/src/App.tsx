const conversations = [
  "Brand launch",
  "Product copy",
  "Research summary",
  "Design review",
  "Weekly plan"
];

const suggestions = [
  "Draft a compact launch plan",
  "Compare three UI directions",
  "Turn notes into action items",
  "Review this onboarding flow"
];

const chatMessages = [
  {
    role: "assistant",
    title: "What should we shape today?",
    body: "Drop a prompt, a file, or a link. I will keep the thread focused and ready to continue."
  },
  {
    role: "user",
    title: "Make the product update shorter",
    body: "Keep the same details, but make it suitable for the top of a release note."
  },
  {
    role: "assistant",
    title: "Here is a tighter version",
    body: "The release brings faster search, cleaner project switching, and clearer billing alerts for team admins."
  }
];

export function App() {
  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Conversations">
        <div className="brand-mark">AI</div>
        <button className="new-chat-button">New chat</button>
        <nav className="conversation-list">
          {conversations.map((item) => (
            <a href="#chat" key={item} className="conversation-link">
              {item}
            </a>
          ))}
        </nav>
        <div className="profile-row">
          <span className="avatar">R</span>
          <span>Ren</span>
        </div>
      </aside>

      <section className="workspace" id="chat">
        <header className="topbar">
          <div>
            <p className="eyebrow">ChatGPT Redesign</p>
            <h1>Ask, refine, continue.</h1>
          </div>
          <button className="share-button">Share</button>
        </header>

        <section className="prompt-band" aria-label="Prompt suggestions">
          {suggestions.map((item) => (
            <button className="suggestion-chip" key={item}>
              {item}
            </button>
          ))}
        </section>

        <section className="chat-stack" aria-label="Chat messages">
          {chatMessages.map((message) => (
            <article className={`message-row ${message.role}`} key={message.title}>
              <div className="message-avatar">{message.role === "assistant" ? "G" : "Y"}</div>
              <div className="message-content">
                <h2>{message.title}</h2>
                <p>{message.body}</p>
              </div>
            </article>
          ))}
        </section>

        <form className="composer">
          <button type="button" className="icon-button" aria-label="Attach file">
            +
          </button>
          <input aria-label="Message" placeholder="Message ChatGPT" />
          <button type="submit" className="send-button">
            Send
          </button>
        </form>
      </section>
    </main>
  );
}
