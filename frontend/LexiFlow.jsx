import { useState, useRef } from "react";

const API = "http://localhost:8000";

const C = {
  bg: "#0C0E12", surface: "#14171E", border: "#232830", borderFocus: "#4A6FA5",
  text: "#E2E4E9", textMuted: "#7C8291", textDim: "#515766",
  accent: "#4A6FA5", accentGlow: "rgba(74,111,165,0.15)",
  filler: "#E85D5D", fillerBg: "rgba(232,93,93,0.1)", fillerBorder: "rgba(232,93,93,0.25)",
  weak: "#E8A84C", weakBg: "rgba(232,168,76,0.1)", weakBorder: "rgba(232,168,76,0.25)",
  normal: "#5DAE8B", normalBg: "rgba(93,174,139,0.1)", normalBorder: "rgba(93,174,139,0.25)",
  success: "#5DAE8B",
};

const font = { display: "'Instrument Serif', serif", mono: "'DM Mono', monospace" };

const inputStyle = {
  background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
  color: C.text, fontFamily: font.mono, fontSize: 13, padding: "10px 14px",
  outline: "none", width: "100%", boxSizing: "border-box",
};
const btnPrimary = {
  background: C.accent, color: "#fff", border: "none", borderRadius: 6,
  fontFamily: font.mono, fontSize: 13, fontWeight: 500, padding: "10px 20px",
  cursor: "pointer", letterSpacing: "0.02em",
};
const labelStyle = {
  fontFamily: font.mono, fontSize: 11, color: C.textMuted,
  textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6, display: "block",
};

function BubbleViz({ wordData }) {
  if (!wordData?.length) return null;
  const maxCount = Math.max(...wordData.map((d) => d.count));
  const catColor = { filler: C.filler, weak: C.weak, normal: C.normal };
  const catBg = { filler: C.fillerBg, weak: C.weakBg, normal: C.normalBg };
  const catBorder = { filler: C.fillerBorder, weak: C.weakBorder, normal: C.normalBorder };
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, padding: "4px 0" }}>
      {wordData.map((d, i) => {
        const ratio = d.count / maxCount;
        const size = 30 + ratio * 48;
        const fontSize = 10 + ratio * 6;
        return (
          <div key={i} title={`"${d.word}" — ${d.count}× (${d.category})`}
            style={{
              height: size, borderRadius: size, display: "flex", alignItems: "center",
              justifyContent: "center", gap: 5, background: catBg[d.category],
              border: `1px solid ${catBorder[d.category]}`, fontFamily: font.mono, fontSize,
              color: catColor[d.category], paddingLeft: 12, paddingRight: 12,
              animation: `fadeUp 0.4s ${i * 0.04}s both`,
            }}>
            <span style={{ fontWeight: 500 }}>{d.word}</span>
            <span style={{ opacity: 0.5, fontSize: fontSize - 2 }}>×{d.count}</span>
          </div>
        );
      })}
    </div>
  );
}

