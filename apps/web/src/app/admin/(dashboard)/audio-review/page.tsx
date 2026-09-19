"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  Headphones,
  ListMusic,
  Play,
  RefreshCw,
  RotateCcw,
  Save,
  UserRound,
} from "lucide-react";
import AdminFeedbackToast from "@/components/admin/AdminFeedbackToast";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel, AdminToolbar } from "@/components/admin/AdminUI";

interface AudioSubmission {
  id: number;
  storage_key: string;
  status: string;
  submitted_at: string;
  student_id?: number | null;
  student_name?: string | null;
  session_type?: string | null;
  item_title?: string | null;
  expected_reading_text?: string | null;
}

function AudioPlayer({ storageKey }: { storageKey: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadRecording = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`/api/recordings/stream-by-key?key=${encodeURIComponent(storageKey)}`);
      const data = await response.json().catch(() => null);
      if (!response.ok || !data?.url) throw new Error(data?.detail || "تعذر تحميل التسجيل");
      setSrc(data.url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "تعذر تحميل التسجيل");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="audio-review-source-card" aria-label="التسجيل الصوتي">
      <div className="audio-review-card-heading">
        <span className="audio-review-card-icon"><Headphones size={19} aria-hidden="true" /></span>
        <div>
          <strong>التسجيل الصوتي</strong>
          <span>استمع إلى التسجيل كاملًا قبل التقييم.</span>
        </div>
      </div>

      {src ? (
        <audio src={src} controls className="audio-review-native-player" preload="metadata" />
      ) : (
        <button type="button" className="audio-review-listen-button" onClick={() => void loadRecording()} disabled={loading}>
          <Play size={18} aria-hidden="true" />
          {loading ? "جاري تجهيز التسجيل..." : "تشغيل التسجيل"}
        </button>
      )}

      {error && <p className="alert-error text-sm" role="alert">{error}</p>}
    </section>
  );
}

function sessionLabel(value?: string | null) {
  if (value === "pretest") return "الاختبار القبلي";
  if (value === "posttest") return "الاختبار البعدي";
  if (value === "core") return "نشاط تعليمي";
  return "قراءة مسجلة";
}

function queueUrl(studentId: number | null) {
  return studentId ? `/api/review/pending-audio?student_id=${studentId}` : "/api/review/pending-audio";
}

function positiveQueryNumber(name: string): number | null {
  if (typeof window === "undefined") return null;
  const raw = new URLSearchParams(window.location.search).get(name);
  if (!raw || !/^\d+$/.test(raw)) return null;
  const parsed = Number(raw);
  return parsed > 0 ? parsed : null;
}

function studentFilterFromLocation(): number | null {
  return positiveQueryNumber("student_id");
}

function submissionFilterFromLocation(): number | null {
  return positiveQueryNumber("submission_id");
}

