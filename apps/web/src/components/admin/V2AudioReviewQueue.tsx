"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ClipboardCheck, RefreshCw, X } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel } from "./AdminUI";
import V2BlockedReviewNotice, { type BlockedV2Review } from "./V2BlockedReviewNotice";
import V2ReviewedAudioPlayer from "./V2ReviewedAudioPlayer";
import V2ReadingRubricEditor, { emptyReadingRubric, rubricValid } from "./V2ReadingRubricEditor";
import styles from "./V2AudioReviewQueue.module.css";

type Kind = "assessment" | "lesson";
export interface AudioReviewItem {
  response_id: number; student_id: number; student_name: string; question_id: string;
  kind?: string; lesson_id?: string; interaction: string; prompt: string;
  stimulus_text?: string | null; reference?: unknown; rubric?: unknown;
  audio_url: string | null; audio_submission_id: number | null;
  audio_playback_completed: boolean; evidence_ready: boolean; submitted_at: string | null;
  retry_state?: "requested" | "submitted" | null;
}
interface Queue { items: AudioReviewItem[]; blocked_items?: BlockedV2Review[]; next_offset: number | null }
const referenceText = (value: unknown) => typeof value === "string" ? value : value == null ? "" : JSON.stringify(value, null, 2);
const activity = (item: AudioReviewItem) => item.lesson_id ?? (item.kind === "posttest" ? "الاختبار البعدي" : "الاختبار القبلي");

