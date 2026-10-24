import { CUTS, F, fmt } from "@/lib/data";
import { label } from "@/lib/labels";

export const metadata = { title: "How it works · SIP Drop-off Lens" };

const STAGES = [
  ["Collect", "Public posts, reviews and comments about SIPs: Reddit (via the Arctic Shift archive), Play Store and App Store reviews for six investing apps, TradingQ&A, YouTube comments and two personal-finance blogs.", "Python collectors · no accounts or paid APIs"],
  ["Clean", "Remove duplicates, cross-posts and non-SIP text; keep language, date, source and app. Usernames are never kept for display.", "clean.py"],
  ["Pre-filter", "Keyword and pattern searches pull likely stories, plus targeted searches for first-time investors, stayers and each brief question.", "prefilter*.py"],
  ["Read: story or not?", "AI reads each candidate and decides whether it is a personal SIP story (stopped, wavering or kept going) or a post that answers a brief question.", "Gemma 4 26B + Claude"],
  ["Deep tagging", "Each relevant item is tagged on 23 fields from a written codebook: action, trigger, root cause, unmet need, emotion, segments and more, with a verbatim evidence quote and a one-line reason.", "Claude (Sonnet) subagents · codebook v1.10"],
  ["Automatic checks", "Every code must exist in the codebook and every quote must be found word for word in the source text. Failures are reset to unknown and logged.", "validate_deep.py"],
  ["Human golden set", "25 posts labelled blind by a human, then every disagreement reviewed with both answers visible. Mistakes became rule fixes and corrections.", "Guided labelling page + score_golden.py"],
  ["Analyse and freeze", "Counts and shares for every cut (app reviews vs community, first-time, stayers vs leavers, with and without ET Money), then the data is frozen with fingerprints.", "analyze.py · frozen 24 Oct 2026"],
];

const HISTORY: [string, string][] = [
  ["v1", "Draft from 150 items (75 Play Store, 75 YouTube): voice, action, trigger, root cause, unmet need, emotion. Added metric branch, platform and a required reason for any “other”."],
  ["v1.1", "Re-checked on Reddit: added restructured (stop one fund, keep investing), portfolio clean-up, own portfolio review, portfolio construction help."],
  ["v1.2", "Trigger: tax rule change (new regime / 80C made the SIP pointless)."],
  ["v1.3", "Action: tried to stop but was blocked. Trigger: missing notification."],
  ["v1.4", "Investor experience (first-time / experienced) replaces a loose first-time flag; nearly stopped, and a wider “continued” so stayers can be compared."],
  ["v1.5", "Trigger: app malfunction (crash, login, a feature not working)."],
  ["v1.6", "Triggers: debited after cancel, support failure. New field: stay reason, for the control group."],
  ["v1.7", "Someone else’s conviction narrowed to a specific person steering the decision; 52 tags re-checked by hand, 44 re-coded (Correction 3)."],
  ["v1.8", "Behaviour change field for brief Q2; check frequency gains “when something happens”."],
  ["v1.9", "Behaviour change: switched plan / mode (SIP ↔ lump sum, regular → direct)."],
  ["v1.10", "Thinking of switching app split from thinking of stopping; app-switchers become their own outcome group (Correction 5)."],
];

export default function Page() {
  const C = CUTS._corpus;
  const src = Object.entries(C.by_source as Record<string, number>);
  const max = Math.max(...src.map(([, n]) => n));
  const stories = F.corpus.by_source as Record<string, number>;
  return (
    <>
      <div className="page-head"><div>
        <div className="eyebrow">Method</div><h1>How it works</h1>
        <p>An eight-stage pipeline turns {fmt(C.clean)} public SIP posts into {fmt(F.corpus.stories)} tagged investor stories and {fmt(F.corpus.question_items)} related posts. AI does the reading and tagging; code checks every quote; a human golden set checks the AI.</p>
      </div></div>

      <div className="stages">
        {STAGES.map(([t, d, tool], i) => (
          <div className="card stage" key={t}><div className="num">{i + 1}</div><h3>{t}</h3><p>{d}</p><div className="tool">{tool}</div></div>
        ))}
      </div>

      <div className="sec"><div><div className="eyebrow">Sources and volumes</div><h2>Where the {fmt(C.clean)} items came from</h2>
        <p>Clean items per source, and how many of the {fmt(F.corpus.stories)} personal stories each one gave.</p></div></div>
      <div className="panel tablewrap">
        <table>
          <thead><tr><th>Source</th><th>Clean items</th><th style={{ width: 240 }}>Share of corpus</th><th>Stories</th></tr></thead>
          <tbody>
            {src.map(([k, n]) => {
              const [s, app] = k.split("/");
              return (
                <tr key={k}>
                  <td className="need">{app ? `${label(s)} · ${label(app)}` : label(s)}</td>
                  <td>{fmt(n)}</td>
                  <td><div className="score"><div className="track"><div className="fill" style={{ width: `${Math.max(1, Math.round((n / max) * 100))}%` }} /></div><b>{((n / C.clean) * 100).toFixed(1)}%</b></div></td>
                  <td>{stories[k] ?? (app ? 0 : stories[s] ?? 0)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="meta" style={{ marginTop: 14 }}>App Store reviews were short and gave no personal stories, but some answer the brief questions. {fmt(C.story_candidates)} story candidates and {fmt(C.question_candidates)} question candidates were read by AI.</p>

      <div className="sec"><div><div className="eyebrow">Codebook history</div><h2>v1 &rarr; v1.10: every change had a reason</h2>
        <p>Codes were added only when real posts didn&rsquo;t fit, and narrowed when a check showed they claimed too much.</p></div></div>
      <div className="panel timeline">
        {HISTORY.map(([v, d]) => <div className="tl" key={v}><b className="v">{v}</b><span>{d}</span></div>)}
      </div>

      <div className="sec"><div><div className="eyebrow">Ask the Data</div><h2>How a question is answered</h2></div></div>
      <div className="panel" style={{ padding: "22px 24px" }}>
        <div className="prose">
          <p><b>1. Understand.</b> The question is mapped to filters (first-time, stopped or stayed, Groww, app reviews) and topics (codebook fields). These show as &ldquo;Understood as&rdquo; chips.</p>
          <p><b>2. Retrieve.</b> Tag filters plus keyword search over the tagged stories pick the 12 most relevant items, with at most 4 from one source. No vector database.</p>
          <p><b>3. Write.</b> Gemma 4 (backup: Gemini Flash-Lite) writes a short answer from those stories and the counts only.</p>
          <p><b>4. Check.</b> Sentences without a citation, with a percentage not in the counts, with a quote not found word for word, or with advice are removed before the answer is shown.</p>
          <p><b>5. Fall back.</b> The nine brief questions are saved in advance. If the AI is down or out of quota, the best-matching stories are shown instead; if the stories say too little, the answer is &ldquo;not enough evidence&rdquo;.</p>
        </div>
      </div>
    </>
  );
}
