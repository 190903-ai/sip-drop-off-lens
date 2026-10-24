import { F } from "@/lib/data";

export const metadata = { title: "Limitations · SIP Drop-off Lens" };

export default function Page() {
  const s = F.corpus.by_source as Record<string, number>;
  const q4 = F.questions.q4_checking.fields.check_frequency;
  const LIMITS: [string, string, string, string][] = [
    ["Bias", "Survivorship and loudness bias", "People who quietly stop a SIP rarely post about it. The stories over-represent engaged, upset or curious investors, so shares here are not drop-off rates.", "Treat every finding as a hypothesis for user interviews, not a measured rate."],
    ["Sample", "Public posts are not a random sample", "Reddit, app reviews and forums each attract a different kind of writer. App reviews are complaints by design; Reddit leans towards salaried, English-speaking writers.", "Patterns are read by source type: app reviews show what broke, community posts show intent."],
    ["Coverage", "No X (Twitter), Instagram or Quora", "Social media was out of scope, and Quora blocked collection. Investors who talk mainly there are missing.", "The gap is noted wherever segment findings are used."],
    ["Coverage", "Some sources are small", `Blogs gave ${s.blog ?? 24} stories and INDmoney ${s["playstore/indmoney"] ?? 16}: under 30 each, so they are never reported on their own.`, "Shares are only shown for groups of 30 or more."],
    ["Coverage", "Reddit collection stopped early", "By decision on 24 Oct: r/IndianStreetBets and r/StockMarketIndia were not collected, nor Reddit history from Oct 2022 to Sep 2024.", "The frozen corpus is what every number on this site uses."],
    ["Evidence", "How often investors check is only moderate", `Only ${q4.n} items say how often they check (strength: ${q4.strength}). People rarely state it in public.`, "Interviews will cover check frequency directly."],
    ["AI", "Tags are AI-made, checked on a sample", "The golden set is 25 posts. Action and root cause agree with the reviewed answers 69% of the time, below the 80% bar.", "Read action and root-cause splits as directional; the AI Evidence Log has the details."],
    ["Scope", "No advice, no solutions", "The engine only describes what investors said. It does not recommend funds, say what anyone should do, or propose product features.", "Personal questions get a pointer to a SEBI-registered adviser."],
  ];
  return (
    <>
      <div className="page-head"><div>
        <div className="eyebrow">Method</div><h1>Limitations</h1>
        <p>What this engine can&rsquo;t tell you, and how each gap is handled. Read these before using any number on this site.</p>
      </div></div>
      <div className="limits">
        {LIMITS.map(([tag, t, d, so]) => (
          <div className="card limit" key={t}><span className="chip a">{tag}</span><h3>{t}</h3><p>{d}</p><p className="so"><b>How it&rsquo;s handled:</b> {so}</p></div>
        ))}
      </div>
    </>
  );
}
