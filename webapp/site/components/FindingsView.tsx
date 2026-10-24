"use client";
import Link from "next/link";
import { useState } from "react";
import { label, pct, SOURCE_NAME } from "@/lib/labels";
import { fmt, NEED_DESC, top, type Share } from "@/lib/data";

export type WorldQuote = { id: string; quote: string; src: string; app: string | null; sub: string | null; outcome: string; grp: string };
type World = { n: number; root_cause: Share; stop_trigger: Share; unmet_need: Share };
type Cut = { n: number; first_time: number; app_review: World; community: World; first_time_root: Share };

const CUT_NAMES: [string, string][] = [["all", "All"], ["first_time", "First-time"], ["groww", "Groww only"]];
const CUT_QS: Record<string, string> = { all: "", first_time: "&grp=first_time", groww: "&app=groww" };
const CUT_DESC: Record<string, string> = {
  all: "all drop-off stories",
  first_time: "first-time investors only",
  groww: "stories about Groww only",
};

function WorldBars({ w }: { w: World }) {
  const rows: [string, number][] = [
    ...top(w.root_cause, 2).map(([c, v]) => [label(c), v.share] as [string, number]),
    ...top(w.stop_trigger, 1).map(([c, v]) => [`Trigger: ${label(c).toLowerCase()}`, v.share] as [string, number]),
    ...top(w.unmet_need, 1).map(([c, v]) => [`Need: ${label(c).toLowerCase()}`, v.share] as [string, number]),
  ];
  return (
    <div className="bars">
      {rows.map(([l, s]) => (
        <div className="bar" key={l}>
          <span>{l}</span>
          <div className="track"><div className="fill" style={{ width: `${Math.round(s * 100)}%` }} /></div>
          <span className="pct">{pct(s)}</span>
        </div>
      ))}
    </div>
  );
}

