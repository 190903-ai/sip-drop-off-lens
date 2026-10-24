// Ask the data: understanding, retrieval, checks. Server-only (imports the text excerpts).
import storiesJson from "@/data/stories.json";
import searchJson from "@/data/search.json";
import { CUTS, F, type Story } from "@/lib/data";
import { FIELD_LABELS, label, SOURCE_NAME } from "@/lib/labels";

const STORIES = storiesJson as Story[];
const TEXT = searchJson as Record<string, string>;

export type Chip = { text: string; tone: "g" | "" };
export type Evidence = {
  n: number; id: string; src: string; source: string; quote: string; tags: string[]; grp: string;
  outcome: string; cls: string; url: string | null; exact: boolean;
};
export type AskResult = {
  status: "answer" | "advice" | "ai_down" | "ai_limit" | "weak" | "checks_failed" | "unclear";
  question: string; chips: Chip[]; searched: number; exploreHref: string;
  paragraphs?: string[]; caveat?: string; evidence: Evidence[]; model?: string; removed?: number;
  cached?: boolean; message?: string;
};

type Plan = {
  grp?: string; cls?: "dropoff" | "stayed"; st?: string; app?: string; src?: string; opp?: boolean;
  fields: string[]; codes: Set<string>; terms: string[]; key?: string; topics: [RegExp, string[]][];
  recognised: boolean; // matched a topic, segment, outcome, app or source (not just the default fields)
};

// --- understanding ------------------------------------------------------------------------------
// pattern -> fields to summarise, codes to boost, and whether the question is narrow enough that only
// items about that topic are searched (by tag, or the pattern's words in the quote / AI reason)
// "the app keeps crashing" is about the app, not the market
const APP_TECH = /\b(app|website|platform|groww|coin|et ?money|paytm|ind ?money)\b[^.?]*\b(crash\w*|bugs?|buggy|glitch\w*|hangs?|hanging|freez\w*|slow|lag\w*|errors?|not (working|loading|opening))\b|\b(bugs?|buggy|glitch\w*|technical (issues?|problems?|glitch\w*)|app crash\w*)\b/i;
const VOLATILITY = /\b(loss|losses|negative|in the red|down \d+|fall(s|ing)?|fell|crash\w*|dips?|bear\w*|corrections?|volatil\w*|underperform\w*)\b/i;
const SOURCES: [RegExp, string][] = [
  [/\byoutube (comments?|viewers|users|videos?)\b|\b(on|in|from|under) youtube\b/i, "youtube"],
  [/\breddit(ors| users| posts| threads| comments| discussions)\b|\b(on|in|from) reddit\b|\br\/\w+/i, "reddit"],
  [/\bplay ?store\b|\bandroid reviews?\b/i, "playstore"],
  [/\bapp store\b|\bios reviews?\b/i, "appstore"],
  [/\btrading ?q ?(&|and)? ?a\b|\btradingqna\b/i, "tradingqna"],
  [/\bblogs?\b/i, "blog"],
];
const APPS: [RegExp, string][] = [[/groww/i, "groww"], [/et ?money/i, "etmoney"], [/zerodha|\bcoin\b/i, "coin"],
  [/paytm/i, "paytmmoney"], [/ind ?money/i, "indmoney"], [/kuvera/i, "kuvera"]];
// questions about where the opportunities are: answered from the opportunity comparison (cuts.json)
const OPPORTUNITY = /opportunit\w*|biggest (problems?|issues?|pain\w*|gaps?)|\bpriorit\w*|most (improve|impact\w*)|where (to|should \w+) focus|business metric|\bretention\b/i;
// a question must be about investing at all; nonsense and off-topic questions get "didn't understand"
const DOMAIN = /\b(sips?|invest\w*|mutual|funds?|mfs?|nav|returns?|markets?|portfolio\w*|money|apps?|savings?|xirr|equity|stocks?|amc|kyc|mandates?|debit\w*|instal\w*|pause\w*|stop\w*|redeem\w*|withdraw\w*|groww|zerodha|coin|paytm|demat|nifty|sensex|salary|income|beginners?)\b/i;

