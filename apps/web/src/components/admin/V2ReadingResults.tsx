"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Headphones, RefreshCw, Search, ShieldCheck } from "lucide-react";
import {
  AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel, AdminRequestStatus,
} from "@/components/admin/AdminUI";
import { adminErrorMessage, safeAdminCaughtError } from "@/lib/adminFeedback";

type ReadingFilter = "all" | "completed" | "needs_attention" | "processing";
type ReadingItem = {
  job_id: number;
  student_id: number;
  student_name: string;
  question_id: string;
  reference: string;
  kind: "letter" | "word" | "sentence" | "text";
  session_kind: "assessment" | "lesson";
  result: string;
  score_percent: number | null;
  created_at: string | null;
  has_audio: boolean;
};
type ReadingPage = { items: ReadingItem[]; total: number; next_offset: number | null };

const FILTERS: Array<{ id: ReadingFilter; label: string }> = [
  { id: "all", label: "جميع النتائج" },
  { id: "completed", label: "اكتمل التقييم" },
  { id: "needs_attention", label: "تحتاج متابعة" },
  { id: "processing", label: "جاري التحقق" },
];
const KIND_LABELS: Record<ReadingItem["kind"], string> = {
  letter: "حرف", word: "كلمة", sentence: "جملة", text: "نص",
};
const PAGE_SIZE = 20;
const INITIAL: ReadingPage = { items: [], total: 0, next_offset: null };

function isPage(value: unknown): value is ReadingPage {
  if (!value || typeof value !== "object") return false;
  const data = value as Partial<ReadingPage>;
  return Array.isArray(data.items)
    && Number.isSafeInteger(data.total) && (data.total ?? -1) >= 0
    && (data.next_offset === null ||
      (Number.isSafeInteger(data.next_offset) && (data.next_offset ?? -1) >= 0));
}

