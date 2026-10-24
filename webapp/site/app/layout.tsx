import type { Metadata, Viewport } from "next";
import { Manrope } from "next/font/google";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

const manrope = Manrope({ subsets: ["latin"], weight: ["400", "500", "600", "700", "800"], variable: "--font-manrope" });

export const metadata: Metadata = {
  title: "SIP Drop-off Lens",
  description: "Why first-time SIP investors stop before month 12: 720 public investor stories, tagged by AI and checked by a human golden set.",
};
export const viewport: Viewport = { width: "device-width", initialScale: 1 };

// applies a saved theme before paint (storage can be blocked, so it is wrapped)
const THEME = `try{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={manrope.variable} suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: THEME }} /></head>
      <body>
        <div className="shell">
          <Sidebar />
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
