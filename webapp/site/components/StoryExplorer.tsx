"use client";
import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { FIELD_LABELS, label, SOURCE_NAME } from "@/lib/labels";
import type { Story } from "@/lib/data";

const SRC_ICON: Record<string, [string, string]> = {
  reddit: ["r/", "#ff5700"], playstore: ["▶", "#01875f"], appstore: ["", "#1c1c1e"], youtube: ["▶", "#e62117"],
  tradingqna: ["Q", "#387ed1"], blog: ["B", "#7c5cc4"],
};
const PAGE = 30;
// filter -> tag field; outcome / experience / source / kind are story-level
const TAG_FILTERS: [string, string][] = [["rc", "root_cause"], ["tr", "stop_trigger"], ["need", "unmet_need"], ["sr", "stay_reason"]];

export default function StoryExplorer() {
  const router = useRouter();
  const sp = useSearchParams();
  const [data, setData] = useState<Story[] | null>(null);
  const [err, setErr] = useState(false);
  const [shown, setShown] = useState(PAGE);
  const [q, setQ] = useState(sp.get("q") ?? "");

  useEffect(() => {
    fetch("/data/stories.json").then((r) => r.json()).then(setData).catch(() => setErr(true));
  }, []);

  // the two cards fill the rest of the window, so each scrolls on its own
  useEffect(() => {
    const el = document.getElementById("ex-cols");
    if (!el) return;
    const fit = () => el.style.setProperty("--ex-h", `${Math.max(420, window.innerHeight - (el.getBoundingClientRect().top + window.scrollY) - 24)}px`);
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);
  useEffect(() => { document.querySelector("#ex-cols .list")?.scrollTo(0, 0); }, [sp, q]);

  const f = {
    kind: sp.get("kind") ?? "story", outcome: sp.get("outcome") ?? "all", grp: sp.get("grp") ?? "",
    src: sp.get("src") ?? "", st: sp.get("st") ?? "", app: sp.get("app") ?? "",
    sort: sp.get("sort") ?? "detail",
    ...Object.fromEntries(TAG_FILTERS.map(([k]) => [k, sp.get(k) ?? ""])),
  } as Record<string, any>;

  const set = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(sp.toString());
    for (const [k, v] of Object.entries(patch)) (v ? next.set(k, v) : next.delete(k));
    setShown(PAGE);
    router.replace(`/stories?${next.toString()}`, { scroll: false });
  };

  // filtered without the text search, so option counts stay stable while typing
  const base = useMemo(() => (data ?? []).filter((s) =>
    (f.kind === "all" || s.kind === f.kind) &&
    (f.outcome === "all" || (f.outcome === "dropoff" ? s.cls === "dropoff" : f.outcome === "stayed" ? s.cls === "stayed" : s.outcome === f.outcome)) &&
    (!f.grp || s.grp === f.grp) && (!f.src || s.src === f.src) && (!f.st || s.st === f.st) &&
    (!f.app || s.app === f.app || (f.app === "groww" && (s.tags.platform ?? []).includes("groww"))) &&
    TAG_FILTERS.every(([k, field]) => !f[k] || (s.tags[field] ?? []).includes(f[k]))
  ), [data, sp]); // eslint-disable-line react-hooks/exhaustive-deps

  const terms = q.toLowerCase().split(/\s+/).filter((t) => t.length > 1);
  const list = useMemo(() => {
    const hits = terms.length ? base.filter((s) => {
      const hay = `${s.quote} ${s.why}`.toLowerCase();
      return terms.every((t) => hay.includes(t));
    }) : base;
    return [...hits].sort((a, b) => f.sort === "newest" ? b.date.localeCompare(a.date) : b.len - a.len);
  }, [base, q, f.sort]); // eslint-disable-line react-hooks/exhaustive-deps

  const counts = (field: string) => {
    const c: Record<string, number> = {};
    for (const s of base) for (const v of s.tags[field] ?? []) c[v] = (c[v] ?? 0) + 1;
    return Object.entries(c).sort((a, b) => b[1] - a[1]);
  };
  const countBy = (key: "grp" | "src") => {
    const c: Record<string, number> = {};
    for (const s of base) c[s[key]] = (c[s[key]] ?? 0) + 1;
    return Object.entries(c).sort((a, b) => b[1] - a[1]);
  };
  const active = ["grp", "src", "st", "app", ...TAG_FILTERS.map(([k]) => k)].filter((k) => f[k]).length
    + (f.outcome !== "all" ? 1 : 0) + (f.kind !== "story" ? 1 : 0);

  const Select = ({ k, field, all, opts }: { k: string; field?: string; all: string; opts?: [string, number][] }) => {
    const o = opts ?? counts(field!);
    const cur = f[k];
    return (
      <select className={`select${cur ? " set" : ""}`} value={cur} onChange={(e) => set({ [k]: e.target.value || null })} aria-label={all}>
        <option value="">{all}</option>
        {cur && !o.some(([c]) => c === cur) && <option value={cur}>{label(cur)} (0)</option>}
        {o.map(([c, n]) => <option key={c} value={c}>{label(c)} ({n})</option>)}
      </select>
    );
  };

  const describe = [
    f.kind === "item" ? "other relevant posts" : f.kind === "all" ? "stories and posts" : "stories",
    f.grp && `${label(f.grp).toLowerCase()} investors`,
    f.outcome === "dropoff" ? "who stopped or wavered" : f.outcome === "stayed" ? "who kept going" : f.outcome !== "all" ? `outcome: ${label(f.outcome).toLowerCase()}` : "",
    f.st && `from ${label(f.st).toLowerCase()}`, f.app && `about ${label(f.app)}`,
  ].filter(Boolean).join(" · ");

  return (
    <>
      <div className="page-head">
        <div>
          <div className="eyebrow">Investor story library</div>
          <h1>Story Explorer</h1>
          <p>Read what investors said first, then see how the AI tagged it and open the original post. Quotes are verbatim; usernames are removed.</p>
        </div>
        <label className="search-top">
          <span aria-hidden="true">⚲</span>
          <input value={q} onChange={(e) => { setQ(e.target.value); setShown(PAGE); }} placeholder={'Search quotes: "mandate", "pause"…'} aria-label="Search quotes" />
        </label>
      </div>
      <div className="ex-cols" id="ex-cols">
        <div className="panel filters">
          <div className="panel-head"><span><b>Filters</b><small>{active} active{active > 0 && <> · <button className="link" style={{ fontSize: 12 }} onClick={() => router.replace("/stories", { scroll: false })}>Clear</button></>}</small></span></div>
          <div className="body">
            <div className="fgroup">Investor</div>
            <span className="flabel">Outcome</span>
            <div className="seg" role="group" aria-label="Outcome">
              {[["all", "All"], ["dropoff", "Stopped"], ["stayed", "Stayed"]].map(([k, n]) => (
                <button key={k} className={f.outcome === k ? "on" : ""} aria-pressed={f.outcome === k} onClick={() => set({ outcome: k === "all" ? null : k })}>{n}</button>
              ))}
            </div>
            <span className="flabel">Investor experience</span>
            <Select k="grp" all="Any experience" opts={countBy("grp")} />
            <span className="flabel">Source</span>
            <Select k="src" all="All sources" opts={countBy("src")} />
            {(f.st || f.app || f.kind !== "story" || !["all", "dropoff", "stayed"].includes(f.outcome)) && <p className="meta" style={{ marginBottom: 16 }}>
              Also filtered: {[f.st && label(f.st), f.app && label(f.app), f.kind === "all" && "includes related posts", f.kind === "item" && "related posts only", !["all", "dropoff", "stayed"].includes(f.outcome) && label(f.outcome)].filter(Boolean).join(", ")} · <button className="link" style={{ fontSize: 12 }} onClick={() => set({ st: null, app: null, kind: null, outcome: ["all", "dropoff", "stayed"].includes(f.outcome) ? f.outcome === "all" ? null : f.outcome : null })}>remove</button>
            </p>}
            <div className="fgroup alt">Why they stopped / stayed</div>
            <span className="flabel">Root cause</span><Select k="rc" field="root_cause" all="All root causes" />
            <span className="flabel">Trigger</span><Select k="tr" field="stop_trigger" all="All triggers" />
            <span className="flabel">Unmet need</span><Select k="need" field="unmet_need" all="All unmet needs" />
            <span className="flabel">Stay reason</span><Select k="sr" field="stay_reason" all="All stay reasons" />
          </div>
        </div>
        <div className="panel">
          <div className="panel-head">
            <span><b>Investor stories</b><small>{data ? `${list.length.toLocaleString("en-IN")} matching · ${describe}` : "Loading…"}</small></span>
            <select className="select" style={{ margin: 0, width: "auto", height: 38 }} value={f.sort} onChange={(e) => set({ sort: e.target.value === "detail" ? null : e.target.value })} aria-label="Sort">
              <option value="detail">Most detailed</option>
              <option value="newest">Newest</option>
            </select>
          </div>
          <div className="list">
            {err && <div className="empty">Couldn&rsquo;t load the stories. Please refresh.</div>}
            {data && list.length === 0 && <div className="empty">No stories match these filters.</div>}
            {list.slice(0, shown).map((s) => <StoryCard key={s.id} s={s} />)}
            {list.length > shown && <div className="more"><button className="btn ghost" onClick={() => setShown(shown + PAGE)}>Show {Math.min(PAGE, list.length - shown)} more</button></div>}
          </div>
        </div>
      </div>
    </>
  );
}