const TOPICS: [RegExp, string[], string[], boolean][] = [
  [/\b(payments?|mandates?|auto ?pay|autodebit|debit(ed)?|bounced?|instal?ments?|nach|upi)\b/i, ["root_cause", "stop_trigger", "unmet_need"],
    ["payment_plumbing", "payment_failure", "reliable_payment_recovery", "payment_mandate_status", "debit_after_cancel", "missing_notification"], true],
  [/\b(pause[sd]?|skip|modify|edit|cancel(led|s)?|outright)\b|change (the )?(amount|date)/i, ["action", "stop_trigger", "unmet_need"],
    ["flexible_pause_modify", "modify_blocked", "paused", "stopped", "attempted_blocked", "modify_sip"], true],
  [/\b(support|customer care|help ?desk|grievance)\b/i, ["root_cause", "stop_trigger", "unmet_need"],
    ["responsive_support", "support_failure", "complaint_escalation"], true],
  [APP_TECH, ["stop_trigger", "root_cause", "in_app_confusion"],
    ["app_malfunction", "navigation_ui", "data_discrepancy", "order_redemption_delay", "value_mismatch"], true],
  [VOLATILITY, ["stay_reason", "stop_trigger", "root_cause"],
    ["own_returns_negative_flat", "volatility_mismatch", "expectation_violation", "return_misreading", "market_news"], true],
  [/\b(advice|advis\w+|lean on|influenc\w*|who (do|did)|creators?|youtube|family|friends?)\b/i, ["influencer_source", "outside_app_workaround"],
    ["advisor_distributor", "youtube_creator", "family", "friend_colleague", "creator_comment", "family_friend", "advisor_ca", "advice_received", "borrowed_conviction"], true],
  [/\b(check\w*|how often|track\w*|monitor\w*|look at)\b/i, ["checking_behaviour", "check_frequency"], ["xirr", "daily_pnl", "current_value_amount", "returns_pct", "avoids_checking", "nav", "fund_level_returns"], false],
  [/\b(confus\w*|worr\w*|unclear|inside the app|in the app)\b/i, ["in_app_confusion"], ["value_mismatch", "return_figure_meaning", "payment_mandate_status", "charges_plan_type", "order_timeline"], false],
  [/outside the app|elsewhere|\b(forums?|reddit|google|research)\b/i, ["outside_app_workaround"], ["reddit_forum", "self_research", "creator_comment", "other_platform"], false],
  [/\b(needs?|lack\w*|wish\w*|missing|gaps?)\b/i, ["unmet_need"], [], false],
  [/why .*start|start(ed)? (a |their )?sip|\b(motivat\w*|expect\w*)\b/i, ["start_motivation", "expectation"], ["specific_goal", "wealth_returns", "family_friend_push", "saving_discipline"], false],
  [/\b(fees?|charges?|exit load|expense ratio|commissions?|regular plans?|direct plans?|penalt\w+)\b/i, ["root_cause", "stop_trigger", "unmet_need"], ["transparent_costs", "charge_penalty", "charges_plan_type"], true],
  [/\b(too many funds|overlap|consolidat\w*|clean ?up|rebalanc\w*)\b/i, ["root_cause", "behaviour_change"], ["portfolio_rationalisation", "portfolio_construction_help", "funds_consolidated", "restructured"], true],
  [/\b(income|salary|salaried|job|students?|age|segments?|career|retire\w*|homemakers?)\b/i, ["income_type", "life_stage", "source_of_money"], [], false],
  [/\b(cash|emergency|afford\w*|expenses|emi|loans?)\b/i, ["root_cause", "stop_trigger"], ["cashflow_rigidity", "cash_need_life_event", "affordable_amount"], true],
  [/\b(trust|scam|fraud|unsafe)\b/i, ["root_cause", "unmet_need"], ["platform_trust_erosion", "product_distrust", "consent_control"], true],
  [/\b(switch\w*|another app|other apps?|migrat\w*)\b/i, ["action", "stop_trigger"], ["switched_platform", "considering_switch_platform", "platform_change"], true],
  [/\b(months after|over time|habits?|behaviou?r)\b/i, ["behaviour_change"], ["checking_faded", "checking_rose", "amount_increased", "funds_added", "confidence_fell", "confidence_rose"], false],
];
const STOP = new Set("a an and are as at be by do does did for from has have how i in is it its of on or so that the their them they this to was were what when where which who why will with do people investors investor sip sips most more after".split(" "));

