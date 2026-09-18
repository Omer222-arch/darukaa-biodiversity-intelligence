import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const example = {
  soil_organic_carbon: 0.3,
  soil_moisture: 18,
  rainfall: "low",
  crop: "monoculture wheat",
  region: "semi-arid",
  land_use: "intensive agriculture",
  habitat_diversity: "low",
  pollution: "moderate",
  deforestation: "high"
};

/* =========================================================
   HELPERS
   ========================================================= */

function prettyKey(key) {
  return key
    .replaceAll("_", " ")
    .replace(/\b\w/g, char => char.toUpperCase());
}

function severity(value) {
  const text = String(value || "").toLowerCase();

  if (
    text.includes("high") ||
    text.includes("low-screening") ||
    text.includes("severe")
  ) {
    return "alert";
  }

  if (
    text.includes("moderate") ||
    text.includes("medium") ||
    text.includes("watch")
  ) {
    return "watch";
  }

  return "";
}

function uniqueEvidence(items = []) {
  const seen = new Set();

  return items.filter(item => {
    const key = item?.source_url || item?.title;

    if (!key || seen.has(key)) {
      return false;
    }

    seen.add(key);
    return true;
  });
}

/* =========================================================
   ENVIRONMENTAL SIGNALS
   ========================================================= */

function MetricState({ state }) {
  const entries = Object.entries(state || {});

  if (!entries.length) return null;

  return (
    <div className="state-grid">
      {entries.map(([key, value]) => (
        <div
          className={`state-card ${severity(value)}`}
          key={key}
        >
          <span className="state-label">
            {prettyKey(key)}
          </span>

          <strong>{String(value)}</strong>
        </div>
      ))}
    </div>
  );
}

/* =========================================================
   INTERACTION GRAPH
   ========================================================= */

function InteractionGraph({ graph }) {
  if (!graph?.length) return null;

  return (
    <section className="analysis-section">
      <div className="section-kicker">
        REASONING ENGINE
      </div>

      <div className="section-heading">
        <div>
          <h3>Environmental interaction graph</h3>

          <p className="section-note">
            Multiple environmental signals are connected before
            selecting an intervention.
          </p>
        </div>

        <span className="section-count">
          {graph.length} pathways
        </span>
      </div>

      <div className="interaction-list">
        {graph.map((node, i) => (
          <article className="interaction" key={i}>

            <div className="interaction-step">
              <span className="node-label">
                SIGNALS
              </span>

              <div className="signal-row">
                {(node.signals || []).map(signal => (
                  <span className="signal" key={signal}>
                    {signal}
                  </span>
                ))}
              </div>
            </div>

            <div className="arrow">
              ↓
            </div>

            <div className="interaction-step">
              <span className="node-label">
                RELATIONSHIP
              </span>

              <p>
                {node.relationship}
              </p>
            </div>

            <div className="arrow">
              ↓
            </div>

            <div className="interaction-step intervention-node">
              <span className="node-label">
                INTERVENTION
              </span>

              <p>
                {node.intervention}
              </p>
            </div>

            <div className="metric-output">
              {(node.metrics || []).map(metric => (
                <span key={metric}>
                  {metric}
                </span>
              ))}
            </div>

          </article>
        ))}
      </div>
    </section>
  );
}

/* =========================================================
   CONVERSATIONAL ANALYSIS CARD
   ========================================================= */