export function StoryCard({ s }: { s: Story }) {
  const [ico, color] = SRC_ICON[s.src] ?? ["•", "#7c7e8c"];
  const rows = (["action", "root_cause", "stop_trigger", "unmet_need", "stay_reason", "emotion"] as const)
    .filter((k) => s.tags[k]?.length && !(k === "stay_reason" && s.cls !== "stayed"))
    .slice(0, 5);
  return (
    <div className="card story">
      <div>
        <div className="srcname">
          <span className="srcico" style={{ background: color }}>{ico || "A"}</span>{SOURCE_NAME(s)}
          {s.grp === "first_time" && <span className="chip g">First-time</span>}
          <span className={`chip ${s.cls === "stayed" ? "g" : s.cls === "dropoff" ? "r" : ""}`}>{s.cls === "stayed" ? "Kept going" : s.cls === "dropoff" ? "Stopped or wavering" : "Related post"}</span>
        </div>
        <p className="quote">{s.quote}</p>
        {s.excerpt && <p className="meta" style={{ marginTop: 6 }}>Opening of the post (no single evidence quote)</p>}
      </div>
      <div className="ctx">
        {rows.map((k) => <div key={k}><span>{FIELD_LABELS[k]}</span><b>{s.tags[k].map(label).join(", ")}</b></div>)}
        {s.tags.stage && <div><span>Stage</span><b>{label(s.tags.stage[0])}</b></div>}
      </div>
      {(s.why || (s.url && s.exact)) && <div className="why">
        <span>{s.why && <><b>AI&rsquo;s reason:</b> {s.why}</>}</span>
        {s.url && s.exact && <a className="link" href={s.url} target="_blank" rel="noopener noreferrer">View original ↗</a>}
      </div>}
    </div>
  );
}