export function understand(question: string, key?: string): Plan {
  const q = question.toLowerCase();
  const plan: Plan = { fields: [], codes: new Set(), terms: [], key, topics: [], recognised: Boolean(key) };
  if (/first[- ]?time|new (investor|to)|beginner|newbie|just started|novice/.test(q)) plan.grp = "first_time";
  else if (/experienced|veteran|long[- ]time investor/.test(q)) plan.grp = "experienced";
  const stay = /\b(keep|kept|stay|stayed|continu|stick|hold on|keeps)/.test(q);
  const stop = /\b(stop|quit|cancel|drop|leave|left|pause|exit|give up|gave up)/.test(q);
  if (stay && !stop) plan.cls = "stayed";
  else if (stop && !stay && !/pause, or cancel|pause or cancel/.test(q)) plan.cls = "dropoff";
  plan.app = APPS.find(([re]) => re.test(q))?.[1];
  const source = SOURCES.find(([re]) => re.test(q));
  plan.src = source?.[1];
  if (!plan.src && /app (store )?reviews?/.test(q)) plan.st = "app_review";
  if (OPPORTUNITY.test(q)) { plan.opp = true; plan.cls = "dropoff"; plan.fields = ["unmet_need"]; }
  const appTech = APP_TECH.test(q);
  const qt = source ? q.replace(source[0], " ") : q; // "YouTube comments" names a source, not the topic "influenced by"
  for (const [re, fields, codes, narrow] of TOPICS) if (re.test(qt)) {
    if (re === VOLATILITY && appTech) continue;
    plan.recognised = true;
    codes.forEach((c) => plan.codes.add(c));
    if (plan.opp) continue; // the comparison covers every need; topics only steer which stories are cited
    fields.forEach((f) => plan.fields.includes(f) || plan.fields.push(f));
    if (narrow) plan.topics.push([re, codes]);
  }
  if (plan.grp || plan.cls || plan.app || plan.src || plan.st || plan.opp) plan.recognised = true;
  if (/complain/.test(q) && !plan.fields.includes("root_cause")) plan.fields.unshift("root_cause");
  if (!plan.fields.length) plan.fields = plan.cls === "stayed" ? ["stay_reason", "emotion"] : ["root_cause", "stop_trigger", "unmet_need"];
  plan.fields = plan.fields.slice(0, 3);
  plan.terms = [...new Set(q.replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter((t) => t.length > 2 && !STOP.has(t)))];
  return plan;
}

// nonsense ("asdfgh") or off-topic ("who won the match"): nothing recognised, and either no investing word or
// none of the question's words appear in any story
export function unclear(question: string, p: Plan) {
  if (p.recognised) return false;
  if (!DOMAIN.test(question)) return true;
  return !p.terms.some((t) => STORIES.some((s) => `${s.quote} ${TEXT[s.id] ?? ""}`.toLowerCase().includes(stem(t))));
}

