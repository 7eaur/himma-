"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BarChart3, ClipboardCheck, Clock3, RefreshCw } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel, AdminStat, AdminStatGrid } from "@/components/admin/AdminUI";
import V2BlockedReviewNotice, { type BlockedV2Review } from "@/components/admin/V2BlockedReviewNotice";
import SupervisorClaimActions from "@/components/admin/SupervisorClaimActions";
import V2EvidenceHistory from "@/components/admin/V2EvidenceHistory";
import V2ReviewedAudioPlayer from "@/components/admin/V2ReviewedAudioPlayer";
import V2ReviewQueuePicker from "@/components/admin/V2ReviewQueuePicker";
import V2ReadingRubricEditor, { emptyReadingRubric, rubricValid, type ReadingRubricDraft } from "@/components/admin/V2ReadingRubricEditor";

interface ReviewItem {
  response_id: number; session_id: number; student_id: number; student_name: string;
  question_id: string; kind: string; skill_group: string; evidence_type: string;
  interaction: string; prompt: string; stimulus_text: string | null;
  reference: unknown; rubric: unknown; text_response: string | null;
  audio_url: string | null; audio_submission_id: number | null; audio_playback_completed: boolean;
  evidence_ready: boolean; submitted_at: string; retry_state?: "requested" | "submitted" | null;
}
interface Paged<T> { items: T[]; blocked_items?: BlockedV2Review[]; next_offset: number | null }
interface Report { counts: Record<string, number>; averages: { pretest: number | null; posttest: number | null }; missing_policy: string }
function describeReference(value: unknown): string {
  if (value === null || value === undefined) return "لم تُحدد مرجعية إضافية لهذا السؤال.";
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

export default function V2AssessmentsPage() {
  const [reviews, setReviews] = useState<Paged<ReviewItem>>({ items: [], next_offset: null });
  const [reviewOffset, setReviewOffset] = useState(0);
  const [report, setReport] = useState<Report | null>(null);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [readingRubrics, setReadingRubrics] = useState<Record<number, ReadingRubricDraft>>({});
  const [selectedResponseId, setSelectedResponseId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [completedAudio, setCompletedAudio] = useState<Record<number, boolean>>({});

  const loadId = useRef(0);
  const load = useCallback(async () => {
    const requestId = ++loadId.current;
    setLoading(true); setError("");
    try {
      const [reviewResponse, summaryResponse] = await Promise.all([
        fetch(`/api/v2/assessments/admin/review-queue?limit=25&offset=${reviewOffset}`, { cache: "no-store" }),
        fetch("/api/v2/assessments/admin/reports/summary", { cache: "no-store" }),
      ]);
      const [queue, summary] = await Promise.all([reviewResponse.json().catch(() => null), summaryResponse.json().catch(() => null)]);
      if (!reviewResponse.ok || !summaryResponse.ok || !queue || !summary) {
        throw new Error(queue?.detail || summary?.detail || "تعذر تحميل تقييمات V2");
      }
      if (requestId !== loadId.current) return;
      setReviews(queue); setReport(summary);
    } catch (reason) {
      if (requestId !== loadId.current) return;
      setReviews({ items: [], next_offset: null }); setReport(null);
      setError(reason instanceof Error ? reason.message : "تعذر تحميل تقييمات V2");
    } finally { if (requestId === loadId.current) setLoading(false); }
  }, [reviewOffset]);

  useEffect(() => { const timer = window.setTimeout(() => { void load(); }, 0); return () => { window.clearTimeout(timer); loadId.current += 1; }; }, [load]);

  const review = async (item: ReviewItem, isCorrect: boolean) => {
    const playbackReady = item.interaction !== "read_aloud" || (
      item.audio_submission_id !== null &&
      (completedAudio[item.audio_submission_id] ?? item.audio_playback_completed)
    );
    if (!item.evidence_ready || !playbackReady || (notes[item.response_id] || "").trim().length < 2 ||
        (item.interaction === "read_aloud" && !rubricValid(readingRubrics[item.response_id] ?? emptyReadingRubric()))) return;
    setBusy(`review:${item.response_id}`); setError("");
    try {
      const response = await fetch(`/api/v2/assessments/admin/responses/${item.response_id}/review`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          is_correct: isCorrect, note: notes[item.response_id].trim(),
          ...(item.interaction === "read_aloud" ? { rubric: readingRubrics[item.response_id] } : {}),
        }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر حفظ المراجعة");
      setReadingRubrics(current => { const rest = {...current}; delete rest[item.response_id]; return rest; });
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر حفظ المراجعة"); }
    finally { setBusy(null); }
  };

  const requestRetry = async (item: ReviewItem) => {
    const reason = (notes[item.response_id] || "").trim();
    if (reason.length < 10 || item.retry_state === "requested") return;
    setBusy(`retry:${item.response_id}`); setError("");
    try {
      const response = await fetch(`/api/v2/retries/admin/assessment/${item.response_id}/request`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر طلب الإعادة");
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر طلب الإعادة"); }
    finally { setBusy(null); }
  };

  return <AdminPage>
    <AdminPageHeader eyebrow="المراجعة" icon={ClipboardCheck} title="الاختبارات ومراجعة القراءة"
      description="راجع التسجيلات الصوتية فقط؛ بعد اكتمالها يحدد النظام مستوى الطالب تلقائيًا وفق نتيجة القبلي."
      actions={<AdminAction icon={RefreshCw} onClick={() => void load()}>تحديث</AdminAction>} />
    {error && <div role="alert" className="alert-error">{error}</div>}
    {loading ? <p role="status">جاري تحميل المراجعات...</p> : <>
    <V2BlockedReviewNotice items={reviews.blocked_items} onRestored={load} />
    <V2ReviewQueuePicker items={reviews.items} selectedResponseId={selectedResponseId}
      onSelect={setSelectedResponseId} busy={busy !== null}
      label="مراجعة الاختبارات" />
    {report && <AdminStatGrid>
      <AdminStat icon={Clock3} value={reviews.items.length} label="الإجابات في الصفحة الحالية"/>
      <AdminStat icon={ClipboardCheck} value={report.counts["pretest:completed"] ?? 0} label="قبلي مكتمل وتسكين آلي"/>
      <AdminStat icon={BarChart3} value={report.averages.pretest ?? "—"} label="متوسط القبلي الرسمي"/>
      <AdminStat icon={BarChart3} value={report.averages.posttest ?? "—"} label="متوسط البعدي الرسمي"/>
    </AdminStatGrid>}
    <AdminPanel title="مراجعة القراءة الصوتية" description="التسجيلات خاصة، ويحدد النظام التسكين والتكيف تلقائيًا بعد اكتمال مراجعات الصوت.">
      {reviews.items.length === 0
        ? <AdminEmptyState title="لا توجد أدلة قابلة للمراجعة في هذه الصفحة" description="تظهر الإجابات المفتوحة التي تنتظر قرار المشرف."/>
        : <div className="space-y-4">{reviews.items.filter(item => item.response_id ===
          (reviews.items.some(row => row.response_id === selectedResponseId) ? selectedResponseId : reviews.items[0]?.response_id)).map((item) => {
          const playbackReady = item.interaction !== "read_aloud" || (
            item.audio_submission_id !== null &&
            (completedAudio[item.audio_submission_id] ?? item.audio_playback_completed)
          );
          return <article key={item.response_id} className="space-y-3 rounded-2xl border border-slate-200 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div><strong className="text-navy">{item.student_name} · {item.question_id}</strong>
              <p className="text-sm text-muted">{item.kind === "pretest" ? "اختبار قبلي" : "اختبار بعدي"} · {item.skill_group} · {item.evidence_type} · جلسة {item.session_id}</p></div>
            <span className="text-xs text-muted">{item.interaction === "read_aloud" ? "قراءة مسجلة" : "إجابة كتابية"}</span>
          </div>
          <div className="rounded-xl bg-slate-50 p-3">
            <p className="font-semibold text-navy">{item.prompt}</p>
            {item.stimulus_text && <p className="mt-1 whitespace-pre-wrap text-sm">{item.stimulus_text}</p>}
            <details className="mt-2 text-sm"><summary className="cursor-pointer font-medium">مرجع التقييم والضوابط للمشرف</summary>
              <pre className="mt-2 whitespace-pre-wrap break-words font-sans">{describeReference(item.reference)}{item.rubric ? `\n${describeReference(item.rubric)}` : ""}</pre>
            </details>
          </div>
          {item.interaction === "write_text" && <div><strong className="text-sm">ما كتبه الطالب</strong>
            <p dir="rtl" className="mt-1 whitespace-pre-wrap break-words rounded-xl border p-3">{item.text_response || "لا يوجد نص محفوظ"}</p></div>}
          {item.interaction === "read_aloud" && (item.audio_url && item.audio_submission_id
            ? <V2ReviewedAudioPlayer key={item.audio_submission_id} id={`audio-${item.response_id}`} src={item.audio_url}
                audioSubmissionId={item.audio_submission_id}
                completionUrl={`/api/v2/assessments/admin/responses/${item.response_id}/audio-completed`}
                initiallyCompleted={item.audio_playback_completed}
                onCompletionChange={(completed) => setCompletedAudio((previous) => ({ ...previous, [item.audio_submission_id!]: completed }))} />
            : <p role="alert" className="text-sm text-rose-700">ملف التسجيل غير متاح، لا يمكن اعتماد هذه الإجابة.</p>)}
          {item.interaction === "read_aloud" && item.evidence_ready && !playbackReady && <p className="text-sm text-amber-700">أكمل تشغيل التسجيل الحالي لتفعيل قرار المراجعة.</p>}
          <V2EvidenceHistory kind="assessment" responseId={item.response_id}/>
          {item.interaction === "read_aloud" && <V2ReadingRubricEditor
            value={readingRubrics[item.response_id] ?? emptyReadingRubric()}
            onChange={value => setReadingRubrics(previous => ({...previous, [item.response_id]: value}))}
            disabled={busy !== null} />}
          <label htmlFor={`note-${item.response_id}`} className="block text-sm font-semibold">سبب القرار في سجل التدقيق</label>
          <textarea id={`note-${item.response_id}`} rows={2} maxLength={2000}
            value={notes[item.response_id] || ""} onChange={event => setNotes(previous => ({ ...previous, [item.response_id]: event.target.value }))}
            placeholder="اذكر ما لاحظته في القراءة أو الكتابة" className="w-full rounded-xl border border-slate-300 p-3" />
          <div className="flex flex-wrap gap-2">
            <SupervisorClaimActions kind="assessment" responseId={item.response_id}/>
            <button type="button" disabled={!item.evidence_ready || !playbackReady || (notes[item.response_id] || "").trim().length < 2 || (item.interaction === "read_aloud" && !rubricValid(readingRubrics[item.response_id] ?? emptyReadingRubric())) || busy !== null}
              onClick={() => void review(item, true)} className="rounded-xl bg-emerald-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-40">مستوفٍ</button>
            <button type="button" disabled={!item.evidence_ready || !playbackReady || (notes[item.response_id] || "").trim().length < 2 || busy !== null}
              onClick={() => void review(item, false)} className="rounded-xl bg-rose-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-40">غير مستوفٍ</button>
            <button type="button" disabled={item.retry_state === "requested" || (notes[item.response_id] || "").trim().length < 10 || busy !== null}
              onClick={() => void requestRetry(item)} className="rounded-xl border border-amber-600 px-4 py-2 text-sm font-bold text-amber-900 disabled:opacity-40">{item.interaction === "read_aloud" ? "اطلب إعادة التسجيل" : "اطلب إعادة الكتابة"}</button>
          </div>
          {item.retry_state === "requested" && <p role="status" className="text-sm text-amber-700">تم إرسال طلب الإعادة للطالب؛ لا يمكن اعتماد التسجيل الأصلي.</p>}
          {item.retry_state === "submitted" && <p role="status" className="text-sm text-blue-700">وصل دليل جديد؛ راجعه قبل القرار.</p>}
        </article>;})}</div>}
      <div className="mt-3 flex items-center justify-between gap-2">
        <button type="button" className="rounded-lg border px-3 py-2 disabled:opacity-40" disabled={reviewOffset === 0} onClick={() => setReviewOffset(Math.max(0, reviewOffset - 25))}>السابق</button>
        <span className="text-sm text-muted">عدد سجلات الصفحة: {reviews.items.length + (reviews.blocked_items?.length ?? 0)}</span>
        <button type="button" className="rounded-lg border px-3 py-2 disabled:opacity-40" disabled={reviews.next_offset === null} onClick={() => setReviewOffset(reviews.next_offset || 0)}>التالي</button>
      </div>
    </AdminPanel>
    <p className="text-sm text-muted">بعد مراجعة تسجيلات القبلي، يحدد النظام المستوى المناسب تلقائيًا، ويفتح الدروس والبعدي وفق الشروط الأكاديمية.</p>

    </>}
  </AdminPage>;
}
