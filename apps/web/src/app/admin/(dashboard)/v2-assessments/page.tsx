"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BarChart3, ClipboardCheck, Clock3, RefreshCw } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel, AdminStat, AdminStatGrid } from "@/components/admin/AdminUI";
import V2BlockedReviewNotice, { type BlockedV2Review } from "@/components/admin/V2BlockedReviewNotice";
import SupervisorClaimActions from "@/components/admin/SupervisorClaimActions";
import V2EvidenceHistory from "@/components/admin/V2EvidenceHistory";
import V2ReviewedAudioPlayer from "@/components/admin/V2ReviewedAudioPlayer";

interface ReviewItem {
  response_id: number; session_id: number; student_id: number; student_name: string;
  question_id: string; kind: string; skill_group: string; evidence_type: string;
  interaction: string; prompt: string; stimulus_text: string | null;
  reference: unknown; rubric: unknown; text_response: string | null;
  audio_url: string | null; audio_submission_id: number | null; audio_playback_completed: boolean;
  evidence_ready: boolean; submitted_at: string; retry_state?: "requested" | "submitted" | null;
}
interface PlacementItem {
  session_id: number; student_id: number; student_name: string; attempt_no: number;
  result: { answered: number; total: number; pending_review: number; score_percent: number | null; skills: Record<string, { graded: number; correct: number; pending: number }> };
}
interface Paged<T> { items: T[]; blocked_items?: BlockedV2Review[]; next_offset: number | null }
interface Report { counts: Record<string, number>; averages: { pretest: number | null; posttest: number | null }; missing_policy: string }
function describeReference(value: unknown): string {
  if (value === null || value === undefined) return "لم تُحدد مرجعية إضافية لهذا السؤال.";
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

export default function V2AssessmentsPage() {
  const [reviews, setReviews] = useState<Paged<ReviewItem>>({ items: [], next_offset: null });
  const [placements, setPlacements] = useState<Paged<PlacementItem>>({ items: [], next_offset: null });
  const [reviewOffset, setReviewOffset] = useState(0);
  const [placementOffset, setPlacementOffset] = useState(0);
  const [report, setReport] = useState<Report | null>(null);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [levels, setLevels] = useState<Record<number, number>>({});
  const [reasons, setReasons] = useState<Record<number, string>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [completedAudio, setCompletedAudio] = useState<Record<number, boolean>>({});

  const loadId = useRef(0);
  const load = useCallback(async () => {
    const requestId = ++loadId.current;
    setError("");
    try {
      const [reviewResponse, placementResponse, summaryResponse] = await Promise.all([
        fetch(`/api/v2/assessments/admin/review-queue?limit=25&offset=${reviewOffset}`, { cache: "no-store" }),
        fetch(`/api/v2/assessments/admin/placement-queue?limit=25&offset=${placementOffset}`, { cache: "no-store" }),
        fetch("/api/v2/assessments/admin/reports/summary", { cache: "no-store" }),
      ]);
      const [queue, placement, summary] = await Promise.all([reviewResponse.json(), placementResponse.json(), summaryResponse.json()]);
      if (!reviewResponse.ok || !placementResponse.ok || !summaryResponse.ok) {
        throw new Error(queue?.detail || placement?.detail || summary?.detail || "تعذر تحميل تقييمات V2");
      }
      if (requestId !== loadId.current) return;
      setReviews(queue); setPlacements(placement); setReport(summary);
    } catch (reason) {
      if (requestId !== loadId.current) return;
      setReviews({ items: [], next_offset: null }); setPlacements({ items: [], next_offset: null }); setReport(null);
      setError(reason instanceof Error ? reason.message : "تعذر تحميل تقييمات V2");
    }
  }, [reviewOffset, placementOffset]);

  useEffect(() => { const timer = window.setTimeout(() => { void load(); }, 0); return () => { window.clearTimeout(timer); loadId.current += 1; }; }, [load]);

  const review = async (item: ReviewItem, isCorrect: boolean) => {
    const playbackReady = item.interaction !== "read_aloud" || (
      item.audio_submission_id !== null &&
      (completedAudio[item.audio_submission_id] ?? item.audio_playback_completed)
    );
    if (!item.evidence_ready || !playbackReady || (notes[item.response_id] || "").trim().length < 2) return;
    setBusy(`review:${item.response_id}`); setError("");
    try {
      const response = await fetch(`/api/v2/assessments/admin/responses/${item.response_id}/review`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_correct: isCorrect, note: notes[item.response_id].trim() }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر حفظ المراجعة");
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

  const place = async (item: PlacementItem) => {
    const level = levels[item.session_id];
    const reason = (reasons[item.session_id] || "").trim();
    if (![1, 2, 3].includes(level) || reason.length < 10) return;
    setBusy(`place:${item.session_id}`); setError("");
    try {
      const response = await fetch(`/api/v2/assessments/admin/sessions/${item.session_id}/placement`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ assigned_level: level, reason }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر اعتماد التسكين");
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر اعتماد التسكين"); }
    finally { setBusy(null); }
  };

  const pendingPlacement = report?.counts["pretest:placement_pending_review"] ?? 0;
  return <AdminPage>
    <AdminPageHeader eyebrow="P06 · سياسة مرشحة" icon={ClipboardCheck} title="تقييمات V2 والمراجعة"
      description="افحص دليل الطالب ومرجع السؤال قبل القرار؛ التسكين يدوي ومسبب إلى حين اعتماد الحدود التربوية."
      actions={<AdminAction icon={RefreshCw} onClick={() => void load()}>تحديث</AdminAction>} />
    {error && <div role="alert" className="alert-error">{error}</div>}
    <V2BlockedReviewNotice items={reviews.blocked_items} onRestored={load} />
    {report && <AdminStatGrid>
      <AdminStat icon={Clock3} value={reviews.items.length} label="الإجابات في الصفحة الحالية"/>
      <AdminStat icon={ClipboardCheck} value={pendingPlacement} label="جلسات تنتظر التسكين"/>
      <AdminStat icon={BarChart3} value={report.averages.pretest ?? "—"} label="متوسط القبلي الرسمي"/>
      <AdminStat icon={BarChart3} value={report.averages.posttest ?? "—"} label="متوسط البعدي الرسمي"/>
    </AdminStatGrid>}
    <AdminPanel title="مراجعة القراءة والكتابة" description="التسجيلات خاصة، ولا تظهر إلا للمشرف بعد تسجيل الدخول. قرار المراجعة يحتاج دليلًا وملاحظة.">
      {reviews.items.length === 0
        ? <AdminEmptyState title="لا توجد أدلة قابلة للمراجعة في هذه الصفحة" description="تظهر الإجابات المفتوحة التي تنتظر قرار المشرف."/>
        : <div className="space-y-4">{reviews.items.map((item) => {
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
          <label htmlFor={`note-${item.response_id}`} className="block text-sm font-semibold">سبب القرار في سجل التدقيق</label>
          <textarea id={`note-${item.response_id}`} rows={2} maxLength={2000}
            value={notes[item.response_id] || ""} onChange={event => setNotes(previous => ({ ...previous, [item.response_id]: event.target.value }))}
            placeholder="اذكر ما لاحظته في القراءة أو الكتابة" className="w-full rounded-xl border border-slate-300 p-3" />
          <div className="flex flex-wrap gap-2">
            <SupervisorClaimActions kind="assessment" responseId={item.response_id}/>
            <button type="button" disabled={!item.evidence_ready || !playbackReady || (notes[item.response_id] || "").trim().length < 2 || busy !== null}
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
    <AdminPanel title="تسكين الطلاب" description="جلسات قبلية مستوفية للمراجعات فقط؛ راجع درجات المهارات قبل اختيار المستوى وذكر سبب القرار.">
      {placements.items.length === 0 ? <AdminEmptyState title="لا توجد جلسات مؤهلة للتسكين" description="تظهر الجلسة بعد الإجابة على كل الأسئلة ومراجعة الأدلة المفتوحة."/>
        : <div className="space-y-4">{placements.items.map(item => <article key={item.session_id} className="space-y-3 rounded-2xl border border-slate-200 p-4">
          <div><strong className="text-navy">{item.student_name}</strong>
            <p className="text-sm text-muted">جلسة {item.session_id} · المحاولة {item.attempt_no} · {item.result.answered}/{item.result.total} سؤالًا · {item.result.score_percent ?? "—"}%</p></div>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
            {Object.entries(item.result.skills).map(([name, skill]) => <div key={name} className="rounded-lg bg-slate-50 p-2 text-sm">
              <strong>{name}</strong><p>{skill.correct} صحيح من {skill.graded} · {skill.pending} معلّق</p></div>)}
          </div>
          <label className="block text-sm font-semibold" htmlFor={`level-${item.session_id}`}>المستوى المختار</label>
          <select id={`level-${item.session_id}`} value={levels[item.session_id] ?? ""} onChange={event => setLevels(prev => ({ ...prev, [item.session_id]: Number(event.target.value) }))}
            className="w-full rounded-xl border border-slate-300 p-3">
            <option value="">اختر بعد المراجعة</option><option value="1">المستوى الأول</option><option value="2">المستوى الثاني</option><option value="3">المستوى الثالث</option>
          </select>
          <label className="block text-sm font-semibold" htmlFor={`reason-${item.session_id}`}>مبررات التسكين</label>
          <textarea id={`reason-${item.session_id}`} value={reasons[item.session_id] || ""} rows={2} maxLength={2000}
            onChange={event => setReasons(prev => ({ ...prev, [item.session_id]: event.target.value }))}
            placeholder="اكتب مبررًا مستندًا إلى نتائج المهارات" className="w-full rounded-xl border border-slate-300 p-3"/>
          <button type="button" disabled={busy !== null || ![1,2,3].includes(levels[item.session_id]) || (reasons[item.session_id] || "").trim().length < 10}
            onClick={() => void place(item)} className="rounded-xl bg-blue-700 px-4 py-2 font-bold text-white disabled:opacity-40">اعتماد التسكين</button>
        </article>)}</div>}
      <div className="mt-3 flex items-center justify-between gap-2">
        <button type="button" className="rounded-lg border px-3 py-2 disabled:opacity-40" disabled={placementOffset === 0} onClick={() => setPlacementOffset(Math.max(0, placementOffset - 25))}>السابق</button>
        <span className="text-sm text-muted">عدد جلسات الصفحة: {placements.items.length}</span>
        <button type="button" className="rounded-lg border px-3 py-2 disabled:opacity-40" disabled={placements.next_offset === null} onClick={() => setPlacementOffset(placements.next_offset || 0)}>التالي</button>
      </div>
    </AdminPanel>
    <p className="text-sm text-muted">P06 مرشحة: القيم المفقودة لا تُعامل كصفر، ولا يُستخدم تسكين آلي قبل اعتماد السياسة تربويًا.</p>
  </AdminPage>;
}