function ChatAnalysis({ analysis }) {
  if (!analysis || analysis.needs_clarification) {
    return null;
  }

  const stateEntries = Object.entries(
    analysis.environmental_state || {}
  );

  const recommendations =
    analysis.recommendations || [];

  const graph =
    analysis.interaction_graph || [];

  const evidence = uniqueEvidence(
    recommendations.flatMap(
      recommendation => recommendation.evidence || []
    )
  ).slice(0, 5);

  return (
    <div className="chat-analysis">

      {/* SUMMARY */}

      <div className="chat-assessment">
        <div className="assessment-icon">
          ◈
        </div>

        <div>
          <div className="chat-analysis-label">
            GROUNDED ENVIRONMENTAL ASSESSMENT
          </div>

          <p>
            {analysis.summary}
          </p>
        </div>
      </div>

      {/* SIGNALS */}

      {stateEntries.length > 0 && (
        <div className="chat-analysis-section">

          <div className="chat-analysis-title">
            ENVIRONMENTAL SIGNALS
          </div>

          <div className="chat-signal-grid">
            {stateEntries.map(([key, value]) => (
              <div
                className={`chat-signal ${severity(value)}`}
                key={key}
              >
                <span>
                  {prettyKey(key)}
                </span>

                <strong>
                  {String(value)}
                </strong>
              </div>
            ))}
          </div>

        </div>
      )}

      {/* INTERACTION PATHWAYS */}

      {graph.length > 0 && (
        <div className="chat-analysis-section">

          <div className="chat-analysis-title-row">
            <div className="chat-analysis-title">
              MULTI-METRIC REASONING
            </div>

            <span className="mini-count">
              {graph.length} pathways
            </span>
          </div>

          <div className="chat-pathways">

            {graph.slice(0, 3).map((node, i) => (
              <div
                className="chat-pathway"
                key={i}
              >

                <div className="pathway-top">
                  {(node.signals || []).map(signal => (
                    <span
                      className="pathway-signal"
                      key={signal}
                    >
                      {signal}
                    </span>
                  ))}
                </div>

                <div className="pathway-arrow">
                  ↓
                </div>

                <p>
                  {node.relationship}
                </p>

                <div className="pathway-arrow">
                  ↓
                </div>

                <strong>
                  {node.intervention}
                </strong>

                <div className="pathway-metrics">
                  {(node.metrics || []).map(metric => (
                    <span key={metric}>
                      {metric}
                    </span>
                  ))}
                </div>

              </div>
            ))}

          </div>
        </div>
      )}

      {/* RECOMMENDATIONS */}

      {recommendations.length > 0 && (
        <div className="chat-analysis-section">

          <div className="chat-analysis-title-row">
            <div className="chat-analysis-title">
              RECOMMENDED ACTIONS
            </div>

            <span className="mini-count">
              {recommendations.length}
            </span>
          </div>

          <div className="chat-recommendations">

            {recommendations.map(
              (recommendation, index) => (
                <article
                  className="chat-recommendation"
                  key={index}
                >

                  <div className="chat-rec-number">
                    {String(index + 1).padStart(2, "0")}
                  </div>

                  <div className="chat-rec-content">

                    <h4>
                      {recommendation.action}
                    </h4>

                    <p>
                      {recommendation.why_it_works}
                    </p>

                    <div className="chat-rec-metrics">
                      {(
                        recommendation.impacted_metrics ||
                        []
                      ).map(metric => (
                        <span key={metric}>
                          {metric}
                        </span>
                      ))}
                    </div>

                    <div className="chat-rec-meta">

                      <span>
                        <b>TIME</b>
                        {recommendation.time_horizon}
                      </span>

                      <span>
                        <b>CONFIDENCE</b>
                        {recommendation.confidence}
                      </span>

                    </div>

                  </div>

                </article>
              )
            )}

          </div>
        </div>
      )}

      {/* SCIENTIFIC EVIDENCE */}

      {evidence.length > 0 && (
        <div className="chat-analysis-section">

          <div className="chat-analysis-title">
            SCIENTIFIC EVIDENCE
          </div>

          <div className="chat-evidence-list">

            {evidence.map(item => (
              <a
                className="chat-evidence"
                href={item.source_url}
                target="_blank"
                rel="noreferrer"
                key={item.source_url}
              >

                <div className="evidence-mark">
                  ↗
                </div>

                <div className="evidence-copy">

                  <small>
                    {item.organization}
                  </small>

                  <strong>
                    {item.title}
                  </strong>

                </div>

              </a>
            ))}

          </div>
        </div>
      )}

      <div className="chat-analysis-footer">
        <span>RAG GROUNDED</span>
        <span>•</span>
        <span>MULTI-METRIC REASONING</span>
        <span>•</span>
        <span>SCIENTIFIC EVIDENCE</span>
      </div>

    </div>
  );
}

/* =========================================================
   FULL ANALYSIS PANEL
   ========================================================= */

