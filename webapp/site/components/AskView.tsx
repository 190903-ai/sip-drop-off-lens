"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import type { AskResult, Evidence } from "@/lib/ask";

export const STARTERS = [
  "Why do first-time investors stop their SIP?",
  "What goes wrong with SIP payments and mandates?",
  "What keeps people investing after a loss?",
  "Do people pause, or cancel outright?",
  "What do Groww users complain about most?",
  "Who do new investors lean on for advice?",
];
type Brief = { key: string; question: string };
const HIST_KEY = "ask-history";
const withOutcome = (href: string, outcome: string) => {
  const u = new URLSearchParams(href.split("?")[1] ?? "");
  u.set("outcome", outcome);
  return `/stories?${u.toString()}`;
};

function Rich({ text, onCite }: { text: string; onCite: (n: number) => void }) {
  // **bold** and [n] citations; everything else is plain text
  const parts = text.split(/(\*\*[^*]+\*\*|\[\d+\])/g).filter(Boolean);
  return <>{parts.map((p, i) => {
    if (p.startsWith("**")) return <b key={i}>{p.slice(2, -2)}</b>;
    const m = p.match(/^\[(\d+)\]$/);
    if (m) return <sup className="c" key={i}><button onClick={() => onCite(+m[1])} aria-label={`Source ${m[1]}`}>{m[1]}</button></sup>;
    return <span key={i}>{p}</span>;
  })}</>;
}

function Cite({ e, hl }: { e: Evidence; hl: boolean }) {
  return (
    <div className={`cite${hl ? " hl" : ""}`} id={`cite-${e.n}`}>
      <div className="top"><span className="c-num">{e.n}</span><span className="chip">{e.source}</span>{e.tags.map((t) => <span className="chip a" key={t}>{t}</span>)}</div>
      <p className="quote">{e.quote}</p>
      <div className="meta">
        <span>{[e.grp === "first_time" ? "First-time" : e.grp === "experienced" ? "Experienced" : "", e.cls === "stayed" ? "kept going" : e.cls === "dropoff" ? "stopped or wavering" : "related post"].filter(Boolean).join(" · ")}</span>
        {e.url && e.exact && <a className="link" href={e.url} target="_blank" rel="noopener noreferrer">Original ↗</a>}
      </div>
    </div>
  );
}

function Minis({ ev }: { ev: Evidence[] }) {
  return <div className="minis">{ev.map((e) => (
    <div className="card mini" key={e.id}><p className="quote">{e.quote}</p><p className="meta" style={{ marginTop: 8 }}>{e.source}{e.tags[0] ? ` · ${e.tags[0].toLowerCase()}` : ""}{e.url && e.exact && <> · <a className="link" style={{ fontSize: 12 }} href={e.url} target="_blank" rel="noopener noreferrer">Original ↗</a></>}</p></div>
  ))}</div>;
}

