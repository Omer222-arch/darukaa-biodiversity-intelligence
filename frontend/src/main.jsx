import React, { useMemo, useState } from "react";
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

const labels = {
  soil_carbon_signal: "Soil carbon",
  soil_carbon_value: "SOC",
  water_signal: "Rainfall",
  land_use_signal: "Land use",
  habitat_pressure: "Habitat pressure",
  habitat_diversity: "Habitat diversity"
};

function prettyKey(key) {
  return labels[key] || key.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());
}

function severity(value) {
  const v = String(value).toLowerCase();
  if (v.includes("low") || v.includes("high") || v.includes("0.3") || v.includes("pressure")) return "alert";
  if (v.includes("moderate") || v.includes("screening")) return "watch";
  return "normal";
}

function EnvironmentalState({ state }) {
  const entries = Object.entries(state || {});
  return (
    <section className="state-section">
      <div className="section-heading">
        <div>
          <div className="section-kicker">01 · ENVIRONMENTAL STATE</div>
          <h2>What Darukaa sees</h2>
        </div>
        <span className="live-badge"><i /> LIVE ANALYSIS</span>
      </div>
      <div className="state-grid">
        {entries.map(([key, value]) => (
          <div className={`metric-card ${severity(value)}`} key={key}>
            <div className="metric-top">
              <span>{prettyKey(key)}</span>
              <span className="metric-dot" />
            </div>
            <strong>{String(value)}</strong>
            <small>{key === "soil_carbon_value" ? "measured input" : "detected signal"}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

function InteractionGraph({ graph }) {
  if (!graph?.length) return null;
  return (
    <section>
      <div className="section-heading">
        <div>
          <div className="section-kicker">02 · MULTI-METRIC REASONING</div>
          <h2>Environmental interaction graph</h2>
          <p className="section-note">Signals are connected before an intervention is selected.</p>
        </div>
        <span className="graph-badge">{graph.length} pathways</span>
      </div>
      <div className="graph-grid">
        {graph.map((node, i) => (
          <article className="graph-card" key={i}>
            <div className="graph-number">0{i + 1}</div>
            <div className="graph-block">
              <span className="node-label">SIGNALS</span>
              <div className="signal-row">{node.signals.map(signal => <span className="signal" key={signal}>{signal}</span>)}</div>
            </div>
            <div className="graph-arrow">↓</div>
            <div className="graph-block relationship">
              <span className="node-label">RELATIONSHIP</span>
              <p>{node.relationship}</p>
            </div>
            <div className="graph-arrow">↓</div>
            <div className="graph-block intervention-node">
              <span className="node-label">INTERVENTION</span>
              <p>{node.intervention}</p>
            </div>
            <div className="metric-output">
              {node.metrics.map(metric => <span key={metric}>↗ {metric}</span>)}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ReasoningTrace({ trace }) {
  if (!trace?.length) return null;
  return (
    <section className="trace-section">
      <div className="section-kicker">03 · DECISION TRACE</div>
      <h2>How the system reasoned</h2>
      <div className="trace-timeline">
        {trace.map((item, i) => (
          <div className="trace-item" key={i}>
            <div className="trace-marker">{String(i + 1).padStart(2, "0")}</div>
            <p>{item}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function EvidenceCard({ evidence }) {
  return (
    <a className="evidence-card" href={evidence.source_url} target="_blank" rel="noreferrer">
      <div className="evidence-icon">↗</div>
      <div>
        <small>{evidence.organization}</small>
        <strong>{evidence.title}</strong>
        <span>View scientific source</span>
      </div>
    </a>
  );
}

function Recommendation({ recommendation, index }) {
  return (
    <article className="recommendation">
      <div className="rec-head">
        <div className="rec-index">0{index + 1}</div>
        <div>
          <span className="section-kicker">ACTION {index + 1}</span>
          <h3>{recommendation.action}</h3>
        </div>
      </div>
      <p className="rec-why">{recommendation.why_it_works}</p>

      <div className="reasoning-chain">
        <div className="chain-label">REASONING CHAIN</div>
        {recommendation.reasoning_chain?.map((step, j) => (
          <div className="chain-step" key={j}>
            <span>{j + 1}</span><p>{step}</p>
          </div>
        ))}
      </div>

      <div className="rec-meta">
        <div><span>IMPACTED METRICS</span><div className="chips">{recommendation.impacted_metrics.map(m => <b key={m}>{m}</b>)}</div></div>
        <div className="meta-pair"><span>TIME HORIZON</span><strong>{recommendation.time_horizon}</strong></div>
        <div className="meta-pair"><span>CONFIDENCE</span><strong>{recommendation.confidence}</strong></div>
      </div>

      <div className="evidence-wrap">
        <div className="evidence-title"><span>SCIENTIFIC EVIDENCE</span><em>{recommendation.evidence?.length || 0} sources</em></div>
        <div className="evidence-grid">{recommendation.evidence?.map(e => <EvidenceCard evidence={e} key={e.source_url} />)}</div>
      </div>
    </article>
  );
}

function Analysis({ result }) {
  if (!result) return (
    <div className="empty-state">
      <div className="empty-orbit"><span>◌</span></div>
      <div className="section-kicker">DARUKAA ENGINE READY</div>
      <h2>Turn environmental signals into evidence-backed action.</h2>
      <p>Start with a natural-language question or structured ecosystem data.</p>
      <div className="empty-flow"><span>signals</span><b>→</b><span>reasoning</span><b>→</b><span>evidence</span><b>→</b><span>action</span></div>
    </div>
  );

  if (result.needs_clarification) {
    return (
      <div className="clarification-panel">
        <div className="status-pill">CONTEXT NEEDED</div>
        <h2>{result.summary}</h2>
        <p className="clarify-intro">A site-specific recommendation needs a little more environmental context.</p>
        <div className="question-list">{result.clarification_questions.map((q, i) => <div key={q}><span>{i + 1}</span>{q}</div>)}</div>
      </div>
    );
  }

  return (
    <div className="analysis-content">
      <div className="analysis-hero">
        <div>
          <span className="status-pill grounded">● GROUNDED ANALYSIS</span>
          <h1>Environmental intelligence report</h1>
          <p>{result.summary}</p>
        </div>
        <div className="score-orbit"><div><strong>{result.recommendations?.length || 0}</strong><span>actions</span></div></div>
      </div>

      <EnvironmentalState state={result.environmental_state} />
      <InteractionGraph graph={result.interaction_graph} />
      <ReasoningTrace trace={result.reasoning_trace} />

      <section>
        <div className="section-heading">
          <div><div className="section-kicker">04 · RECOMMENDATIONS</div><h2>Evidence-backed actions</h2></div>
          <span className="graph-badge">Actionable</span>
        </div>
        {result.recommendations?.map((r, i) => <Recommendation recommendation={r} index={i} key={i} />)}
      </section>

      <section className="rag-section">
        <div className="section-heading"><div><div className="section-kicker">05 · RAG LAYER</div><h2>Retrieved scientific evidence</h2></div><span className="graph-badge">Local knowledge base</span></div>
        <div className="source-grid">{result.retrieved_evidence?.map(e => <EvidenceCard evidence={e} key={e.source_url} />)}</div>
      </section>
    </div>
  );
}

function App() {
  const [mode, setMode] = useState("chat");
  const [text, setText] = useState("");
  const [input, setInput] = useState(JSON.stringify(example, null, 2));
  const [messages, setMessages] = useState([{ role: "assistant", content: "Tell me what is happening on the land. I’ll ask for missing environmental context before making a recommendation." }]);
  const [conversationId, setConversationId] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const contextCount = useMemo(() => result?.environmental_state ? Object.keys(result.environmental_state).length : 0, [result]);

  async function sendChat(customText) {
    const message = (customText ?? text).trim();
    if (!message || loading) return;
    setLoading(true); setError(""); setMessages(prev => [...prev, { role: "user", content: message }]); setText("");
    try {
      const res = await fetch(`${API}/api/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ conversation_id: conversationId, message }) });
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      const data = await res.json();
      setConversationId(data.conversation_id); setMessages(prev => [...prev, { role: "assistant", content: data.message }]);
      setResult(data.analysis || { needs_clarification: true, summary: data.message, clarification_questions: data.clarification_questions || [] });
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  async function analyzeJSON() {
    setLoading(true); setError("");
    try {
      const payload = JSON.parse(input);
      const res = await fetch(`${API}/api/analyze`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      setResult(await res.json());
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  function loadDemoChat() { setText("Biodiversity is declining on my semi-arid farm. I grow monoculture wheat."); }
  function runFullDemo() {
    setMode("chat");
    setMessages([{ role: "assistant", content: "Tell me what is happening on the land. I’ll ask for missing environmental context before making a recommendation." }]);
    setConversationId(null); setResult(null); setText("Biodiversity is declining on my semi-arid farm. I grow monoculture wheat.");
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><div className="brand-mark">D</div><div><strong>DARUKAA<span>.EARTH</span></strong><small>BIODIVERSITY INTELLIGENCE</small></div></div>
        <div className="top-status"><i /> SYSTEM ONLINE <span>·</span> LOCAL RAG</div>
      </header>

      <section className="hero">
        <div className="hero-copy"><div className="eyebrow">AI ENVIRONMENTAL SCIENTIST</div><h1>See the ecosystem.<br/><em>Understand the interaction.</em></h1><p>Evidence-grounded environmental reasoning across soil, water, land use, climate and biodiversity.</p></div>
        <div className="hero-orb"><div className="orb-ring ring-a"/><div className="orb-ring ring-b"/><div className="orb-core"><span>◎</span><small>ENVIRONMENT<br/>MODEL</small></div></div>
      </section>

      <section className="workspace">
        <aside className="input-panel">
          <div className="input-head"><div><span className="section-kicker">INPUT LAYER</span><h2>Ask Darukaa</h2></div><span className="api-dot">API</span></div>
          <div className="tabs"><button className={mode === "chat" ? "active" : ""} onClick={() => setMode("chat")}>Conversation</button><button className={mode === "json" ? "active" : ""} onClick={() => setMode("json")}>Structured JSON</button></div>
          {mode === "chat" ? <>
            <div className="chat">{messages.map((m, i) => <div className={`bubble ${m.role}`} key={i}><span>{m.role === "assistant" ? "DARUKAA AI" : "YOU"}</span><p>{m.content}</p></div>)}</div>
            <textarea className="composer-input" value={text} onChange={e => setText(e.target.value)} onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); } }} placeholder="Describe what is happening on your land…" />
            <button className="primary" onClick={() => sendChat()} disabled={loading}>{loading ? <><i className="spinner"/> Analyzing…</> : <>Run analysis <span>↗</span></>}</button>
            <button className="demo-link" onClick={loadDemoChat}>Load first demo message</button>
          </> : <>
            <textarea className="json-input" value={input} onChange={e => setInput(e.target.value)} />
            <button className="primary" onClick={analyzeJSON} disabled={loading}>{loading ? "Reasoning…" : <>Analyze ecosystem <span>↗</span></>}</button>
            <button className="demo-link" onClick={() => setInput(JSON.stringify(example, null, 2))}>Reset demo data</button>
          </>}
          {error && <div className="error">{error}</div>}
          <div className="input-footer"><span>● FASTAPI</span><span>● RAG</span><span>● REASONING</span></div>
        </aside>

        <div className="results-panel">
          <div className="results-top"><span>ANALYSIS OUTPUT</span>{result && <span>{contextCount} environmental signals retained</span>}</div>
          <Analysis result={result} />
        </div>
      </section>

      <footer><span>DARUKAA.EARTH</span><span>ENVIRONMENTAL INTELLIGENCE · RAG · MULTI-METRIC REASONING</span><button onClick={runFullDemo}>Reset demo</button></footer>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
