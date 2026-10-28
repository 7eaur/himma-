"use client";

import { useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { CheckCheck, ClipboardCheck, Headphones } from "lucide-react";
import V2AssessmentsPage from "../v2-assessments/page";
import V2LessonReviewPage from "../v2-lesson-review/page";
import ReviewedRecordingsPage from "../v2-reviewed-recordings/page";

type ReviewTab = "assessments" | "lessons" | "reviewed";
const TABS: Array<{key: ReviewTab; label: string; icon: typeof Headphones}> = [
  {key: "assessments", label: "قراءات الاختبارات", icon: ClipboardCheck},
  {key: "lessons", label: "قراءات الدروس", icon: Headphones},
  {key: "reviewed", label: "تم تقييمها", icon: CheckCheck},
];
function safeTab(value: string | null): ReviewTab {
  return value === "assessments" || value === "lessons" || value === "reviewed"
    ? value : "assessments";
}

export default function V2ReviewCenterPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const urlTab = safeTab(searchParams.get("tab"));
  const [active, setActive] = useState<ReviewTab>(urlTab);
  const [lastUrlTab, setLastUrlTab] = useState(urlTab);
  // Keep the review tab aligned with Next navigation and browser Back/Forward.
  if (lastUrlTab !== urlTab) {
    setLastUrlTab(urlTab);
    setActive(urlTab);
  }
  const selectTab = (value: ReviewTab) => {
    setActive(value);
    const query = new URLSearchParams(searchParams.toString());
    query.set("tab", value);
    router.push(`${pathname}?${query.toString()}`, { scroll: false });
  };
  return <div dir="rtl" className="mx-auto w-full max-w-screen-xl min-w-0">
    <p className="mb-3 px-1 text-sm text-slate-600">استمع لقراءة الطالب، ثم اعتمدها أو اطلب إعادة التسجيل.</p>
    <nav role="tablist" aria-label="أقسام مراجعة التسجيلات"
      className="mb-4 flex gap-2 overflow-x-auto rounded-2xl border border-slate-200 bg-white p-2">
      {TABS.map((tab, index) => {
        const Icon = tab.icon;
        return <button key={tab.key} type="button" id={`review-center-tab-${tab.key}`}
          role="tab" aria-selected={active === tab.key} aria-controls="review-center-panel"
          tabIndex={active === tab.key ? 0 : -1}
          onClick={() => selectTab(tab.key)}
          onKeyDown={event => {
            const next = event.key === "ArrowLeft" ? (index + 1) % TABS.length
              : event.key === "ArrowRight" ? (index + TABS.length - 1) % TABS.length
                : event.key === "Home" ? 0 : event.key === "End" ? TABS.length - 1 : null;
            if (next !== null) {
              event.preventDefault();
              selectTab(TABS[next].key);
              document.getElementById(`review-center-tab-${TABS[next].key}`)?.focus();
            }
          }}
          className={`flex min-h-11 shrink-0 items-center gap-2 rounded-xl px-4 text-sm font-bold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 ${active === tab.key ? "bg-teal-50 text-teal-900" : "text-slate-600 hover:bg-slate-50"}`}>
          <Icon size={18} aria-hidden="true" />{tab.label}
        </button>;
      })}
    </nav>
    <div id="review-center-panel" role="tabpanel" aria-labelledby={`review-center-tab-${active}`} tabIndex={0}>
      {active === "assessments" ? <V2AssessmentsPage /> :
        active === "lessons" ? <V2LessonReviewPage /> : <ReviewedRecordingsPage />}
    </div>
  </div>;
}
