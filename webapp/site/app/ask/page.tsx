import { Suspense } from "react";
import AskView from "@/components/AskView";
import { F, QUESTION_ORDER } from "@/lib/data";

export const metadata = { title: "Ask the Data · SIP Drop-off Lens" };

export default function Page() {
  const briefs = QUESTION_ORDER.map((key) => ({ key, question: F.questions[key].question as string }));
  return <Suspense fallback={null}><AskView briefs={briefs} /></Suspense>;
}
