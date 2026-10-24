import { Suspense } from "react";
import StoryExplorer from "@/components/StoryExplorer";

export const metadata = { title: "Story Explorer · SIP Drop-off Lens" };

export default function Page() {
  return <Suspense fallback={null}><StoryExplorer /></Suspense>;
}
