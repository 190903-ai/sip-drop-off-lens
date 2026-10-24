"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const ICONS: Record<string, React.ReactNode> = {
  findings: <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />,
  stories: <><rect x="3" y="4" width="18" height="16" rx="3" /><path d="M7 9h10M7 13h7" /></>,
  ask: <><circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" /></>,
  how: <><circle cx="5" cy="6" r="2" /><circle cx="19" cy="6" r="2" /><circle cx="12" cy="18" r="2" /><path d="M7 6h10M6 8l5 8M18 8l-5 8" /></>,
  limits: <><circle cx="12" cy="12" r="9" /><path d="M12 7v6M12 16.5v.5" /></>,
};

const WORKSPACE = [
  { href: "/", key: "findings", title: "Findings", sub: "Overview" },
  { href: "/stories", key: "stories", title: "Story Explorer", sub: "720 investor stories" },
  { href: "/ask", key: "ask", title: "Ask the Data", sub: "Questions with citations" },
];
const METHOD = [
  { href: "/how-it-works", key: "how", title: "How it works", sub: "Pipeline and sources" },
  { href: "/limitations", key: "limits", title: "Limitations", sub: "What this can't tell you" },
];

function Item({ href, k, title, sub, on }: { href: string; k: string; title: string; sub: string; on: boolean }) {
  return (
    <Link href={href} className={`side-item${on ? " on" : ""}`} aria-current={on ? "page" : undefined} title={title}>
      <svg viewBox="0 0 24 24" aria-hidden="true">{ICONS[k]}</svg>
      <span><b>{title}</b><small>{sub}</small></span>
    </Link>
  );
}

export default function Sidebar() {
  const path = usePathname();
  const [dark, setDark] = useState<boolean | null>(null);

  useEffect(() => {
    const set = document.documentElement.dataset.theme;
    setDark(set ? set === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches);
  }, []);

  const flip = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.dataset.theme = next ? "dark" : "light";
    try { localStorage.setItem("theme", next ? "dark" : "light"); } catch {}
  };

  const isOn = (href: string) => (href === "/" ? path === "/" : path.startsWith(href));
  return (
    <nav className="side-nav" aria-label="Main">
      <Link href="/" className="side-brand">
        <span className="side-logo"><span className="mark" /></span>
        <span><b>SIP DROP-OFF LENS</b><small>Groww · SIP study</small></span>
      </Link>
      <div className="side-label">Workspace</div>
      {WORKSPACE.map((i) => <Item key={i.key} href={i.href} k={i.key} title={i.title} sub={i.sub} on={isOn(i.href)} />)}
      <div className="side-label second">Method</div>
      {METHOD.map((i) => <Item key={i.key} href={i.href} k={i.key} title={i.title} sub={i.sub} on={isOn(i.href)} />)}
      <div className="side-foot">
        <a className="side-log" href="https://docs.google.com/document/d/19trpl81SXwOHlTXyf4WZIBEujWOd3c5B/edit?usp=sharing" target="_blank" rel="noopener noreferrer">AI Evidence Log ↗</a>
        <button className="toggle" onClick={flip} aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}>
          {dark ? "☾" : "☼"}
        </button>
      </div>
    </nav>
  );
}