function chips(p: Plan): Chip[] {
  const c: Chip[] = [];
  if (p.grp) c.push({ text: `${label(p.grp).toLowerCase()} investors`, tone: "g" });
  if (p.cls) c.push({ text: p.cls === "stayed" ? "kept going" : "stopped or wavering", tone: "g" });
  if (p.app) c.push({ text: `about ${label(p.app)}`, tone: "g" });
  if (p.src) c.push({ text: `from ${label(p.src)}`, tone: "g" });
  if (p.opp) c.push({ text: "opportunity areas compared", tone: "g" });
  if (p.st) c.push({ text: "app reviews", tone: "g" });
  for (const f of p.fields) c.push({ text: `topic: ${(FIELD_LABELS[f] ?? f).toLowerCase()}`, tone: "" });
  return c;
}

// --- retrieval ----------------------------------------------------------------------------------
const stem = (t: string) => t.slice(0, Math.max(4, Math.min(t.length, 6)));

const onTopic = (s: Story, p: Plan) => !p.topics.length || p.topics.some(([re, codes]) =>
  Object.values(s.tags).some((v) => v.some((c) => codes.includes(c))) || re.test(`${s.quote} ${s.why}`));

function pool(p: Plan) {
  return STORIES.filter((s) => onTopic(s, p) &&
    (!p.grp || s.grp === p.grp) && (!p.cls || s.cls === p.cls) && (!p.st || s.st === p.st) &&
    (!p.app || s.app === p.app || (s.tags.platform ?? []).includes(p.app)) && (!p.src || s.src === p.src) &&
    (!p.key || p.fields.some((f) => (s.tags[f] ?? []).some((v) => v !== "other"))));
}

function score(s: Story, p: Plan) {
  const hay = `${s.quote} ${s.why} ${TEXT[s.id] ?? ""}`.toLowerCase();
  let sc = 0;
  for (const t of p.terms) if (hay.includes(stem(t))) sc += 1;
  for (const vals of Object.values(s.tags)) for (const v of vals) if (p.codes.has(v)) sc += 2;
  for (const f of p.fields) if ((s.tags[f] ?? []).some((v) => v !== "other")) sc += 1.5;
  if (s.kind === "story") sc += 0.5;
  if (s.quote.length > 30) sc += 0.3;
  return sc;
}

export function retrieve(p: Plan, k = 12) {
  const all = pool(p);
  const ranked = all.map((s) => ({ s, sc: score(s, p) })).filter((x) => x.sc > 0).sort((a, b) => b.sc - a.sc);
  // keep variety: at most 4 stories from the same source
  const out: Story[] = [], per: Record<string, number> = {};
  for (const { s } of ranked) {
    if ((per[s.src] ?? 0) >= 4) continue;
    per[s.src] = (per[s.src] ?? 0) + 1;
    out.push(s);
    if (out.length >= k) break;
  }
  return { all, top: out, best: ranked[0]?.sc ?? 0 };
}

// shares over the searched pool (or the exact findings.json numbers for the nine brief questions)
type Stats = { field: string; n: number; codes: [string, number, number][]; line?: string }[];
const p100 = (x: number) => Math.round(x * 100);

