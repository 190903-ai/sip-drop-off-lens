import { NextResponse } from "next/server";
import cachedJson from "@/data/cached.json";
import {
  type AskResult, caveat, check, chips, exploreHref, isPersonalAdvice, prompt, retrieve, stats, toEvidence, unclear, understand,
} from "@/lib/ask";

export const runtime = "nodejs";
export const maxDuration = 60;

// Gemma first; Flash-Lite as backup, tried twice because Gemma's failures are usually timeouts
const MODELS = [["gemma-4-26b-a4b-it", "Gemma 4"], ["gemini-3.5-flash-lite", "Gemini Flash-Lite"], ["gemini-3.5-flash-lite", "Gemini Flash-Lite"]] as const;
// Gemini models accept a response schema, which stops malformed JSON; Gemma models don't
const SCHEMA = { type: "object", properties: { enough_evidence: { type: "boolean" }, paragraphs: { type: "array", items: { type: "string" } } },
  required: ["enough_evidence", "paragraphs"] };
const CACHED = cachedJson as Record<string, AskResult>;
const normQ = (q: string) => q.toLowerCase().replace(/[^a-z0-9 ]/g, "").replace(/\s+/g, " ").trim();
const recent = new Map<string, AskResult>(); // per-instance memo of fresh answers

class Limit extends Error {}

async function callModel(model: string, text: string, ms: number): Promise<any> {
  const key = process.env.GEMINI_API_KEY;
  if (!key) throw new Error("no key");
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), ms);
  try {
    const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
      method: "POST", signal: ctl.signal,
      headers: { "content-type": "application/json", "x-goog-api-key": key },
      body: JSON.stringify({
        contents: [{ role: "user", parts: [{ text }] }],
        generationConfig: { temperature: 0.2, responseMimeType: "application/json", maxOutputTokens: 1500,
          ...(model.startsWith("gemini") ? { responseSchema: SCHEMA } : {}) },
      }),
    });
    if (r.status === 429) throw new Limit("rate limited");
    if (!r.ok) throw new Error(`model ${r.status}`);
    const j = await r.json();
    const out = (j.candidates?.[0]?.content?.parts ?? []).filter((x: any) => !x.thought).map((x: any) => x.text ?? "").join("");
    const body = out.trim().replace(/^```(?:json)?/, "").replace(/```$/, "");
    return JSON.parse(body.slice(body.indexOf("{"), body.lastIndexOf("}") + 1)); // ignore any text around the JSON
  } finally {
    clearTimeout(timer);
  }
}

export async function POST(req: Request) {
  let body: any;
  try { body = await req.json(); } catch { return NextResponse.json({ error: "bad request" }, { status: 400 }); }
  const question = String(body.question ?? "").trim().slice(0, 300);
  const key = typeof body.key === "string" && /^q\d_\w+$/.test(body.key) ? body.key : undefined;
  if (!question && !key) return NextResponse.json({ error: "empty question" }, { status: 400 });
  // cached answers are re-generated only by the local precompute script
  const fresh = Boolean(body.fresh) && process.env.ALLOW_PRECOMPUTE === "1";

  if (!fresh) {
    const hit = (key && CACHED[key]) || CACHED[normQ(question)] || recent.get(normQ(question));
    if (hit) return NextResponse.json({ ...hit, cached: true });
  }

  const plan = understand(question, key);
  if (key) { // the nine brief questions: answer from the codebook fields analyze.py uses
    const { F } = await import("@/lib/data");
    plan.fields = Object.keys(F.questions[key].fields).slice(0, 3);
    plan.grp = undefined; plan.cls = undefined; plan.app = undefined; plan.st = undefined; plan.src = undefined; plan.opp = undefined; plan.topics = [];
  }
  const { all, top, best } = retrieve(plan);
  const base = { question: question || key!, chips: chips(plan), searched: all.length, exploreHref: exploreHref(plan) };
  // "closest matches" only make sense when the question was recognised as being about something in the data
  const closest = plan.codes.size || plan.grp || plan.cls || plan.app ? toEvidence(top.slice(0, 6)) : [];

  if (!key && isPersonalAdvice(question)) {
    // describe what others did, both ways; no model call
    const stopped = top.filter((s) => s.cls === "dropoff").slice(0, 2);
    const stayed = retrieve({ ...plan, cls: "stayed" }).top.slice(0, 2);
    return NextResponse.json({ ...base, status: "advice", evidence: toEvidence([...stopped, ...stayed]) } satisfies AskResult);
  }
  if (!key && unclear(question, plan)) {
    return NextResponse.json({ ...base, chips: [], searched: 0, status: "unclear", evidence: [] } satisfies AskResult);
  }
  if (all.length < 5 || best < 2 || top.length < 3) {
    return NextResponse.json({ ...base, status: "weak", evidence: closest } satisfies AskResult);
  }

  const st = stats(plan, all);
  const text = prompt(question || key!, plan, st, top, all.length);
  let limited = false, failedChecks = false;
  for (const [model, name] of MODELS) {
    try {
      const out = await callModel(model, text, model.startsWith("gemma") ? 25000 : 15000);
      if (out?.enough_evidence === false) {
        return NextResponse.json({ ...base, status: "weak", evidence: closest } satisfies AskResult);
      }
      const paras = (Array.isArray(out?.paragraphs) ? out.paragraphs : []).filter((x: unknown) => typeof x === "string");
      const checked = check(paras, top, st);
      if (!checked.paragraphs.length) { failedChecks = true; continue; } // try the backup model before giving up
      // renumber citations to the stories actually cited, in order of first use
      const order: number[] = [];
      for (const p of checked.paragraphs) for (const m of p.matchAll(/\[(\d+)\]/g)) if (!order.includes(+m[1])) order.push(+m[1]);
      const paragraphs = checked.paragraphs.map((p) => p.replace(/\[(\d+)\]/g, (_x, n) => `[${order.indexOf(+n) + 1}]`));
      const result: AskResult = {
        ...base, status: "answer", paragraphs, caveat: caveat(all.length, all), model: name, removed: checked.removed,
        evidence: toEvidence(order.map((n) => top[n - 1])),
      };
      if (!fresh) recent.set(normQ(question), result);
      return NextResponse.json(result);
    } catch (e) {
      if (e instanceof Limit) limited = true;
      console.error(`ask: ${model} failed: ${(e as Error).message}`); // never logs the key or prompt
    }
  }
  return NextResponse.json({ ...base, status: failedChecks ? "checks_failed" : limited ? "ai_limit" : "ai_down", evidence: toEvidence(top.slice(0, 6)) } satisfies AskResult);
}
