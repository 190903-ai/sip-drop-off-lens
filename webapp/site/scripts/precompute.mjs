// Saves answers for the nine brief questions and the six starter prompts into data/cached.json,
// so they work with no AI. Run against a local dev server with ALLOW_PRECOMPUTE=1:
//   node scripts/precompute.mjs [baseUrl] [only-key-or-question]
import { readFileSync, writeFileSync } from "node:fs";

const BASE = process.argv[2] ?? "http://localhost:3123";
const ONLY = process.argv[3];
const F = JSON.parse(readFileSync("data/findings.json", "utf8"));
const STARTERS = [
  "Why do first-time investors stop their SIP?",
  "What goes wrong with SIP payments and mandates?",
  "What keeps people investing after a loss?",
  "Do people pause, or cancel outright?",
  "What do Groww users complain about most?",
  "Who do new investors lean on for advice?",
];
const normQ = (q) => q.toLowerCase().replace(/[^a-z0-9 ]/g, "").replace(/\s+/g, " ").trim();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const jobs = [
  ...Object.entries(F.questions).map(([key, q]) => ({ id: key, body: { question: q.question, key } })),
  ...STARTERS.map((q) => ({ id: normQ(q), body: { question: q } })),
].filter((j) => !ONLY || j.id === ONLY || j.body.question === ONLY);

const cached = JSON.parse(readFileSync("data/cached.json", "utf8"));
for (const job of jobs) {
  for (let attempt = 1; attempt <= 4; attempt++) {
    const r = await fetch(`${BASE}/api/ask`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ ...job.body, fresh: true }) });
    const j = await r.json();
    console.log(`${job.id}: ${j.status} (${j.model ?? "-"}, removed ${j.removed ?? 0}, attempt ${attempt})`);
    if (j.status === "answer") {
      delete j.cached;
      cached[job.id] = { ...j, savedAt: "2026-10-24" };
      writeFileSync("data/cached.json", JSON.stringify(cached, null, 1));
      break;
    }
    await sleep(20000);
  }
  await sleep(8000); // stay under Gemma's free tokens-per-minute cap
}