export function stats(p: Plan, rows: Story[]): Stats {
  const out: Stats = [];
  if (p.key === "q7_continue_vs_drop") { // the comparison itself: stayed vs left / wobbling
    const q = F.questions.q7_continue_vs_drop;
    for (const [f, list] of Object.entries(q.differences) as [string, any[]][]) {
      const rowsF = list.filter((d) => d.code !== "other").slice(0, 3);
      if (!rowsF.length) continue;
      out.push({ field: f, n: q.n_stayed, codes: rowsF.flatMap((d) => [[d.code, 0, d.stayed], [d.code, 0, d.left_or_wobbling]] as [string, number, number][]),
        line: `${FIELD_LABELS[f] ?? f}, stayed (${q.n_stayed}) vs left or wobbling (${q.n_left_or_wobbling}): ` +
          rowsF.map((d) => `${label(d.code)} ${p100(d.stayed)}% vs ${p100(d.left_or_wobbling)}%`).join("; ") });
    }
  }
  if (p.key === "q8_segments") { // how each segment's people split between stayed and left
    for (const [f, segs] of Object.entries(F.questions.q8_segments.segment_outcomes) as [string, Record<string, any>][]) {
      const list = Object.entries(segs).filter(([, v]) => v.evidence !== "thin" && v.stayed_share != null);
      if (!list.length) continue;
      out.push({ field: f, n: 0, codes: list.map(([c, v]) => [c, v.n_with_outcome, v.stayed_share] as [string, number, number]),
        line: `${FIELD_LABELS[f] ?? f}, share who stayed (segments with 30+ items): ` +
          list.map(([c, v]) => `${label(c)} ${p100(v.stayed_share)}% stayed of ${v.n_with_outcome}`).join("; ") });
    }
  }
  if (p.opp && !p.key) { // the opportunity comparison: the same numbers as the Findings table
    const o = CUTS._opportunities;
    const list = (o.rows as any[]).filter((r) => r.stories >= 20);
    out.push({ field: "unmet_need", n: o.n_dropoff,
      codes: list.flatMap((r) => [[r.need, r.stories, r.share], [r.need, r.first_time, r.first_time_share], [r.need, 0, r.exit_rate]] as [string, number, number][]),
      line: `Unmet needs in the ${o.n_dropoff} drop-off stories (${o.n_first_time} of them first-time investors). Per need: drop-off stories (share of ${o.n_dropoff}); first-time investors (share of ${o.n_first_time}); share that fully exited:\n` +
        list.map((r) => `${label(r.need)}: ${r.stories} (${p100(r.share)}%); first-time ${r.first_time} (${p100(r.first_time_share)}%); fully exited ${p100(r.exit_rate)}%`).join("\n") });
    return out;
  }
  for (const f of p.fields) {
    if (p.key && F.questions[p.key]?.fields[f]) {
      const v = F.questions[p.key].fields[f];
      out.push({ field: f, n: v.n, codes: Object.entries(v.all).slice(0, 6).map(([c, s]: [string, any]) => [c, s.n, s.share]) });
      continue;
    }
    const have = rows.filter((s) => (s.tags[f] ?? []).some((v) => v !== "other"));
    const c: Record<string, number> = {};
    for (const s of have) for (const v of new Set(s.tags[f])) if (v !== "other") c[v] = (c[v] ?? 0) + 1;
    // share over every item searched, the same convention as the dashboard cuts (analyze.py shares())
    out.push({ field: f, n: rows.length, codes: Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([k, n]) => [k, n, n / (rows.length || 1)]) });
  }
  return out;
}

export function exploreHref(p: Plan) {
  const q = new URLSearchParams();
  if (p.grp) q.set("grp", p.grp);
  if (p.cls) q.set("outcome", p.cls);
  if (p.st) q.set("st", p.st);
  if (p.app) q.set("app", p.app);
  if (p.src) q.set("src", p.src);
  if (p.key) q.set("kind", "all");
  return `/stories?${q.toString()}`;
}

export function toEvidence(rows: Story[]): Evidence[] {
  return rows.map((s, i) => ({
    n: i + 1, id: s.id, src: s.src, source: SOURCE_NAME(s), quote: s.quote, grp: s.grp, outcome: s.outcome, cls: s.cls,
    tags: ["root_cause", "stop_trigger", "unmet_need", "stay_reason", "action"].flatMap((f) => (s.tags[f] ?? []).filter((v) => v !== "other")).slice(0, 2).map(label),
    url: s.url, exact: s.exact,
  }));
}

export function caveat(n: number, rows: Story[]) {
  const src: Record<string, number> = {};
  for (const s of rows) src[label(s.src)] = (src[label(s.src)] ?? 0) + 1;
  const [main, cnt] = Object.entries(src).sort((a, b) => b[1] - a[1])[0] ?? ["", 0];
  const mostly = rows.length && cnt / rows.length >= 0.5 ? `, mostly ${main}` : "";
  const size = n >= 100 ? "" : n >= 30 ? " A moderate amount of evidence." : " Thin evidence: read the stories before relying on this.";
  return `${n.toLocaleString("en-IN")} items searched${mostly}.${size} Quiet drop-offs rarely post, so engaged investors are over-represented. Treat this as a hypothesis to test in interviews, not a measured rate.`;
}