export default function V2ReadingResults() {
  const [filter, setFilter] = useState<ReadingFilter>("all");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<ReadingPage>(INITIAL);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const requestId = useRef(0);

  const refresh = useCallback(() => setRefreshKey(key => key + 1), []);
  const changeFilter = (next: ReadingFilter) => {
    setFilter(next);
    setOffset(0);
    setPage(INITIAL);
  };

  useEffect(() => {
    const controller = new AbortController();
    const token = ++requestId.current;
    setLoading(true);
    setError("");
    setPage(INITIAL); // Never leave a previous student's recording after filter changes.
    const timer = window.setTimeout(async () => {
      const query = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
      if (filter !== "all") query.set("state", filter);
      if (search.trim()) query.set("search", search.trim());
      try {
        const response = await fetch(`/api/v2/reading/admin/results?${query.toString()}`, {
          cache: "no-store", signal: controller.signal,
        });
        const body: unknown = await response.json().catch(() => null);
        if (token !== requestId.current) return;
        if (!response.ok) {
          const detail = body && typeof body === "object" && "detail" in body
            ? (body as { detail?: unknown }).detail : undefined;
          throw new Error(adminErrorMessage(response.status, detail,
            "تعذر تحميل نتائج القراءة. أعد المحاولة."));
        }
        if (!isPage(body)) throw new Error("تعذر قراءة نتائج التسجيلات. أعد المحاولة.");
        setPage(body);
      } catch (cause) {
        if (token !== requestId.current || controller.signal.aborted) return;
        setError(safeAdminCaughtError(cause, "تعذر الاتصال بالخدمة. حاول مرة أخرى."));
        setPage(INITIAL);
      } finally {
        if (token === requestId.current && !controller.signal.aborted) setLoading(false);
      }
    }, search.trim() ? 250 : 0);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
      requestId.current += 1;
    };
  }, [filter, search, offset, refreshKey]);

  return <AdminPage>
    <AdminPageHeader eyebrow="نتائج القراءة" title="متابعة القراءة الصوتية"
      description="تابع تقدم الطلاب واستمع إلى تسجيلاتهم، دون اعتماد يدوي لكل إجابة."
      icon={Headphones}
      actions={<button type="button" onClick={refresh}
        className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-teal-700 bg-white px-4 font-semibold text-teal-800 hover:bg-teal-50 focus-visible:outline-2 focus-visible:outline-teal-700">
        <RefreshCw size={18} aria-hidden="true" /> تحديث النتائج
      </button>} />
    <AdminPanel title="البحث والتصفية" description="يمكنك متابعة جميع القراءات أو عرض الحالات التي تحتاج اهتمامًا.">
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
        <label className="relative flex flex-col gap-1 text-sm font-semibold text-slate-800">
          اسم الطالب أو رقم السؤال
          <span className="relative">
            <Search size={17} aria-hidden="true" className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input type="search" value={search} maxLength={80}
              onChange={event => { setSearch(event.target.value); setOffset(0); }}
              placeholder="ابحث باسم الطالب أو رقم السؤال"
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white py-2 pl-3 pr-10 outline-offset-2 focus-visible:outline-teal-700" />
          </span>
        </label>
        <div className="flex flex-wrap gap-2" role="group" aria-label="حالة القراءة">
          {FILTERS.map(item => <button type="button" key={item.id}
            aria-pressed={filter === item.id} onClick={() => changeFilter(item.id)}
            className={`min-h-11 rounded-xl border px-3 text-sm font-bold focus-visible:outline-2 focus-visible:outline-teal-700 ${filter === item.id
              ? "border-teal-700 bg-teal-50 text-teal-900"
              : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"}`}>{item.label}</button>)}
        </div>
      </div>
    </AdminPanel>
    <AdminPanel title="التسجيلات والنتائج" description="النتائج التعليمية وأحدث تسجيل مرتبط بكل إجابة.">
      <AdminRequestStatus loading={loading} error={error} onRetry={refresh}
        loadingText="جارٍ تحميل نتائج القراءة..." />
      {!loading && !error && page.items.length === 0 &&
        <AdminEmptyState title="لا توجد نتائج لهذه التصفية"
          description="ستظهر القراءات عند وصول تسجيلات الطلاب وتحليلها." />}
      {!loading && !error && page.items.length > 0 && <div className="space-y-3">
        <p role="status" className="text-sm text-slate-600">إجمالي النتائج: {page.total}</p>
        {page.items.map(item => <article key={item.job_id}
          className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h3 className="font-bold text-slate-900">{item.student_name}</h3>
              <p className="mt-1 text-sm text-slate-600">
                {item.session_kind === "assessment" ? "اختبار" : "درس"} · {KIND_LABELS[item.kind]}
                {item.created_at ? ` · ${new Date(item.created_at).toLocaleDateString("ar")}` : ""}
              </p>
              <p className="mt-2 break-words rounded-xl bg-slate-50 p-3 text-lg font-semibold leading-relaxed text-slate-900" dir="rtl">
                {item.reference}
              </p>
            </div>
            <div className="min-w-[120px] rounded-xl bg-teal-50 px-3 py-2 text-center text-sm font-bold text-teal-900">
              {item.result}
              {item.score_percent != null && <span className="mt-1 block text-xs">{item.score_percent}% من الكلمات</span>}
            </div>
          </div>
          {item.has_audio && <details className="mt-3 rounded-xl border border-slate-200 p-3">
            <summary className="cursor-pointer text-sm font-semibold text-slate-800">
              الاستماع إلى تسجيل الطالب
            </summary>
            <audio controls preload="none" className="mt-3 w-full"
              src={`/api/v2/reading/admin/jobs/${item.job_id}/audio`}
              aria-label={`تسجيل قراءة ${item.student_name}`} />
          </details>}
        </article>)}
      </div>}
      {!loading && !error && (offset > 0 || page.next_offset !== null) &&
        <nav aria-label="صفحات نتائج القراءة" className="mt-4 flex items-center justify-between gap-3">
          <button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            className="min-h-11 rounded-xl border border-slate-300 px-4 disabled:opacity-40">السابق</button>
          <span className="text-sm text-slate-600">صفحة {Math.floor(offset / PAGE_SIZE) + 1}</span>
          <button type="button" disabled={page.next_offset === null}
            onClick={() => setOffset(page.next_offset ?? offset)}
            className="min-h-11 rounded-xl border border-slate-300 px-4 disabled:opacity-40">التالي</button>
        </nav>}
    </AdminPanel>
    <p className="mt-3 flex items-center gap-2 text-sm text-slate-500">
      <ShieldCheck size={17} aria-hidden="true" /> التسجيلات خاصة؛ الاستماع متاح للمشرف المصرح فقط.
    </p>
  </AdminPage>;
}
