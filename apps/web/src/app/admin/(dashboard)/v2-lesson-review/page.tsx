"use client";

import { useCallback, useEffect, useState } from "react";
import { ClipboardCheck, Clock3, RefreshCw } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";

interface ReviewItem {
  response_id: number; session_id: number; student_id: number; student_name: string;
  question_id: string; lesson_id: string; interaction: "read_aloud" | "write_text";
  prompt: string; reference: unknown; rubric: unknown;
  text_response: string | null; audio_url: string | null;
  evidence_ready: boolean; submitted_at: string | null; retry_state?: "requested" | "submitted" | null;
}
interface ReviewQueue { items: ReviewItem[]; next_offset: number | null }

function reference(value: unknown): string {
  if (value === null || value === undefined) return "لا يوجد نص مرجعي إضافي.";
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

export default function V2LessonReviewPage() {
  const [queue, setQueue] = useState<ReviewQueue>({ items: [], next_offset: null });
  const [offset, setOffset] = useState(0);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setError("");
    try {
      const response = await fetch(`/api/v2/review/lesson-queue?limit=20&offset=${offset}`, { cache: "no-store" });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر تحميل قائمة مراجعة الدروس");
      setQueue(data as ReviewQueue);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تعذر تحميل قائمة المراجعة");
    } finally {
      setLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const requestRetry = async (item: ReviewItem) => {
    const reason = (notes[item.response_id] || "").trim();
    if (reason.length < 10 || item.retry_state === "requested") return;
    setBusy(item.response_id); setError("");
    try {
      const response = await fetch(`/api/v2/retries/admin/lesson/${item.response_id}/request`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      });
      const result = await response.json().catch(() => null);
      if (!response.ok) throw new Error(result?.detail || "تعذر إنشاء طلب الإعادة");
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر طلب الإعادة"); }
    finally { setBusy(null); }
  };

  const decide = async (item: ReviewItem, isCorrect: boolean) => {
    const note = (notes[item.response_id] || "").trim();
    if (note.length < 2 || !item.evidence_ready) return;
    setBusy(item.response_id); setError("");
    try {
      const response = await fetch(`/api/v2/review/lessons/${item.response_id}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_correct: isCorrect, note }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر تسجيل قرار المراجعة");
      setNotes((previous) => { const updated = { ...previous }; delete updated[item.response_id]; return updated; });
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تعذر حفظ القرار");
    } finally {
      setBusy(null);
    }
  };

  return <AdminPage>
    <AdminPageHeader eyebrow="هِمّة V2 · P08" icon={ClipboardCheck}
      title="مراجعة قراءة وكتابة الدروس"
      description="افحص دليل الطالب ونص السؤال ومعيار التصحيح قبل أي قرار. لا يُحتسب التسجيل صحيحًا تلقائيًا."
      actions={<AdminAction icon={RefreshCw} onClick={() => void load()}>تحديث القائمة</AdminAction>} />
    {error && <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-4 text-red-800">{error}</div>}
    <AdminPanel title="أدلة معلّقة" description="قرارات المشرف موثّقة؛ لا يمكن إعادة اعتماد الإجابة نفسها.">
      {loading ? <div role="status" className="flex items-center gap-2 text-slate-600"><Clock3 size={18}/> جاري جلب الأدلة...</div>
        : queue.items.length === 0 ? <AdminEmptyState title="لا توجد إجابات معلّقة في هذه الصفحة" description="راجع صفحة أخرى أو حدّث القائمة." />
        : <div className="space-y-4">
          {queue.items.map((item) => {
            const note = notes[item.response_id] || "";
            const disabled = !item.evidence_ready || note.trim().length < 2 || busy !== null;
            return <article key={item.response_id} className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div><h3 className="font-bold text-slate-900">{item.student_name} · {item.lesson_id}</h3>
                  <p className="text-xs text-slate-600">{item.question_id} · {item.interaction === "read_aloud" ? "قراءة مسموعة" : "إجابة مكتوبة"}</p></div>
                <span className="text-xs text-slate-500">{item.submitted_at ? new Date(item.submitted_at).toLocaleString("ar") : ""}</span>
              </div>
              <p className="font-semibold text-slate-800">{item.prompt}</p>
              {item.interaction === "write_text"
                ? <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 whitespace-pre-wrap break-words"><strong>كتابة الطالب:</strong> {item.text_response || "لا توجد كتابة"}</div>
                : item.audio_url
                  ? <div className="space-y-2"><p className="font-semibold text-sm">تسجيل الطالب — استمع قبل الاعتماد</p><audio controls preload="none" src={item.audio_url} className="w-full" /></div>
                  : <p role="alert" className="text-amber-700">التسجيل غير متاح للمراجعة</p>}
              <details className="rounded-lg border border-blue-100 bg-blue-50/30 p-3">
                <summary className="cursor-pointer font-semibold text-sm">المرجع والمعيار الخاص بالمشرف</summary>
                <pre className="mt-2 whitespace-pre-wrap break-words text-xs text-slate-700 font-sans">{reference(item.reference)}{"\n"}{reference(item.rubric)}</pre>
              </details>
              <div className="space-y-2">
                <label htmlFor={`note-${item.response_id}`} className="block text-sm font-semibold">سبب قرار المراجعة (مطلوب)</label>
                <textarea id={`note-${item.response_id}`} value={note} maxLength={2000} rows={2}
                  onChange={(event) => setNotes((previous) => ({ ...previous, [item.response_id]: event.target.value }))}
                  className="w-full rounded-xl border border-slate-300 p-3 text-sm" placeholder="ما سبب قبول الدليل أو عدم استيفائه؟" />
                {!item.evidence_ready && <p className="text-sm text-amber-700">يجب توفر دليل صوتي/كتابي قبل إصدار القرار.</p>}
                <div className="flex flex-wrap gap-3">
                  <button type="button" disabled={disabled} onClick={() => void decide(item, true)}
                    className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-40">مستوفٍ</button>
                  <button type="button" disabled={disabled} onClick={() => void decide(item, false)}
                    className="rounded-lg bg-rose-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-40">غير مستوفٍ</button>
                  <button type="button" disabled={busy !== null || note.trim().length < 10 || item.retry_state === "requested"}
                    onClick={() => void requestRetry(item)} className="rounded-lg border border-amber-600 px-4 py-2 text-sm font-bold text-amber-900 disabled:opacity-40">
                    {item.interaction === "read_aloud" ? "اطلب إعادة القراءة" : "اطلب إعادة الكتابة"}</button>
                </div>
                {item.retry_state === "requested" && <p role="status" className="text-sm text-amber-700">بانتظار إرسال الطالب نسخة جديدة.</p>}
                {item.retry_state === "submitted" && <p role="status" className="text-sm text-blue-700">وصلت نسخة جديدة، راجعها قبل اعتماد القرار.</p>}
              </div>
            </article>;
          })}
        </div>}
      <nav className="mt-5 flex items-center gap-3" aria-label="صفحات مراجعة V2">
        <button type="button" disabled={offset === 0 || busy !== null} onClick={() => setOffset(Math.max(0, offset - 20))}
          className="rounded-lg border px-4 py-2 disabled:opacity-40">السابق</button>
        <span className="text-sm text-slate-600">الصفحة {Math.floor(offset / 20) + 1}</span>
        <button type="button" disabled={queue.next_offset === null || busy !== null} onClick={() => setOffset(queue.next_offset ?? offset)}
          className="rounded-lg border px-4 py-2 disabled:opacity-40">التالي</button>
      </nav>
    </AdminPanel>
  </AdminPage>;
}