function Analysis({ result }) {
  if (!result) return null;

  if (result.needs_clarification) {
    return (
      <div className="clarify-box">

        <div className="status">
          CONTEXT NEEDED
        </div>

        <h2>
          {result.summary}
        </h2>

        <div className="clarification-list">
          {(result.clarification_questions || []).map(
            (question, index) => (
              <div
                className="clarification-item"
                key={question}
              >
                <span>
                  0{index + 1}
                </span>

                <p>
                  {question}
                </p>
              </div>
            )
          )}
        </div>

      </div>
    );
  }

  return (
    <>
      <div className="analysis-top">

        <div>
          <div className="status">
            GROUNDED ANALYSIS
          </div>

          <h2>
            {result.summary}
          </h2>
        </div>

        <div className="analysis-status-dot">
          <span></span>
          LIVE
        </div>

      </div>

      <div className="analysis-block">

        <div className="section-kicker">
          ENVIRONMENTAL STATE
        </div>

        <MetricState
          state={result.environmental_state}
        />

      </div>

      <InteractionGraph
        graph={result.interaction_graph}
      />

      {result.reasoning_trace?.length > 0 && (
        <section className="analysis-section">

          <div className="section-kicker">
            DECISION TRACE
          </div>

          <div className="section-heading">
            <div>
              <h3>
                Reasoning trace
              </h3>

              <p className="section-note">
                How the environmental signals were
                transformed into intervention pathways.
              </p>
            </div>

            <span className="section-count">
              {result.reasoning_trace.length} steps
            </span>
          </div>

          <div className="trace-card">

            {result.reasoning_trace.map(
              (step, index) => (
                <div
                  className="trace-row"
                  key={index}
                >
                  <span className="trace-number">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <p>
                    {step}
                  </p>
                </div>
              )
            )}

          </div>

        </section>
      )}

      <section className="analysis-section">

        <div className="section-kicker">
          ACTIONS
        </div>

        <div className="section-heading">
          <div>
            <h3>
              Evidence-backed recommendations
            </h3>

            <p className="section-note">
              Each action is connected to impacted
              environmental metrics and retrieved evidence.
            </p>
          </div>

          <span className="section-count">
            {result.recommendations?.length || 0} actions
          </span>
        </div>

        <div className="recommendations">

          {(result.recommendations || []).map(
            (recommendation, index) => (
              <article
                className="recommendation"
                key={index}
              >

                <div className="recommendation-header">

                  <div className="rec-number">
                    {String(index + 1).padStart(2, "0")}
                  </div>

                  <div>
                    <div className="rec-title">
                      RECOMMENDATION
                    </div>

                    <h3>
                      {recommendation.action}
                    </h3>
                  </div>

                </div>

                <div className="rec-body">

                  <p>
                    {recommendation.why_it_works}
                  </p>

                  {recommendation.reasoning_chain?.length >
                    0 && (
                    <div className="reasoning-chain">

                      <div className="chain-heading">
                        LOGIC CHAIN
                      </div>

                      {recommendation.reasoning_chain.map(
                        (step, j) => (
                          <div
                            className="chain-step"
                            key={j}
                          >
                            <span>
                              {j + 1}
                            </span>

                            <p>
                              {step}
                            </p>
                          </div>
                        )
                      )}

                    </div>
                  )}

                  <div className="chips">

                    {(
                      recommendation.impacted_metrics ||
                      []
                    ).map(metric => (
                      <span key={metric}>
                        {metric}
                      </span>
                    ))}

                  </div>

                  <div className="rec-details">

                    <div>
                      <span>
                        TIME HORIZON
                      </span>

                      <strong>
                        {recommendation.time_horizon}
                      </strong>
                    </div>

                    <div>
                      <span>
                        CONFIDENCE
                      </span>

                      <strong>
                        {recommendation.confidence}
                      </strong>
                    </div>

                  </div>

                  {recommendation.evidence?.length > 0 && (
                    <details>

                      <summary>
                        View supporting evidence
                      </summary>

                      <div className="evidence">

                        {recommendation.evidence.map(
                          evidence => (
                            <a
                              href={evidence.source_url}
                              target="_blank"
                              rel="noreferrer"
                              key={evidence.source_url}
                            >
                              <span>↗</span>
                              <div>
                                <small>
                                  {evidence.organization}
                                </small>

                                <strong>
                                  {evidence.title}
                                </strong>
                              </div>
                            </a>
                          )
                        )}

                      </div>

                    </details>
                  )}

                </div>

              </article>
            )
          )}

        </div>

      </section>

      {result.retrieved_evidence?.length > 0 && (
        <section className="analysis-section">

          <div className="section-kicker">
            RAG LAYER
          </div>

          <div className="section-heading">
            <div>
              <h3>
                Retrieved scientific evidence
              </h3>

              <p className="section-note">
                Documents retrieved from the local
                environmental knowledge base.
              </p>
            </div>

            <span className="section-count">
              {result.retrieved_evidence.length} sources
            </span>
          </div>

          <div className="source-list">

            {result.retrieved_evidence.map(
              evidence => (
                <a
                  className="source"
                  href={evidence.source_url}
                  target="_blank"
                  rel="noreferrer"
                  key={evidence.source_url}
                >

                  <div className="source-top">
                    <span>
                      {evidence.organization}
                    </span>

                    <span>
                      {evidence.relevance}
                    </span>
                  </div>

                  <strong>
                    {evidence.title}
                  </strong>

                  <p>
                    {evidence.excerpt}
                  </p>

                </a>
              )
            )}

          </div>

        </section>
      )}
    </>
  );
}