export default function AskView({ briefs }: { briefs: Brief[] }) {
  const sp = useSearchParams();
  const [q, setQ] = useState("");
  const [res, setRes] = useState<AskResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [netErr, setNetErr] = useState(false);
  const [hl, setHl] = useState<number | null>(null);
  const [hist, setHist] = useState<string[]>([]);
  const last = useRef<{ question: string; key?: string } | null>(null);
  const top = useRef<HTMLDivElement>(null);

  useEffect(() => { try { setHist(JSON.parse(localStorage.getItem(HIST_KEY) ?? "[]")); } catch {} }, []);

  const ask = useCallback(async (question: string, key?: string) => {
    if (!question.trim() && !key) return;
    last.current = { question, key };
    setQ(question); setBusy(true); setNetErr(false); setHl(null);
    top.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    try {
      const r = await fetch("/api/ask", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ question, key }) });
      if (!r.ok) throw new Error(String(r.status));
      setRes(await r.json());
      setHist((h) => {
        const next = [question, ...h.filter((x) => x !== question)].slice(0, 6);
        try { localStorage.setItem(HIST_KEY, JSON.stringify(next)); } catch {}
        return next;
      });
    } catch {
      setNetErr(true); setRes(null);
    } finally { setBusy(false); }
  }, []);

  useEffect(() => {
    const k = sp.get("q");
    const b = briefs.find((x) => x.key === k);
    if (b) ask(b.question, b.key);
    else if (sp.get("ask")) ask(sp.get("ask")!);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const cite = (n: number) => { setHl(n); document.getElementById(`cite-${n}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" }); };
  const retry = () => last.current && ask(last.current.question, last.current.key);
  const showing = busy || res || netErr;

  const askCard = (
    <div className="panel">
      <form className="askcard" onSubmit={(e) => { e.preventDefault(); ask(q); }}>
        <div className="askhead"><span className="ico"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" /></svg></span>
          <span><b>Ask a question</b><small>Answered only from the 720 tagged stories and 1,128 related posts, with numbered citations</small></span></div>
        <div className="askrow">
          <input className="ask-input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Why do first-time investors stop their SIP?" aria-label="Your question" maxLength={300} />
          <button className="btn" type="submit" disabled={busy}>{busy ? "Asking…" : "Ask"}</button>
        </div>
      </form>
      {res && !busy && res.status !== "advice" && res.status !== "unclear" && (
        <div className="understood"><b style={{ color: "var(--ink-2)" }}>Understood as:</b>{res.chips.map((c) => <span key={c.text} className={`chip ${c.tone}`}>{c.text}</span>)}<span>→ {res.searched.toLocaleString("en-IN")} items searched</span></div>
      )}
      {res && !busy && res.status === "advice" && (
        <div className="advice">
          <b>This engine doesn&rsquo;t give investment advice.</b> It only reports what investors have said. For a decision about your own money, speak to a SEBI-registered investment adviser.
          <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
            <Link className="chip g" href={withOutcome(res.exploreHref, "dropoff")}>Stories of people who stopped &rarr;</Link>
            <Link className="chip g" href={withOutcome(res.exploreHref, "stayed")}>Stories of people who kept going &rarr;</Link>
          </div>
        </div>
      )}
    </div>
  );

  const prompts = (
    <>
      <div className="sec"><div><div className="eyebrow">Starter questions</div><h2 style={{ fontSize: 22 }}>Start with a broad question</h2><p>These show the kinds of drop-off, friction and staying behaviour the stories can answer.</p></div></div>
      <div className="prompts">
        {STARTERS.map((s, i) => (
          <button key={s} className="card prompt" onClick={() => ask(s)}><span><small>PROMPT {String(i + 1).padStart(2, "0")}</small><b>{s}</b></span><span className="arr">&rarr;</span></button>
        ))}
      </div>
      <div className="sec"><div><div className="eyebrow">The brief&rsquo;s nine questions</div><h2 style={{ fontSize: 22 }}>Pre-computed answers</h2><p>Saved in advance, so they work even when the AI is unavailable.</p></div></div>
      <div className="prompts">
        {briefs.map((b, i) => (
          <button key={b.key} className="card prompt" onClick={() => ask(b.question, b.key)}><span><small>QUESTION {i + 1}</small><b>{b.question}</b></span><span className="arr">&rarr;</span></button>
        ))}
      </div>
    </>
  );

  const side = (
    <div>
      <div className="panel hist">
        <div className="panel-head"><span><div className="eyebrow" style={{ fontSize: 11 }}>On this device</div><b style={{ marginTop: 6 }}>Recent questions</b></span></div>
        {hist.length === 0 ? <div className="hrow">No questions yet. Questions you ask will appear here.</div>
          : hist.map((h) => <button key={h} className="hrow" onClick={() => ask(h, briefs.find((b) => b.question === h)?.key)}>{h}</button>)}
        <div className="foot"><span>Stored only in this browser.</span>{hist.length > 0 && <button className="link" style={{ fontSize: 12 }} onClick={() => { setHist([]); try { localStorage.removeItem(HIST_KEY); } catch {} }}>Clear</button>}</div>
      </div>
      <div className="panel trust"><b>How answers are checked</b>The AI only sees retrieved stories. Every sentence needs a story citation or must be a count that matches the data, every percentage is checked against the counts, and every quote is matched word for word to its source before it&rsquo;s shown.</div>
      <div className="panel trust"><b>No advice</b>The engine reports what investors said. It does not tell you what to do with your SIP or which fund to pick, and it does not propose product solutions.</div>
    </div>
  );

  return (
    <div ref={top} style={{ scrollMarginTop: 80 }}>
      <div className="page-head">
        <div>
          <div className="eyebrow">Explore investor stories</div>
          <h1>Ask the Data</h1>
          <p>Ask a question, see how it was understood, and check every claim against the stories it came from. Answers describe what investors said; they do not recommend funds.</p>
        </div>
      </div>
      {!showing ? (
        <div className="ask-cols"><div>{askCard}{prompts}</div>{side}</div>
      ) : (
        <>
          <div className="ask-cols">
            <div>
              {askCard}
              {busy && <div className="panel answer"><div className="loading"><span className="spin" />Searching the stories and writing a cited answer…</div></div>}
              {netErr && !busy && <div className="warn"><b>Couldn&rsquo;t reach the server.</b> Check your connection. <button className="link" style={{ marginLeft: "auto" }} onClick={retry}>Try again</button></div>}
              {res && !busy && res.status === "answer" && (
                <div className="panel answer">
                  <div className="panel-head"><span><b>Answer</b><small>From {res.searched.toLocaleString("en-IN")} items · {res.evidence.length} cited</small></span><span className="meta">{res.model} · checked{res.cached ? " · saved answer" : ""}</span></div>
                  <div className="body">
                    {res.paragraphs!.map((p, i) => <p key={i}><Rich text={p} onCite={cite} /></p>)}
                    <div className="caveat"><b>How sure is this?</b> {res.caveat}</div>
                  </div>
                </div>
              )}
              {res && !busy && (res.status === "ai_down" || res.status === "ai_limit" || res.status === "checks_failed") && (
                <>
                  <div className="warn">
                    <span><b>{res.status === "ai_limit" ? "AI limit reached." : res.status === "checks_failed" ? "The AI's answer didn't pass the checks." : "The AI is unavailable right now."}</b>{" "}
                      Here are the stories that best match your question.{res.status === "ai_limit" && " The free AI allows a few questions per minute; the nine brief questions below always work."}</span>
                    <button className="link" style={{ marginLeft: "auto" }} onClick={retry}>Try again</button>
                  </div>
                  <Minis ev={res.evidence} />
                </>
              )}
              {res && !busy && res.status === "unclear" && (
                <div className="warn"><span><b>I didn&rsquo;t understand that question.</b> This engine answers questions about what investors said about SIPs: why they start, stop, pause or keep going, payments, the app, returns and who they turn to. Try rephrasing, or pick a question below.</span></div>
              )}
              {res && !busy && res.status === "weak" && (
                <>
                  <div className="warn"><span><b>Not enough evidence.</b> The stories don&rsquo;t say enough about this to give an answer. {res.evidence.length ? "These are the closest matches." : "Try one of the starter questions."}</span></div>
                  {res.evidence.length > 0 && <Minis ev={res.evidence} />}
                </>
              )}
              {res && !busy && res.status === "advice" && res.evidence.length > 0 && (
                <><div className="sec" style={{ marginTop: 24 }}><div><div className="eyebrow">What others in similar situations said</div><p>Both ways: people who stopped and people who kept going.</p></div></div><Minis ev={res.evidence} /></>
              )}
            </div>
            {res && !busy && res.status === "answer" ? (
              <div className="panel">
                <div className="panel-head"><span><b>Evidence behind the answer</b><small>{res.evidence.length} stories · quotes verified</small></span></div>
                {res.evidence.map((e) => <Cite key={e.id} e={e} hl={hl === e.n} />)}
                <div className="cite"><Link className="link" href={res.exploreHref}>Open all {res.searched.toLocaleString("en-IN")} in Story Explorer &rarr;</Link></div>
              </div>
            ) : side}
          </div>
          {prompts}
        </>
      )}
    </div>
  );
}