function Metric({ label, value, sub, color }) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "16px 20px", flex: 1, minWidth: 130 }}>
      <div style={{ fontFamily: font.mono, fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>{label}</div>
      <div style={{ fontFamily: font.display, fontSize: 32, color: color || C.text, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontFamily: font.mono, fontSize: 11, color: C.textDim, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function Section({ title, tag, children }) {
  return (
    <div style={{ marginBottom: 32 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 14 }}>
        <h2 style={{ fontFamily: font.display, fontSize: 22, color: C.text, margin: 0, fontWeight: 400 }}>{title}</h2>
        {tag && <span style={{ fontFamily: font.mono, fontSize: 10, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.1em" }}>{tag}</span>}
      </div>
      {children}
    </div>
  );
}

export default function LexiFlow() {
  const [step, setStep] = useState("input");
  const [transcript, setTranscript] = useState("");
  const [duration, setDuration] = useState(60);
  const [audioFile, setAudioFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [oldPhrase, setOldPhrase] = useState("");
  const [newPhrase, setNewPhrase] = useState("");
  const [goalMsg, setGoalMsg] = useState(null);
  const [practiceTopic, setPracticeTopic] = useState("");
  const [practicePrompt, setPracticePrompt] = useState(null);
  const fileRef = useRef();

  async function handleAnalyze() {
    if (!transcript.trim()) return;
    setLoading(true); setError(null);
    try {
      const formData = new FormData();
      formData.append("file", audioFile || new Blob(["placeholder"], { type: "audio/wav" }), audioFile?.name || "speech.wav");
      const uploadRes = await fetch(`${API}/recordings/upload`, { method: "POST", body: formData });
      if (!uploadRes.ok) throw new Error("Upload failed");
      const { id } = await uploadRes.json();

      const analyzeRes = await fetch(`${API}/recordings/${id}/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript, duration_seconds: parseFloat(duration) }),
      });
      if (!analyzeRes.ok) throw new Error("Analysis failed");
      setAnalysis(await analyzeRes.json());
      setStep("results");
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  async function handleCreateGoal() {
    if (!oldPhrase.trim() || !newPhrase.trim()) return;
    try {
      const res = await fetch(`${API}/goals`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ old_phrase: oldPhrase, new_phrase: newPhrase }),
      });
      if (!res.ok) throw new Error("Failed");
      setGoalMsg(`Goal set: "${oldPhrase}" → "${newPhrase}"`);
      setOldPhrase(""); setNewPhrase("");
      setTimeout(() => setGoalMsg(null), 4000);
    } catch (e) { setGoalMsg("Error: " + e.message); }
  }

  async function handleGeneratePractice() {
    try {
      const res = await fetch(`${API}/practice/generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: practiceTopic || "general communication" }),
      });
      if (!res.ok) throw new Error("Failed");
      setPracticePrompt((await res.json()).prompt);
    } catch (e) { setPracticePrompt("Error: " + e.message); }
  }

  return (
    <div style={{ minHeight: "100vh", background: C.bg, color: C.text, fontFamily: font.mono }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Instrument+Serif&display=swap');
        @keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        input:focus, textarea:focus { border-color: ${C.borderFocus} !important; box-shadow: 0 0 0 3px ${C.accentGlow} !important; }
        button:hover { filter: brightness(1.1); transform: translateY(-1px); }
        ::selection { background: ${C.accent}; color: #fff; }
      `}</style>

      <header style={{ borderBottom: `1px solid ${C.border}`, padding: "20px 24px", display: "flex", alignItems: "baseline", gap: 14 }}>
        <h1 style={{ fontFamily: font.display, fontSize: 28, margin: 0, fontWeight: 400 }}>LexiFlow</h1>
        <span style={{ fontSize: 11, color: C.textDim, letterSpacing: "0.08em", textTransform: "uppercase" }}>speech analysis mvp</span>
        {step === "results" && (
          <button onClick={() => { setStep("input"); setAnalysis(null); }}
            style={{ ...btnPrimary, background: "transparent", border: `1px solid ${C.border}`, color: C.textMuted, marginLeft: "auto", fontSize: 11, padding: "6px 14px" }}>
            ← New Analysis
          </button>
        )}
      </header>

      <div style={{ maxWidth: 780, margin: "0 auto", padding: "40px 16px 80px" }}>
        {/* ── INPUT ── */}
        {step === "input" && (
          <div style={{ animation: "fadeIn 0.4s both" }}>
            <Section title="Analyze Your Speech" tag="step 1">
              <div style={{ marginBottom: 20 }}>
                <label style={labelStyle}>Audio file (optional)</label>
                <div onClick={() => fileRef.current?.click()}
                  style={{ background: C.surface, border: `1px dashed ${C.border}`, borderRadius: 8, padding: "20px 24px", textAlign: "center", cursor: "pointer", color: C.textMuted, fontSize: 12 }}>
                  {audioFile ? <span style={{ color: C.success }}>✓ {audioFile.name}</span> : <span>Click to upload audio · mp3 / wav / m4a</span>}
                  <input ref={fileRef} type="file" accept="audio/*" style={{ display: "none" }} onChange={(e) => setAudioFile(e.target.files[0] || null)} />
                </div>
              </div>
              <div style={{ marginBottom: 20 }}>
                <label style={labelStyle}>Transcript</label>
                <textarea value={transcript} onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Paste or type your speech transcript here. Whisper auto-transcription coming soon."
                  rows={8} style={{ ...inputStyle, resize: "vertical", lineHeight: 1.7 }} />
              </div>
              <div style={{ marginBottom: 24 }}>
                <label style={labelStyle}>Speech duration (seconds)</label>
                <input type="number" value={duration} onChange={(e) => setDuration(e.target.value)} style={{ ...inputStyle, width: 140 }} />
              </div>
              {error && <div style={{ color: C.filler, fontSize: 12, marginBottom: 16 }}>{error}</div>}
              <button onClick={handleAnalyze} disabled={loading || !transcript.trim()}
                style={{ ...btnPrimary, opacity: loading || !transcript.trim() ? 0.5 : 1, width: "100%", padding: "13px 24px", fontSize: 14 }}>
                {loading ? "Analyzing..." : "Analyze Speech →"}
              </button>
            </Section>
          </div>
        )}

        {/* ── RESULTS ── */}
        {step === "results" && analysis && (
          <div style={{ animation: "fadeIn 0.5s both" }}>
            <Section title="Your Numbers" tag="metrics">
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Metric label="Fillers" value={analysis.metrics.filler_count} sub={`in ${analysis.metrics.total_words} words`} color={analysis.metrics.filler_count > 5 ? C.filler : C.success} />
                <Metric label="Vocab Diversity" value={analysis.metrics.vocab_diversity} sub="unique / total" color={analysis.metrics.vocab_diversity > 0.6 ? C.success : C.weak} />
                <Metric label="WPM" value={analysis.metrics.words_per_minute} sub="words per minute" />
                <Metric label="Total Words" value={analysis.metrics.total_words} sub={`${analysis.metrics.unique_words} unique`} />
              </div>
            </Section>

            {analysis.filler_words && Object.keys(analysis.filler_words).length > 0 && (
              <Section title="Filler Breakdown" tag="reduce these">
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {Object.entries(analysis.filler_words).sort((a, b) => b[1] - a[1]).map(([word, count]) => (
                    <div key={word} style={{ background: C.fillerBg, border: `1px solid ${C.fillerBorder}`, borderRadius: 6, padding: "8px 14px", fontSize: 13, color: C.filler, display: "flex", alignItems: "center", gap: 8 }}>
                      <span>"{word}"</span><span style={{ opacity: 0.55, fontSize: 11 }}>×{count}</span>
                    </div>
                  ))}
                </div>
              </Section>
            )}

            <Section title="Word Map" tag="visualization">
              <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 20 }}>
                <BubbleViz wordData={analysis.word_data} />
                <div style={{ display: "flex", gap: 16, marginTop: 14, paddingTop: 12, borderTop: `1px solid ${C.border}` }}>
                  {[{ label: "Filler", color: C.filler }, { label: "Weak", color: C.weak }, { label: "Normal", color: C.normal }].map((l) => (
                    <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: C.textMuted }}>
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: l.color }} />{l.label}
                    </div>
                  ))}
                </div>
              </div>
            </Section>

            <Section title="Transcript" tag="raw text">
              <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "16px 20px", fontSize: 13, lineHeight: 1.8, color: C.textMuted, maxHeight: 200, overflowY: "auto" }}>
                {analysis.transcript}
              </div>
            </Section>

            <Section title="Set a Replacement Goal" tag="vocabulary upgrade">
              <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 20 }}>
                <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
                  <div style={{ flex: 1, minWidth: 140 }}>
                    <label style={labelStyle}>Replace</label>
                    <input value={oldPhrase} onChange={(e) => setOldPhrase(e.target.value)} placeholder='"very big"' style={inputStyle} />
                  </div>
                  <div style={{ color: C.textDim, fontFamily: font.display, fontSize: 20, paddingBottom: 8 }}>→</div>
                  <div style={{ flex: 1, minWidth: 140 }}>
                    <label style={labelStyle}>With</label>
                    <input value={newPhrase} onChange={(e) => setNewPhrase(e.target.value)} placeholder='"massive"' style={inputStyle} />
                  </div>
                  <button onClick={handleCreateGoal} style={{ ...btnPrimary, whiteSpace: "nowrap", opacity: !oldPhrase.trim() || !newPhrase.trim() ? 0.4 : 1 }}>Save Goal</button>
                </div>
                {goalMsg && <div style={{ marginTop: 12, fontSize: 12, color: goalMsg.startsWith("Error") ? C.filler : C.success, animation: "fadeIn 0.3s both" }}>{goalMsg}</div>}
              </div>
            </Section>

            <Section title="Guided Speaking Prompt" tag="practice">
              <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 20 }}>
                <div style={{ display: "flex", gap: 12, alignItems: "flex-end", marginBottom: practicePrompt ? 16 : 0 }}>
                  <div style={{ flex: 1 }}>
                    <label style={labelStyle}>Topic (optional)</label>
                    <input value={practiceTopic} onChange={(e) => setPracticeTopic(e.target.value)} placeholder="e.g. teamwork in software development" style={inputStyle} />
                  </div>
                  <button onClick={handleGeneratePractice} style={{ ...btnPrimary, whiteSpace: "nowrap" }}>Generate Prompt</button>
                </div>
                {practicePrompt && (
                  <div style={{ background: C.accentGlow, border: `1px solid ${C.borderFocus}`, borderRadius: 8, padding: "16px 20px", fontSize: 13, lineHeight: 1.8, color: C.text, animation: "fadeIn 0.4s both" }}>
                    {practicePrompt}
                  </div>
                )}
              </div>
            </Section>
          </div>
        )}
      </div>
    </div>
  );
}
