import findingsJson from "@/data/findings.json";
import cutsJson from "@/data/cuts.json";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const F: any = findingsJson;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const CUTS: any = cutsJson;

export type Story = {
  id: string; kind: "story" | "item"; cls: "dropoff" | "stayed" | "item"; outcome: string;
  src: string; app: string | null; sub: string | null; st: "app_review" | "community"; grp: string;
  date: string; quote: string; excerpt?: boolean; why: string; url: string | null; exact: boolean;
  tags: Record<string, string[]>; len: number;
};

export type Share = Record<string, { n: number; share: number }>;
export const top = (d: Share | undefined, k = 3, drop = ["other"]) =>
  Object.entries(d ?? {}).filter(([c]) => !drop.includes(c)).slice(0, k);

export const fmt = (n: number) => n.toLocaleString("en-IN");

// what investors described for each unmet need (plain words; not a solution)
export const NEED_DESC: Record<string, string> = {
  responsive_support: "Support that answers and owns the issue",
  portfolio_construction_help: "How many funds, which kinds, does my mix make sense",
  reliable_payment_recovery: "Debits that work, retries, reminders, no punitive charges",
  independent_reassurance: "A trusted, non-salesy answer when unsure",
  flexible_pause_modify: "Skip, pause, reduce or increase easily",
  basics_education: "How SIPs and mutual funds actually work",
  accurate_timely_portfolio: "Correct, up-to-date values",
  transparent_costs: "Clear fees, expense ratio, direct vs regular plans",
  consent_control: "No changes to their SIP or account without consent",
  understand_my_returns: "Whether their own returns are normal or on track",
  goal_linkage: "SIPs mapped to the goals they were for",
};

export const QUESTION_ORDER = [
  "q1_start_expect", "q2_change_over_time", "q3_stop_drivers", "q4_checking", "q5_in_app_confusion",
  "q6_outside_app", "q7_continue_vs_drop", "q8_segments", "q9_unmet_needs",
] as const;