function submissionDate(value: string) {
  return new Date(value).toLocaleString("ar-SA", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}

function NumberField({
  id,
  label,
  value,
  min,
  onChange,
}: {
  id: string;
  label: string;
  value: number;
  min: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="audio-review-score-field" htmlFor={id}>
      <span className="audio-review-score-label">{label}</span>
      <input
        id={id}
        className="audio-review-score-input"
        type="number"
        inputMode="numeric"
        min={min}
        step={1}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

export default function AudioReviewPage() {
  const [submissions, setSubmissions] = useState<AudioSubmission[]>([]);
  const [studentFilter] = useState<number | null>(studentFilterFromLocation);
  const [submissionFilter] = useState<number | null>(submissionFilterFromLocation);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string }>({ kind: "success", text: "" });
  const [gradingId, setGradingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const editingRef = useRef<number | null>(null);
  const appliedSubmissionFilterRef = useRef(false);
  const [isValid, setIsValid] = useState(true);
  const [targetUnits, setTargetUnits] = useState(10);
  const [deletions, setDeletions] = useState(0);
  const [substitutions, setSubstitutions] = useState(0);
  const [insertions, setInsertions] = useState(0);
  const [pronunciationNotes, setPronunciationNotes] = useState("");
  const [fluencyNotes, setFluencyNotes] = useState("");
  const [notesOpen, setNotesOpen] = useState(false);

  const activeSubmission = useMemo(
    () => submissions.find((submission) => submission.id === editingId) ?? null,
    [editingId, submissions],
  );

  useEffect(() => { editingRef.current = editingId; }, [editingId]);

  useEffect(() => {
    let cancelled = false;
    const fetchQueue = () => {
      if (editingRef.current !== null) return;
      void fetch(queueUrl(studentFilter), { cache: "no-store" }).then(async (response) => {
        if (!response.ok) throw new Error("تعذر تحميل التسجيلات المنتظرة");
        const data: AudioSubmission[] = await response.json();
        if (!cancelled && editingRef.current === null) {
          setSubmissions(data);
          if (submissionFilter && !appliedSubmissionFilterRef.current && data.some((submission) => submission.id === submissionFilter)) {
            appliedSubmissionFilterRef.current = true;
            editingRef.current = submissionFilter;
            setEditingId(submissionFilter);
          }
        }
      }).catch((caught: unknown) => {
        if (!cancelled) setMessage({ kind: "error", text: caught instanceof Error ? caught.message : "تعذر تحميل التسجيلات" });
      }).finally(() => { if (!cancelled) setLoading(false); });
    };
    fetchQueue();
    const interval = window.setInterval(fetchQueue, 30000);
    return () => { cancelled = true; window.clearInterval(interval); };
  }, [studentFilter, submissionFilter]);

  const refreshQueue = async () => {
    if (editingId !== null) {
      setMessage({ kind: "error", text: "أكمل المراجعة الحالية أو ألغها قبل تحديث القائمة." });
      return;
    }
    setRefreshing(true);
    setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(queueUrl(studentFilter), { cache: "no-store" });
      if (!response.ok) throw new Error("تعذر تحديث قائمة التسجيلات");
      setSubmissions(await response.json());
    } catch (caught) {
      setMessage({ kind: "error", text: caught instanceof Error ? caught.message : "تعذر تحديث القائمة" });
    } finally {
      setRefreshing(false);
    }
  };

  const openReview = (id: number) => {
    if (editingId !== null && editingId !== id) {
      setMessage({ kind: "error", text: "احفظ المراجعة الحالية أو ألغها قبل الانتقال إلى تسجيل آخر." });
      return;
    }
    editingRef.current = id;
    setEditingId(id);
    setIsValid(true);
    setTargetUnits(10);
    setDeletions(0);
    setSubstitutions(0);
    setInsertions(0);
    setPronunciationNotes("");
    setFluencyNotes("");
    setNotesOpen(false);
    setMessage({ kind: "success", text: "" });
  };

  const closeReview = () => {
    editingRef.current = null;
    setEditingId(null);
    setMessage({ kind: "success", text: "" });
  };

  const validateReview = () => {
    if (!isValid) return "";
    if (!Number.isInteger(targetUnits) || targetUnits < 1) return "عدد الوحدات المستهدفة يجب أن يكون رقمًا صحيحًا أكبر من صفر.";
    if ([deletions, substitutions, insertions].some((value) => !Number.isInteger(value) || value < 0)) return "قيم الحذف والاستبدال والإضافة يجب أن تكون أرقامًا صحيحة غير سالبة.";
    return "";
  };

  const handleGrade = async (id: number) => {
    const validation = validateReview();
    if (validation) {
      setMessage({ kind: "error", text: validation });
      return;
    }
    setGradingId(id);
    setMessage({ kind: "success", text: "" });
    try {
      const payload = {
        is_valid: isValid,
        target_units: isValid ? targetUnits : undefined,
        deletions: isValid ? deletions : 0,
        substitutions: isValid ? substitutions : 0,
        insertions: isValid ? insertions : 0,
        pronunciation_notes: pronunciationNotes || undefined,
        fluency_notes: fluencyNotes || undefined,
      };
      const response = await fetch(`/api/review/audio/${id}/grade`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر حفظ التقييم");
      setSubmissions((current) => current.filter((submission) => submission.id !== id));
      editingRef.current = null;
      setEditingId(null);
      setMessage({
        kind: "success",
        text: isValid
          ? "تم اعتماد التسجيل وحفظ نتيجة المراجعة بنجاح."
          : "تم إرسال مهمة إعادة تسجيل للطالب دون إيقاف مساره، مع الاحتفاظ بالتسجيل السابق في السجل.",
      });
    } catch (caught) {
      setMessage({ kind: "error", text: caught instanceof Error ? caught.message : "تعذر حفظ التقييم" });
    } finally {
      setGradingId(null);
    }
  };

  return (
    <AdminPage>
      <AdminPageHeader
        eyebrow="المراجعة الأكاديمية"
        title="مراجعة التسجيلات"
        description={studentFilter ? `تسجيلات الطالب #${studentFilter} التي تنتظر قرار المشرف.` : "استمع إلى القراءة، قارنها بالنص المرجعي، ثم أدخل التقييم واتخذ القرار."}
        actions={<AdminAction icon={RefreshCw} onClick={() => void refreshQueue()} disabled={refreshing || editingId !== null}>{refreshing ? "جاري التحديث..." : "تحديث القائمة"}</AdminAction>}
      />

      <AdminFeedbackToast feedback={message} onDismiss={() => setMessage({ kind: "success", text: "" })} />

      {studentFilter && (
        <div className="audio-review-filter">
          <UserRound size={18} aria-hidden="true" />
          <span>القائمة مفلترة لهذا الطالب فقط.</span>
          <Link href="/admin/audio-review" className="audio-review-filter-link">عرض جميع التسجيلات</Link>
        </div>
      )}

      {loading ? (
        <AdminPanel>
          <div className="audio-review-loading" role="status">
            <span className="spinner w-8 h-8 border-4" aria-hidden="true" />
            <span>جاري تحميل التسجيلات التي تحتاج مراجعة...</span>
          </div>
        </AdminPanel>
      ) : submissions.length === 0 ? (
        <AdminEmptyState
          title="لا توجد تسجيلات تنتظر المراجعة"
          description={studentFilter ? "لا توجد حاليًا تسجيلات معلقة لهذا الطالب." : "ستظهر هنا التسجيلات الحالية فقط عندما تحتاج إلى قرار المشرف."}
          action={<Headphones size={24} aria-hidden="true" />}
        />
      ) : (
        <div className="audio-review-workspace" data-testid="audio-review-queue">
          <AdminPanel className="audio-review-picker-panel">
            <AdminToolbar>
              <div className="audio-review-picker-meta">
                <span className="audio-review-picker-icon"><ListMusic size={19} aria-hidden="true" /></span>
                <div>
                  <strong id="audio-review-picker-label">التسجيل المطلوب</strong>
                  <span>{submissions.length} {submissions.length === 1 ? "تسجيل ينتظر المراجعة" : "تسجيلات تنتظر المراجعة"}</span>
                </div>
              </div>
              <label className="audio-review-select-wrap" htmlFor="audio-review-selection">
                <span className="sr-only">اختر الطالب والتسجيل</span>
                <select id="audio-review-selection" className="audio-review-select" value={editingId ?? ""} onChange={(event) => { const id = Number(event.target.value); if (id > 0) openReview(id); }} disabled={gradingId !== null} data-testid="audio-review-selector">
                  <option value="">اختر الطالب والتسجيل...</option>
                  {submissions.map((submission) => (
                    <option key={submission.id} value={submission.id}>
                      {(submission.student_name || "طالب غير معروف")} — {sessionLabel(submission.session_type)}
                      {submission.item_title ? ` — ${submission.item_title}` : ""} — {submissionDate(submission.submitted_at)}
                    </option>
                  ))}
                </select>
              </label>
            </AdminToolbar>
          </AdminPanel>

          {!activeSubmission ? (
            <AdminPanel>
              <div className="audio-review-welcome">
                <span className="audio-review-welcome-icon"><Headphones size={26} aria-hidden="true" /></span>
                <h2>اختر تسجيلًا لبدء المراجعة</h2>
                <p>اختر الطالب والتسجيل من القائمة أعلاه، ثم راجع النص والصوت واتخذ القرار من مساحة واحدة.</p>
              </div>
            </AdminPanel>
          ) : (
            <AdminPanel className="audio-review-review-panel">
              <div className="audio-review-compact-header">
                <div className="audio-review-student-block">
                  <span className="audio-review-avatar" aria-hidden="true">{(activeSubmission.student_name || "ط").trim().charAt(0)}</span>
                  <div>
                    <div className="audio-review-inline-meta"><span>{sessionLabel(activeSubmission.session_type)}</span><span>بانتظار المراجعة</span></div>
                    <h2>{activeSubmission.student_name || "طالب غير معروف"}</h2>
                    <p>{activeSubmission.item_title || "قراءة مسجلة"} · {submissionDate(activeSubmission.submitted_at)}</p>
                  </div>
                </div>
                {activeSubmission.student_id && <AdminAction href={`/admin/students/${activeSubmission.student_id}`} icon={UserRound} tone="ghost">ملف الطالب</AdminAction>}
              </div>

              <div className="audio-review-main-grid" data-testid="audio-review-form">
                <section className="audio-review-evidence-column" aria-labelledby="evidence-title">
                  <div className="audio-review-section-heading"><h3 id="evidence-title">النص والتسجيل</h3><p>قارن قراءة الطالب بالنص المرجعي قبل اعتماد النتيجة.</p></div>
                  <section className="audio-review-reference-card" aria-label="النص المطلوب" data-testid="audio-review-summary">
                    <span className="audio-review-card-label">النص المطلوب</span>
                    <p className="audio-review-reference-text">{activeSubmission.expected_reading_text || "لا يوجد نص مرجعي محفوظ لهذا التسجيل."}</p>
                  </section>
                  <AudioPlayer key={activeSubmission.storage_key} storageKey={activeSubmission.storage_key} />
                </section>

                <section className="audio-review-evaluation-column" aria-labelledby="evaluation-title">
                  <div className="audio-review-section-heading"><h3 id="evaluation-title">التقييم والقرار</h3><p>حدد النتيجة ثم أدخل بيانات القراءة اللازمة فقط.</p></div>
                  <fieldset className="audio-review-decision-compact">
                    <legend>نتيجة التسجيل</legend>
                    <div className="audio-review-segmented">
                      <button type="button" className={`audio-review-segment approve ${isValid ? "is-selected" : ""}`} onClick={() => { setIsValid(true); setMessage({ kind: "success", text: "" }); }} aria-pressed={isValid} aria-label="اعتماد القراءة">
                        <CheckCircle2 size={18} aria-hidden="true" /><span><strong>اعتماد القراءة</strong><small>التسجيل صالح للتقييم</small></span>
                      </button>
                      <button type="button" className={`audio-review-segment rerecord ${!isValid ? "is-selected" : ""}`} onClick={() => { setIsValid(false); setMessage({ kind: "success", text: "" }); }} aria-pressed={!isValid} aria-label="طلب إعادة تسجيل">
                        <RotateCcw size={18} aria-hidden="true" /><span><strong>إعادة تسجيل</strong><small>يحتاج محاولة جديدة</small></span>
                      </button>
                    </div>
                  </fieldset>

                  {isValid ? (
                    <div className="audio-review-score-compact" data-testid="audio-review-score-fields">
                      <NumberField id="target-units" label="إجمالي الوحدات" value={targetUnits} min={1} onChange={setTargetUnits} />
                      <NumberField id="deletions" label="الحذف" value={deletions} min={0} onChange={setDeletions} />
                      <NumberField id="substitutions" label="الاستبدال" value={substitutions} min={0} onChange={setSubstitutions} />
                      <NumberField id="insertions" label="الإضافة" value={insertions} min={0} onChange={setInsertions} />
                    </div>
                  ) : (
                    <div className="audio-review-rerecord-note"><RotateCcw size={18} aria-hidden="true" /><p><strong>سيُرسل طلب إعادة تسجيل مستقل.</strong> سيبقى التسجيل الحالي محفوظًا ولن يتوقف مسار الطالب.</p></div>
                  )}

                  <div className="audio-review-notes">
                    <button type="button" className="audio-review-notes-toggle" aria-expanded={notesOpen} onClick={() => setNotesOpen((current) => !current)}>
                      <span><strong>{notesOpen ? "إخفاء الملاحظات" : "إضافة ملاحظات"}</strong><small>اختياري — للنطق أو الطلاقة</small></span><span aria-hidden="true">{notesOpen ? "−" : "+"}</span>
                    </button>
                    {notesOpen && <div className="audio-review-notes-grid">
                      <label><span>ملاحظات النطق</span><textarea className="audio-review-notes-textarea" value={pronunciationNotes} onChange={(event) => setPronunciationNotes(event.target.value)} placeholder="اكتب ملاحظة مختصرة عند الحاجة..." /></label>
                      <label><span>ملاحظات الطلاقة</span><textarea className="audio-review-notes-textarea" value={fluencyNotes} onChange={(event) => setFluencyNotes(event.target.value)} placeholder="اكتب ملاحظة مختصرة عند الحاجة..." /></label>
                    </div>}
                  </div>
                </section>
              </div>

              <footer className={`audio-review-action-bar ${isValid ? "is-approve" : "is-rerecord"}`}>
                <div className="audio-review-action-summary"><strong>{isValid ? "اعتماد التسجيل وحفظ التقييم" : "إرسال طلب إعادة التسجيل"}</strong><span>{isValid ? "راجع الأرقام قبل الحفظ." : "سيبقى التسجيل الحالي محفوظًا."}</span></div>
                <div className="audio-review-action-buttons">
                  <AdminAction onClick={closeReview} disabled={gradingId === activeSubmission.id}>إلغاء</AdminAction>
                  <AdminAction tone={isValid ? "primary" : "danger"} icon={isValid ? Save : RotateCcw} onClick={() => void handleGrade(activeSubmission.id)} disabled={gradingId === activeSubmission.id}>
                    {gradingId === activeSubmission.id ? "جاري الحفظ..." : isValid ? "حفظ واعتماد" : "طلب إعادة تسجيل"}
                  </AdminAction>
                </div>
              </footer>
            </AdminPanel>
          )}
        </div>
      )}
    </AdminPage>
  );
}
