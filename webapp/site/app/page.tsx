import storiesJson from "@/data/stories.json";
import FindingsView, { type WorldQuote } from "@/components/FindingsView";
import { CUTS, F, QUESTION_ORDER, type Story } from "@/lib/data";

const STORIES = storiesJson as Story[];

const CUT_KEEP: Record<string, (s: Story) => boolean> = {
  all: () => true,
  first_time: (s) => s.grp === "first_time",
  groww: (s) => s.app === "groww" || (s.tags.platform ?? []).includes("groww"),
};

// one short, readable quote per world and cut, showing that world's top root cause
function pickQuote(cut: string, st: string, code: string | undefined): WorldQuote | null {
  const pool = STORIES.filter((s) => s.cls === "dropoff" && s.st === st && CUT_KEEP[cut](s) && s.quote.length >= 25 && s.quote.length <= 140);
  const hit = pool.filter((s) => code && (s.tags.root_cause ?? []).includes(code))
    .sort((a, b) => Number(b.grp === "first_time") - Number(a.grp === "first_time") || b.len - a.len)[0] ?? pool[0];
  return hit ? { id: hit.id, quote: hit.quote, src: hit.src, app: hit.app, sub: hit.sub, outcome: hit.outcome, grp: hit.grp } : null;
}

export default function Page() {
  const quotes: Record<string, Record<string, WorldQuote | null>> = {};
  for (const cut of Object.keys(CUT_KEEP)) {
    quotes[cut] = {};
    for (const st of ["app_review", "community"]) {
      const rc = Object.keys(CUTS[cut][st].root_cause).filter((c) => c !== "other")[0];
      quotes[cut][st] = pickQuote(cut, st, rc);
    }
  }
  const questions = QUESTION_ORDER.map((k) => {
    const q = F.questions[k];
    return {
      key: k, question: q.question, n: q.n, strength: q.strength,
      fields: Object.entries(q.fields).map(([f, v]: [string, any]) => ({
        field: f, n: v.n, strength: v.strength,
        top: Object.entries(v.all).slice(0, 3).map(([c, s]: [string, any]) => [c, s.share] as [string, number]),
      })),
    };
  });
  const svd = F.stayed_vs_dropoff;
  const pick = (field: string, code: string) => svd[field].find((r: any) => r.code === code);
  const diverge = [
    ["emotion", "angry_frustrated"], ["emotion", "calm_confident"], ["stage", "12m_plus"],
    ["expectation", "long_term_volatility_accepted"], ["checking_behaviour", "xirr"], ["metric_branch", "reliability"],
  ].map(([f, c]) => ({ field: f, code: c, ...pick(f, c) }));

  return (
    <FindingsView
      corpus={{ ...CUTS._corpus, stories: F.corpus.stories, dropoff: F.corpus.dropoff, stayed: F.corpus.stayed,
        question_items: F.corpus.question_items, stayed_community: F.corpus.by_source_type["stayed_story/community"],
        first_time: F.corpus.by_group["dropoff_story/first_time"] + F.corpus.by_group["stayed_story/first_time"],
        first_time_dropoff: CUTS._opportunities.n_first_time }}
      cuts={{ all: CUTS.all, first_time: CUTS.first_time, groww: CUTS.groww }}
      quotes={quotes}
      diverge={diverge}
      stayReason={F.stayed.stay_reason}
      needs={CUTS._opportunities.rows}
      questions={questions}
    />
  );
}