/* =========================================================
   APPLICATION
   ========================================================= */

function App() {
  const [mode, setMode] = useState("chat");
  const [text, setText] = useState("");
  const [input, setInput] = useState(
    JSON.stringify(example, null, 2)
  );

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Tell me what is happening on the land. I’ll ask for missing environmental context before making a recommendation."
    }
  ]);

  const [conversationId, setConversationId] =
    useState(null);

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendChat(customText) {
    const message = (customText ?? text).trim();

    if (!message || loading) return;

    setLoading(true);
    setError("");

    setMessages(prev => [
      ...prev,
      {
        role: "user",
        content: message
      }
    ]);

    setText("");

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          message
        })
      });

      if (!res.ok) {
        throw new Error(
          `API returned ${res.status}`
        );
      }

      const data = await res.json();

      setConversationId(
        data.conversation_id
      );

      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: data.message,
          analysis: data.analysis || null
        }
      ]);

      if (data.analysis) {
        setResult(data.analysis);
      } else {
        setResult({
          needs_clarification: true,
          summary: data.message,
          clarification_questions:
            data.clarification_questions || []
        });
      }

    } catch (e) {
      setError(
        e.message ||
        "Unable to connect to the environmental intelligence service."
      );
    } finally {
      setLoading(false);
    }
  }

  async function analyzeJSON() {
    setLoading(true);
    setError("");

    try {
      const payload = JSON.parse(input);

      const res = await fetch(
        `${API}/api/analyze`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(payload)
        }
      );

      if (!res.ok) {
        throw new Error(
          `API returned ${res.status}`
        );
      }

      const data = await res.json();

      setResult(data);

    } catch (e) {
      setError(
        e.message ||
        "Invalid JSON or analysis request failed."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">

      {/* =================================================
          HEADER
          ================================================= */}

      <header className="hero">

        <div className="hero-top">

          <div className="eyebrow">
            DARUKAA.EARTH
            <span>•</span>
            AI ENVIRONMENTAL SCIENTIST
          </div>

          <div className="system-status">
            <span className="status-dot"></span>
            SYSTEM ONLINE
          </div>

        </div>

        <h1>
          Biodiversity
          <br />
          <em>Intelligence</em>
        </h1>

        <div className="hero-bottom">

          <p>
            Evidence-grounded reasoning across
            soil, water, land use, climate and
            biodiversity.
          </p>

          <div className="hero-tags">
            <span>SOIL</span>
            <span>WATER</span>
            <span>LAND</span>
            <span>BIODIVERSITY</span>
          </div>

        </div>

      </header>

      {/* =================================================
          MAIN GRID
          ================================================= */}

      <section className="grid">

        {/* =================================================
            INPUT PANEL
            ================================================= */}

        <div className="panel input-panel">

          <div className="panel-label">
            INPUT LAYER
            <span>
              {mode === "chat"
                ? "CONVERSATIONAL"
                : "STRUCTURED"}
            </span>
          </div>

          <div className="tabs">

            <button
              className={
                mode === "chat"
                  ? "active"
                  : ""
              }
              onClick={() => setMode("chat")}
            >
              Conversation
            </button>

            <button
              className={
                mode === "json"
                  ? "active"
                  : ""
              }
              onClick={() => setMode("json")}
            >
              Structured JSON
            </button>

          </div>

          {mode === "chat" ? (
            <>

              <div className="panel-head">

                <div>
                  <div className="mini-label">
                    CONVERSATIONAL INTELLIGENCE
                  </div>

                  <h2>
                    Ask the environmental scientist
                  </h2>
                </div>

                <div className="memory-badge">
                  MEMORY
                </div>

              </div>

              <div className="chat">

                {messages.map((message, index) => (
                  <div
                    className={`bubble ${message.role}`}
                    key={index}
                  >

                    <div className="bubble-header">

                      <span>
                        {message.role ===
                        "assistant"
                          ? "DARUKAA AI"
                          : "YOU"}
                      </span>

                      {message.role ===
                        "assistant" &&
                        message.analysis && (
                          <small>
                            GROUNDED
                          </small>
                        )}

                    </div>

                    <p>
                      {message.content}
                    </p>

                    {message.role ===
                      "assistant" &&
                      message.analysis && (
                        <ChatAnalysis
                          analysis={message.analysis}
                        />
                      )}

                  </div>
                ))}

                {loading && (
                  <div className="bubble assistant thinking">

                    <div className="bubble-header">
                      <span>
                        DARUKAA AI
                      </span>
                    </div>

                    <div className="thinking-row">
                      <span></span>
                      <span></span>
                      <span></span>
                      <em>
                        Connecting environmental signals…
                      </em>
                    </div>

                  </div>
                )}

              </div>

              <div className="composer">

                <div className="composer-label">
                  <span>
                    ENVIRONMENTAL QUERY
                  </span>

                  <span>
                    ENTER TO ANALYZE
                  </span>
                </div>

                <textarea
                  value={text}
                  onChange={e =>
                    setText(e.target.value)
                  }
                  onKeyDown={e => {
                    if (
                      e.key === "Enter" &&
                      !e.shiftKey
                    ) {
                      e.preventDefault();
                      sendChat();
                    }
                  }}
                  placeholder="Describe what is happening on your land…"
                />

                <button
                  className="primary"
                  onClick={() => sendChat()}
                  disabled={
                    loading ||
                    !text.trim()
                  }
                >
                  <span>
                    {loading
                      ? "Analyzing environment…"
                      : "Run analysis"}
                  </span>

                  {!loading && (
                    <span className="button-arrow">
                      ↗
                    </span>
                  )}
                </button>

                <div className="composer-hint">
                  <span>
                    Shift + Enter for a new line
                  </span>

                  <span>
                    {text.length} characters
                  </span>
                </div>

              </div>

            </>
          ) : (
            <>

              <div className="panel-head">

                <div>
                  <div className="mini-label">
                    STRUCTURED INPUT
                  </div>

                  <h2>
                    Environmental context
                  </h2>
                </div>

                <button
                  className="secondary-button"
                  onClick={() =>
                    setInput(
                      JSON.stringify(
                        example,
                        null,
                        2
                      )
                    )
                  }
                >
                  Load demo
                </button>

              </div>

              <textarea
                className="json-editor"
                value={input}
                onChange={e =>
                  setInput(e.target.value)
                }
              />

              <button
                className="primary"
                onClick={analyzeJSON}
                disabled={loading}
              >
                <span>
                  {loading
                    ? "Reasoning…"
                    : "Analyze ecosystem"}
                </span>

                {!loading && (
                  <span className="button-arrow">
                    ↗
                  </span>
                )}
              </button>

              <div className="json-note">
                Accepts environmental variables
                including soil, rainfall, land use,
                biodiversity and human impact.
              </div>

            </>
          )}

          {error && (
            <div className="error">

              <strong>
                Connection error
              </strong>

              <span>
                {error}
              </span>

            </div>
          )}

          <div className="panel-footer">

            <span>
              <i></i>
              FASTAPI
            </span>

            <span>
              <i></i>
              RAG
            </span>

            <span>
              <i></i>
              REASONING
            </span>

            <span>
              <i></i>
              MEMORY
            </span>

          </div>

        </div>

        {/* =================================================
            RESULTS PANEL
            ================================================= */}

        <div className="panel results">

          <div className="results-header">

            <div>
              <div className="panel-label">
                ANALYSIS OUTPUT
              </div>

              <h2>
                Environmental intelligence
              </h2>
            </div>

            {result &&
              !result.needs_clarification && (
                <div className="result-live">
                  <span></span>
                  ANALYSIS COMPLETE
                </div>
              )}

          </div>

          {!result && (
            <div className="empty">

              <div className="empty-orbit">
                ◈
              </div>

              <div className="empty-kicker">
                AWAITING ENVIRONMENTAL INPUT
              </div>

              <h3>
                See the ecosystem.
                <br />
                Understand the interaction.
              </h3>

              <p>
                Start a conversation or submit
                structured environmental data to
                generate evidence-backed ecological
                recommendations.
              </p>

              <div className="empty-flow">
                <span>INPUT</span>
                <b>→</b>
                <span>RETRIEVE</span>
                <b>→</b>
                <span>REASON</span>
                <b>→</b>
                <span>ACTION</span>
              </div>

            </div>
          )}

          <Analysis
            result={result}
          />

        </div>

      </section>

      {/* =================================================
          FOOTER
          ================================================= */}

      <footer>

        <span>
          DARUKAA.EARTH
        </span>

        <span>
          AI BIODIVERSITY INTELLIGENCE
        </span>

        <span>
          EVIDENCE • REASONING • ACTION
        </span>

      </footer>

    </main>
  );
}

createRoot(
  document.getElementById("root")
).render(<App />);