// --- advice guard -------------------------------------------------------------------------------
const PERSONAL = /\b(should i|shall i|do i need|can i|must i|is it (good|safe|right|wise|ok|okay)( for me)?|my (sip|sips|portfolio|fund|funds|money|investment)|which (fund|funds|sip)|best (fund|funds|sip|app)|recommend|suggest (a|me|some|any)|where (should|do) i invest|what should i)\b/i;
export const isPersonalAdvice = (q: string) => PERSONAL.test(q);

// --- checks on the model's answer ---------------------------------------------------------------
const ADVICE_OUT = /\b(you should|you must|we recommend|i recommend|i suggest|consider (investing|switching|stopping|continuing|pausing)|best fund|groww should|the app should|platforms? should|should (add|build|offer|introduce|provide|improve)|it is advisable|keep investing|don'?t stop|to (address|prevent|fix|reduce|solve|avoid) (this|these|that|such|drop))\b/i;
// a sentence: quoted spans are atomic (a "?" inside a quote doesn't split it); trailing citations stay attached
const SENTENCE = /(?:"[^"]*"|“[^”]*”|[^.!?"“])+(?:[.!?]+(?:\s*(?:\[\d+(?:\s*,\s*\d+)*\])+)?|$)/g;
const norm = (t: string) => t.toLowerCase().replace(/[‘’]/g, "'").replace(/[^a-z0-9' ]/g, " ").replace(/\s+/g, " ").trim();

export function check(paragraphs: string[], ev: Story[], st: Stats) {
  const allowed = new Set<number>();
  for (const s of st) for (const [, , share] of s.codes) { const v = Math.round(share * 100); allowed.add(v - 1).add(v).add(v + 1); }
  let removed = 0;
  const cited = new Set<number>();
  const out = paragraphs.map((para) => {
    let text = para.replace(/\s*\[(?!\d)[^\]]{0,12}\]/g, "").replace(/\s+/g, " ") // drop "[N/A]"-style non-citations
      .replace(/[“”]/g, '"'); // mixed curly and straight quotes break the sentence splitter, leaving fragments
    if ((text.match(/"/g) ?? []).length % 2) { const i = text.lastIndexOf('"'); text = text.slice(0, i) + text.slice(i + 1); }
    const sentences = text.match(SENTENCE) ?? [text];
    const keep = sentences.filter((sen) => {
      if (/^[\s*]*[,;:)\]\[]/.test(sen)) { removed++; return false; } // a fragment left over from a broken split
      const nums = [...sen.matchAll(/\[(\d+(?:\s*,\s*\d+)*)\]/g)].flatMap((m) => m[1].split(/\s*,\s*/).map(Number));
      const valid = nums.filter((n) => n >= 1 && n <= ev.length);
      const pcts = [...sen.matchAll(/(\d{1,3})\s?%/g)].map((m) => Number(m[1]));
      // every sentence needs a story citation, unless it only reports counts (and those are checked below)
      if (!valid.length && !(pcts.length && !/["“]/.test(sen))) { if (sen.trim()) removed++; return false; }
      if (ADVICE_OUT.test(sen)) { removed++; return false; }                       // no advice, no product solutions
      if (pcts.some((v) => !allowed.has(v))) { removed++; return false; }          // numbers must exist in the counts
      for (const m of sen.matchAll(/["“]([^"”]{12,})["”]/g)) {   // quotes must be verbatim in a cited story
        const qn = norm(m[1]);
        if (!valid.some((n) => norm(`${ev[n - 1].quote} ${TEXT[ev[n - 1].id] ?? ""}`).includes(qn))) { removed++; return false; }
      }
      valid.forEach((n) => cited.add(n));
      return true;
    });
    // at most 3 citations per sentence keeps the answer readable; the rest are still in the evidence pool
    return keep.map((sen) => {
      let seen = 0;
      if ((sen.match(/\*\*/g) ?? []).length % 2) sen = sen.replace(/\*\*/g, ""); // unbalanced bold: drop the markers
      return sen.replace(/\[(\d+(?:\s*,\s*\d+)*)\]/g, (_m, g: string) =>
        g.split(/\s*,\s*/).map(Number).filter((n: number) => n >= 1 && n <= ev.length && seen++ < 3).map((n: number) => `[${n}]`).join(""));
    }).join(" ").replace(/\s+/g, " ").replace(/\s+([.,;])/g, "$1").trim();
  }).filter(Boolean);
  return { paragraphs: out, removed, cited };
}

// --- prompt -------------------------------------------------------------------------------------
export const SYSTEM = `You describe what investors said in public posts about SIPs (Indian mutual fund systematic investment plans).
Rules:
- Use ONLY the numbered stories and the counts given. Never use outside knowledge.
- Every sentence about what people said must end with at least one citation like [2] or [1][4]. A sentence that only reports numbers from COUNTS may have no citation. Only numbers in brackets; never [N/A].
- Start the first sentence with the subject (who), not "These" or "They".
- Numbers: lead with the biggest patterns in COUNTS and give their percentage exactly as written there (e.g. "portfolio clean-up (26%)"). Never compute or invent other numbers.
- Cite at most 3 stories per sentence: pick the clearest ones.
- If you quote, copy words exactly from a story's quote, inside double quotes.
- Give NO advice of any kind: no investment advice, no fund names to pick, no suggestions for what anyone should do, and no product or feature suggestions for any app. Describe; do not prescribe.
- Do not say what would prevent, fix or reduce drop-off; only report what people said.
- If the stories do not answer the question, set enough_evidence to false.
- Plain, short English. 2 or 3 short paragraphs, 2–3 sentences each. Mark the 1–3 most important phrases with **bold**.
Return JSON: {"enough_evidence": true|false, "paragraphs": ["...", "..."]}`;

export function prompt(question: string, p: Plan, st: Stats, ev: Story[], searched: number) {
  const counts = st.map((s) => s.line ?? (`${FIELD_LABELS[s.field] ?? s.field} (share of ${s.n} items): ` +
    s.codes.map(([c, n, share]) => `${label(c)}: ${n} items (${p100(share)}%)`).join("; "))).join("\n");
  const stories = ev.map((s, i) => {
    const tags = Object.entries(s.tags).filter(([f]) => ["action", "root_cause", "stop_trigger", "unmet_need", "stay_reason", "emotion", "influencer_source", "checking_behaviour", "check_frequency", "in_app_confusion", "outside_app_workaround", "start_motivation", "behaviour_change"].includes(f))
      .map(([f, v]) => `${FIELD_LABELS[f]}: ${v.map(label).join(", ")}`).join("; ");
    return `[${i + 1}] ${SOURCE_NAME(s)} · ${label(s.grp)} investor · outcome: ${label(s.outcome)}\nQuote: "${s.quote}"\nTags: ${tags}\nContext: ${(TEXT[s.id] ?? "").slice(0, 380)}`;
  }).join("\n\n");
  const scope = chips(p).map((c) => c.text).join(", ") || "all stories";
  const opp = p.opp ? "\nThis question asks where the opportunities are. Compare the unmet needs using COUNTS: which are biggest overall, which are biggest among first-time investors, and which come with the most full exits. Say plainly that the counts show how often investors raised a problem, not how much solving it would change continuation. Do not say what to build or do.\n" : "";
  return `${SYSTEM}\n${opp}\nQUESTION: ${question}\nSCOPE: ${scope} (${searched} items searched)\n\nCOUNTS:\n${counts}\n\nSTORIES:\n${stories}`;
}

export { chips };