function ReviewDialog({ item, kind, onClose, onSaved }: {
  item: AudioReviewItem; kind: Kind; onClose: () => void; onSaved: (message: string) => Promise<void>;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [played, setPlayed] = useState(item.audio_playback_completed);
  const [note, setNote] = useState("");
  const [retry, setRetry] = useState(false);
  const [withRubric, setWithRubric] = useState(false);
  const [rubric, setRubric] = useState(emptyReadingRubric);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    const node = dialog.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    node?.showModal();
    return () => { node?.close(); document.body.style.overflow = previousOverflow; };
  }, []);
  const prefix = kind === "assessment" ? `/api/v2/assessments/admin/responses/${item.response_id}` : `/api/v2/review/lessons/${item.response_id}`;
  const available = item.interaction === "read_aloud" && item.evidence_ready && !!item.audio_url && !!item.audio_submission_id;
  const save = async (requestRetry: boolean) => {
    if (busy || (requestRetry ? note.trim().length < 10 : !available || !played || (withRubric && !rubricValid(rubric)))) return;
    setBusy(true); setError("");
    try {
      const response = await fetch(requestRetry
        ? `/api/v2/retries/admin/${kind}/${item.response_id}/request`
        : `${prefix}/${kind === "assessment" ? "review" : "decision"}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestRetry ? { reason: note.trim() } : {
          is_correct: true, note: note.trim(),
          ...(withRubric ? { rubric } : {}),
        }),
      });
      const result = await response.json().catch(() => null);
      if (!response.ok) throw new Error(typeof result?.detail === "string" ? result.detail : "تعذر حفظ المراجعة. حاول مرة أخرى.");
      await onSaved(requestRetry ? "أُرسل طلب إعادة التسجيل إلى الطالب." : "اعتُمدت القراءة الصحيحة وحُفظ القرار.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تعذر حفظ المراجعة.");
      setBusy(false);
    }
  };
  return <dialog ref={dialog} className={styles.dialog} aria-labelledby="audio-review-title" dir="rtl"
    onCancel={event => { event.preventDefault(); if (!busy) onClose(); }}
    onClick={event => { if (event.target === event.currentTarget && !busy) onClose(); }}>
    <div className={styles.dialogContent}>
      <header className={styles.dialogHeader}>
        <div><h2 id="audio-review-title">مراجعة تسجيل {item.student_name}</h2><p>{activity(item)} · {item.question_id}</p></div>
        <button type="button" autoFocus className={styles.close} aria-label="إغلاق المراجعة" disabled={busy} onClick={onClose}><X size={22} /></button>
      </header>
      <div className={styles.dialogBody}>
        <section className={styles.question}><h3>المطلوب من الطالب</h3><p>{item.prompt}</p>{item.stimulus_text && <p className={styles.stimulus}>{item.stimulus_text}</p>}</section>
        {available ? <V2ReviewedAudioPlayer id={`review-audio-${item.response_id}`} src={item.audio_url!}
          audioSubmissionId={item.audio_submission_id!} completionUrl={`${prefix}/audio-completed`}
          initiallyCompleted={item.audio_playback_completed} onCompletionChange={setPlayed} />
          : <p role="alert" className="alert-error">التسجيل الصوتي غير متاح. لا يمكن اعتماد القراءة؛ اطلب إعادة تسجيل واضحة.</p>}
        {error && <p role="alert" className="alert-error">{error}</p>}
        {retry ? <div className={styles.fields}>
          <label htmlFor="audio-review-note">ماذا يحتاج الطالب أن يعيد؟</label>
          <textarea id="audio-review-note" value={note} onChange={event => setNote(event.target.value)} rows={3} maxLength={2000}
            placeholder="مثال: أعد قراءة الكلمة بصوت واضح ومن دون ضوضاء." disabled={busy} />
          <p>اكتب توجيهًا واضحًا من 10 أحرف على الأقل ليصل إلى الطالب.</p>
        </div> : <>
          <label className={styles.optional}><input type="checkbox" checked={withRubric} onChange={event => setWithRubric(event.target.checked)} disabled={busy} />إضافة تقدير رقمي وملاحظات تفصيلية (اختياري)</label>
          {withRubric && <V2ReadingRubricEditor value={rubric} onChange={setRubric} disabled={busy} />}
          <details><summary>ملاحظة على القرار أو مرجع التقييم</summary>
            <div className={styles.fields}><label htmlFor="audio-review-note">ملاحظة اختيارية</label>
              <textarea id="audio-review-note" value={note} onChange={event => setNote(event.target.value)} rows={2} maxLength={2000} disabled={busy} />
              <pre>{[referenceText(item.reference), referenceText(item.rubric)].filter(Boolean).join("\n") || "استمع إلى القراءة وقارنها بالنص المطلوب."}</pre>
            </div>
          </details>
        </>}
      </div>
      <footer className={styles.dialogFooter}>
        {retry ? <>
          <button type="button" className="btn-primary" disabled={busy || note.trim().length < 10} onClick={() => void save(true)}>{busy ? "جارٍ الإرسال..." : "إرسال طلب الإعادة"}</button>
          <button type="button" className="btn-secondary" disabled={busy} onClick={() => { setRetry(false); setError(""); }}>العودة للاستماع</button>
        </> : <>
          <button type="button" className="btn-primary" disabled={busy || !available || !played || (withRubric && !rubricValid(rubric))} onClick={() => void save(false)}>{busy ? "جارٍ الحفظ..." : "القراءة صحيحة"}</button>
          <button type="button" className="btn-secondary" disabled={busy || item.retry_state === "requested"} onClick={() => { setRetry(true); setError(""); }}>طلب إعادة التسجيل</button>
          {!played && available && <p>استمع للتسجيل كاملًا لتفعيل اعتماد القراءة.</p>}
        </>}
      </footer>
    </div>
  </dialog>;
}

export default function V2AudioReviewQueue({ kind }: { kind: Kind }) {
  const pageSize = kind === "assessment" ? 25 : 20;
  const [queue, setQueue] = useState<Queue>({ items: [], next_offset: null });
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const requestId = useRef(0);
  const load = useCallback(async () => {
    const id = ++requestId.current;
    setLoading(true); setError(""); setSelected(null);
    try {
      const endpoint = kind === "assessment" ? "/api/v2/assessments/admin/review-queue" : "/api/v2/review/lesson-queue";
      const response = await fetch(`${endpoint}?limit=${pageSize}&offset=${offset}`, { cache: "no-store" });
      const data = await response.json().catch(() => null);
      if (!response.ok || !Array.isArray(data?.items)) throw new Error(typeof data?.detail === "string" ? data.detail : "تعذر تحميل قائمة التسجيلات.");
      if (id === requestId.current) setQueue(data);
    } catch (reason) {
      if (id !== requestId.current) return;
      setQueue({ items: [], next_offset: null });
      setError(reason instanceof Error ? reason.message : "تعذر تحميل قائمة التسجيلات.");
    } finally { if (id === requestId.current) setLoading(false); }
  }, [kind, offset, pageSize]);
  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => { window.clearTimeout(timer); requestId.current += 1; };
  }, [load]);
  const audioItems = queue.items.filter(item => item.interaction === "read_aloud");
  const items = audioItems.filter(item => `${item.student_name} ${item.question_id} ${activity(item)}`.includes(search.trim()));
  const current = queue.items.find(item => item.response_id === selected);
  return <AdminPage>
    <AdminPageHeader eyebrow="مراجعة التسجيلات" icon={ClipboardCheck}
      title={kind === "assessment" ? "الاختبارات ومراجعة القراءة" : "مراجعة قراءات الدروس"}
      description="اختر تسجيلًا من القائمة، واستمع إليه، ثم اعتمد القراءة أو اطلب إعادة التسجيل."
      actions={<AdminAction icon={RefreshCw} onClick={() => { setMessage(""); void load(); }}>تحديث القائمة</AdminAction>} />
    {error && <p role="alert" className="alert-error">{error}</p>}
    {message && <p role="status" className={styles.success}>{message}</p>}
    {!loading && <V2BlockedReviewNotice items={queue.blocked_items} onRestored={load} />}
    <AdminPanel title="تسجيلات تحتاج مراجعة">
      <div className={styles.toolbar}><label htmlFor={`review-search-${kind}`}>بحث في هذه الصفحة</label>
        <input id={`review-search-${kind}`} className="input-field" value={search} onChange={event => setSearch(event.target.value)} placeholder="اسم الطالب أو النشاط" />
        <span>{loading ? "جارٍ التحميل" : `${audioItems.length} تسجيل في الصفحة`}</span></div>
      {!loading && audioItems.length !== queue.items.length && <p role="alert" className="alert-error">توجد إجابات محفوظة تحتاج فحص توافق المحتوى؛ لا تُعامل كتسجيلات صوتية ولا تُعاد كتابتها.</p>}
      {loading ? <p role="status">جاري تحميل التسجيلات...</p> : !audioItems.length
        ? <AdminEmptyState title="لا توجد تسجيلات تحتاج مراجعة في هذه الصفحة" description="تظهر هنا تسجيلات القراءة التي تنتظر قرارك." />
        : !items.length ? <AdminEmptyState title="لا توجد نتائج لهذا البحث" description="غيّر البحث أو انتقل إلى صفحة أخرى." />
        : <div className={styles.tableScroll}><table className="data-table" aria-label="تسجيلات تحتاج مراجعة"><thead><tr>
          <th>الطالب</th><th>النشاط</th><th>المطلوب</th><th>تاريخ التسجيل</th><th>الحالة</th><th>الإجراء</th>
        </tr></thead><tbody>{items.map(item => <tr key={item.response_id}>
          <td><Link href={`/admin/students/${item.student_id}?tab=recordings`}>{item.student_name}</Link></td>
          <td>{activity(item)}</td><td className={styles.prompt}>{item.prompt}</td>
          <td>{item.submitted_at ? new Date(item.submitted_at).toLocaleDateString("ar") : "—"}</td>
          <td>{item.retry_state === "requested" ? "بانتظار إعادة الطالب" : item.retry_state === "submitted" ? "وصلت إعادة التسجيل" : "بانتظار المراجعة"}</td>
          <td><button type="button" className="btn-secondary" aria-label={`مراجعة تسجيل ${item.student_name} ${item.question_id}`}
            disabled={item.retry_state === "requested"} onClick={() => setSelected(item.response_id)}>مراجعة</button></td>
        </tr>)}</tbody></table></div>}
      <nav className={styles.pagination} aria-label="صفحات التسجيلات">
        <button type="button" className="btn-secondary" disabled={loading || offset === 0} onClick={() => setOffset(Math.max(0, offset - pageSize))}>السابق</button>
        <span>الصفحة {Math.floor(offset / pageSize) + 1}</span>
        <button type="button" className="btn-secondary" disabled={loading || queue.next_offset === null} onClick={() => setOffset(queue.next_offset ?? offset)}>التالي</button>
      </nav>
    </AdminPanel>
    {current && <ReviewDialog key={`${kind}:${current.response_id}`} item={current} kind={kind} onClose={() => setSelected(null)}
      onSaved={async text => { setMessage(text); await load(); }} />}
  </AdminPage>;
}