export default function FindingsView(p: {
  corpus: any; cuts: Record<string, Cut>; quotes: Record<string, Record<string, WorldQuote | null>>;
  diverge: any[]; stayReason: Share; needs: any[]; questions: any[];
}) {
  const [cut, setCut] = useState("all");
  const [allNeeds, setAllNeeds] = useState(false);
  const [rankFt, setRankFt] = useState(false);
  const c = p.cuts[cut];
  const C = p.corpus;
  const qs = CUT_QS[cut];
  const needs = [...p.needs].sort((a, b) => rankFt ? b.first_time - a.first_time || b.stories - a.stories : b.stories - a.stories);
  const maxNeed = Math.max(...p.needs.map((u) => (rankFt ? u.first_time : u.stories)), 1);
  const thin = (n: number) => n < 30;

  return (
    <div className="pg-find">
      <div className="page-head">
        <div>
          <div className="eyebrow">SIP drop-off overview</div>
          <h1>Why SIPs stop before month 12</h1>
          <p>{fmt(C.stories)} personal stories from public app reviews, Reddit, forums, YouTube and blogs, where someone stopped, nearly stopped or kept going. <Link className="link" style={{ fontSize: "inherit" }} href="/how-it-works">How they were found &rarr;</Link></p>
        </div>
      </div>

      <div className="sec"><div><div className="eyebrow">Headline finding</div><h2>Two drop-off worlds, with different causes</h2>
        <p>Showing {CUT_DESC[cut]}: {fmt(c.n)} drop-off stories.</p></div>
        <div className="cut" role="group" aria-label="Which stories to count">
          {CUT_NAMES.map(([k, n]) => (
            <button key={k} className={cut === k ? "on" : ""} aria-pressed={cut === k} onClick={() => setCut(k)}>{n}</button>
          ))}
        </div>
      </div>
      <div className="worlds">
        <div className="world app">
          <div className="tag">App reviews · {c.app_review.n} stories</div>
          <h3>The app broke their trust</h3>
          <div className="sub">Reliability branch: the SIP failed, not the investor</div>
          {thin(c.app_review.n) ? <p className="sub" style={{ margin: "24px 0" }}>Too few stories in this cut to show shares (under 30).</p> : <WorldBars w={c.app_review} />}
          {p.quotes[cut].app_review && <div className="wq">
            <p className="quote">{p.quotes[cut].app_review!.quote}</p>
            <p className="meta" style={{ marginTop: 8 }}>{SOURCE_NAME(p.quotes[cut].app_review!)} · {label(p.quotes[cut].app_review!.outcome).toLowerCase()} · <Link className="link" href={`/stories?outcome=dropoff&st=app_review${qs}`}>See {c.app_review.n} stories &rarr;</Link></p>
          </div>}
        </div>
        <div className="world com">
          <div className="tag">Reddit, forums, YouTube, blogs · {c.community.n} stories</div>
          <h3>They second-guess their own portfolio</h3>
          <div className="sub">Intent branch: portfolio doubts, returns, cash flow</div>
          {thin(c.community.n) ? <p className="sub" style={{ margin: "24px 0" }}>Too few stories in this cut to show shares (under 30).</p> : <WorldBars w={c.community} />}
          {p.quotes[cut].community && <div className="wq">
            <p className="quote">{p.quotes[cut].community!.quote}</p>
            <p className="meta" style={{ marginTop: 8 }}>{SOURCE_NAME(p.quotes[cut].community!)} · {p.quotes[cut].community!.grp === "first_time" ? "first-time investor" : label(p.quotes[cut].community!.outcome).toLowerCase()} · <Link className="link" href={`/stories?outcome=dropoff&st=community${qs}`}>See {c.community.n} stories &rarr;</Link></p>
          </div>}
        </div>
      </div>
      <div className="bridge"><div>
        First-time investors ({c.first_time}) {cut === "first_time" ? "appear in" : "span"} both worlds:{" "}
        {top(c.first_time_root, 3).map(([code, v], i) => (
          <span key={code}>{i ? ", " : ""}{i === 0 ? <b>{label(code).toLowerCase()} {pct(v.share)}</b> : <>{label(code).toLowerCase()} {pct(v.share)}</>}</span>
        ))}
      </div></div>

      <div className="sec"><div><div className="eyebrow">The control group</div><h2>Stayers vs leavers: what differs in their stories</h2></div></div>
      <div className="panel split">
        <div className="intro">
          <b style={{ fontSize: 14 }}>{C.stayed} kept going · {C.dropoff} stopped or wavering</b>
          <p>Stayers are calmer, further in, and more often check XIRR than the rupee value. {pct(p.stayReason.long_horizon_belief?.share)} of stayers say they invest for the long horizon.</p>
          <div className="legend"><span><i className="dot" style={{ background: "var(--leave)" }} />Stopped / wavering ({C.dropoff})</span><span><i className="dot" style={{ background: "var(--green)" }} />Kept going ({C.stayed})</span></div>
          <div className="note"><b>Read with care:</b> most stayers don&rsquo;t say <i>why</i> they stayed, and {C.stayed_community} of {C.stayed} come from forums. Interviews will fill this gap.</div>
        </div>
        <div className="chart">
          <div className="dhead"><span>Stopped</span><span>Signal</span><span>Kept going</span></div>
          {p.diverge.map((r) => (
            <div className="drow" key={r.code}>
              <div className="left"><span className="v">{pct(r.dropoff)}</span><div className="b leave" style={{ width: `${Math.max(1, Math.round(r.dropoff * 100))}%` }} /></div>
              <div className="label">{r.code === "12m_plus" ? "Investing 12+ months" : r.code === "xirr" ? "Checks XIRR" : r.code === "reliability" ? "App reliability problem" : label(r.code)}</div>
              <div className="right"><div className="b stay" style={{ width: `${Math.max(1, Math.round(r.stayed * 100))}%` }} /><span className="v">{pct(r.stayed)}</span></div>
            </div>
          ))}
        </div>
      </div>

      <div className="sec">
        <div><div className="eyebrow">Opportunity areas</div><h2>What investors lacked, compared</h2></div>
        <div className="cut" role="group" aria-label="Rank by">
          <button className={rankFt ? "" : "on"} aria-pressed={!rankFt} onClick={() => setRankFt(false)}>All drop-offs</button>
          <button className={rankFt ? "on" : ""} aria-pressed={rankFt} onClick={() => setRankFt(true)}>First-time investors</button>
        </div>
      </div>
      <div className="panel tablewrap">
        <table>
          <thead><tr><th>Unmet need (as described by investors)</th><th style={{ width: 190 }}>{rankFt ? `First-time (of ${C.first_time_dropoff})` : `Drop-off stories (of ${C.dropoff})`}</th><th>{rankFt ? "All drop-offs" : "First-time"}</th><th>In first 12 months</th><th>Fully exited</th><th /></tr></thead>
          <tbody>
            {needs.slice(0, allNeeds ? undefined : 5).map((u) => (
              <tr key={u.need}>
                <td className="need">{label(u.need)}<small>{NEED_DESC[u.need]}</small></td>
                <td><div className="score"><div className="track"><div className="fill" style={{ width: `${Math.round(((rankFt ? u.first_time : u.stories) / maxNeed) * 100)}%` }} /></div><b>{rankFt ? u.first_time : u.stories}</b><small>{pct(rankFt ? u.first_time_share : u.share)}</small></div></td>
                <td>{rankFt ? u.stories : u.first_time}</td>
                <td>{u.first_year} <small className="muted">of {u.stage_known}</small></td>
                <td>{pct(u.exit_rate)}</td>
                <td><Link className="link" href={`/stories?outcome=dropoff&need=${u.need}${rankFt ? "&grp=first_time" : ""}`}>Stories &rarr;</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="sec" style={{ marginTop: 10 }}>
        <p className="meta">A story can mention several needs. &ldquo;In first 12 months&rdquo; = stories that say how long they had been investing and it was under a year (of those that say). &ldquo;Fully exited&rdquo; = stopped, redeemed or switched app. This compares problem areas; it doesn&rsquo;t say what to build.</p>
        <button className="link" onClick={() => setAllNeeds(!allNeeds)}>{allNeeds ? <>Show top 5 &uarr;</> : <>Show all {p.needs.length} &darr;</>}</button>
      </div>

      <div className="sec"><div><div className="eyebrow">The brief&rsquo;s nine questions</div><h2>What the evidence says, and how much there is</h2>
        <p>These use all {fmt(C.stories + C.question_items)} relevant items, so they don&rsquo;t change with the filter above.</p></div></div>
      <div className="qgrid">
        {p.questions.map((q, i) => (
          <div className="card qcard" key={q.key}>
            <div className="qn"><span>QUESTION {i + 1}</span></div>
            <h3>{q.question}</h3>
            <ul>
              {q.fields[0].top.map(([code, s]: [string, number]) => (
                <li key={code}><span>{label(code)}</span><div className="track"><div className="fill" style={{ width: `${Math.round(s * 100)}%` }} /></div><b className="pct">{pct(s)}</b></li>
              ))}
            </ul>
            <p className="meta">{q.fields.map((f: any) => `${f.field.replace(/_/g, " ")} ${f.n}${f.strength !== "strong" ? ` (${f.strength})` : ""}`).join(" · ")}</p>
            <div className="foot"><span className="meta">{fmt(q.n)} items</span><Link className="link" href={`/ask?q=${q.key}`}>Read the answer &rarr;</Link></div>
          </div>
        ))}
      </div>
    </div>
  );
}
