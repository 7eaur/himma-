"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  Clock3,
  Headphones,
  ListMusic,
  Play,
  RefreshCw,
  RotateCcw,
  Save,
  UserRound,
  XCircle,
} from "lucide-react";
import AdminFeedbackToast from "@/components/admin/AdminFeedbackToast";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";

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

  useEffect(() => {
    setSrc(null);
    setError("");
  }, [storageKey]);

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
    <section className="audio-review-player" aria-label="الاستماع إلى التسجيل">
      <div className="audio-review-section-heading">
        <span className="audio-review-section-icon"><Headphones size={18} aria-hidden="true" /></span>
        <div>
          <strong>التسجيل المرسل</strong>
          <span>استمع إلى القراءة كاملة قبل اتخاذ القرار.</span>
        </div>
      </div>

      {src ? (
        <audio src={src} controls className="audio-review-native-player" preload="metadata" />
      ) : (
        <button type="button" className="audio-review-listen-button" onClick={() => void loadRecording()} disabled={loading}>
          <Play size={17} aria-hidden="true" />
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

function studentFilterFromLocation(): number | null {
  if (typeof window === "undefined") return null;
  const raw = new URLSearchParams(window.location.search).get("student_id");
  if (!raw || !/^\d+$/.test(raw)) return null;
  const parsed = Number(raw);
  return parsed > 0 ? parsed : null;
}

function submissionDate(value: string) {
  return new Date(value).toLocaleString("ar-SA", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function AudioReviewPage() {
  const [submissions, setSubmissions] = useState<AudioSubmission[]>([]);
  const [studentFilter] = useState<number | null>(studentFilterFromLocation);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string }>({ kind: "success", text: "" });
  const [gradingId, setGradingId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const editingRef = useRef<number | null>(null);
  const [isValid, setIsValid] = useState(true);
  const [targetUnits, setTargetUnits] = useState(10);
  const [deletions, setDeletions] = useState(0);
  const [substitutions, setSubstitutions] = useState(0);
  const [insertions, setInsertions] = useState(0);
  const [pronunciationNotes, setPronunciationNotes] = useState("");
  const [fluencyNotes, setFluencyNotes] = useState("");

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
        if (!cancelled && editingRef.current === null) setSubmissions(data);
      }).catch((caught: unknown) => {
        if (!cancelled) setMessage({ kind: "error", text: caught instanceof Error ? caught.message : "تعذر تحميل التسجيلات" });
      }).finally(() => { if (!cancelled) setLoading(false); });
    };
    fetchQueue();
    const interval = window.setInterval(fetchQueue, 30000);
    return () => { cancelled = true; window.clearInterval(interval); };
  }, [studentFilter]);

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
        description={studentFilter ? `تسجيلات الطالب #${studentFilter} التي تنتظر قرار المشرف.` : "مساحة عمل واحدة للاستماع، المقارنة بالنص المرجعي، ثم اعتماد القراءة أو طلب إعادة التسجيل."}
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
          <aside className="audio-review-sidebar" aria-label="قائمة التسجيلات المنتظرة">
            <div className="audio-review-sidebar-header">
              <div>
                <span className="audio-review-sidebar-kicker">قائمة الانتظار</span>
                <strong>{submissions.length} {submissions.length === 1 ? "تسجيل" : "تسجيلات"}</strong>
              </div>
              <ListMusic size={20} aria-hidden="true" />
            </div>

            <div className="audio-review-list">
              {submissions.map((submission, index) => {
                const active = editingId === submission.id;
                const locked = editingId !== null && !active;
                return (
                  <article
                    key={submission.id}
                    className={`audio-review-queue-item ${active ? "is-active" : ""} ${locked ? "is-locked" : ""}`}
                    data-testid="audio-review-item"
                  >
                    <div className="audio-review-queue-row">
                      <span className="audio-review-queue-index">{index + 1}</span>
                      <div className="audio-review-queue-copy">
                        <strong>{submission.student_name || "طالب غير معروف"}</strong>
                        <span>{sessionLabel(submission.session_type)}{submission.item_title ? ` · ${submission.item_title}` : ""}</span>
                      </div>
                    </div>
                    <div className="audio-review-queue-meta">
                      <Clock3 size={14} aria-hidden="true" />
                      <span>{submissionDate(submission.submitted_at)}</span>
                    </div>
                    <button
                      type="button"
                      className={active ? "audio-review-queue-button is-active" : "audio-review-queue-button"}
                      onClick={() => openReview(submission.id)}
                      disabled={locked}
                      aria-current={active ? "true" : undefined}
                    >
                      <Headphones size={16} aria-hidden="true" />
                      {active ? "المراجعة الحالية" : "بدء المراجعة"}
                    </button>
                  </article>
                );
              })}
            </div>
          </aside>

          <section className="audio-review-stage" aria-label="مساحة مراجعة التسجيل">
            {!activeSubmission ? (
              <div className="audio-review-welcome">
                <span className="audio-review-welcome-icon"><Headphones size={28} aria-hidden="true" /></span>
                <div>
                  <h2>اختر تسجيلًا من قائمة الانتظار</h2>
                  <p>ستظهر هنا هوية الطالب، النص المطلوب، مشغل التسجيل، القرار، ثم الملاحظات والحفظ بالترتيب.</p>
                </div>
                <ol className="audio-review-flow" aria-label="خطوات المراجعة">
                  <li><span>1</span>استمع</li>
                  <li><span>2</span>قارن بالنص</li>
                  <li><span>3</span>اتخذ القرار</li>
                  <li><span>4</span>احفظ</li>
                </ol>
              </div>
            ) : (
              <div className="audio-review-detail" data-testid="audio-review-form">
                <header className="audio-review-detail-header">
                  <div className="audio-review-student-block">
                    <span className="audio-review-avatar" aria-hidden="true">
                      {(activeSubmission.student_name || "ط").trim().charAt(0)}
                    </span>
                    <div>
                      <span className="audio-review-detail-kicker">{sessionLabel(activeSubmission.session_type)}</span>
                      <h2>{activeSubmission.student_name || "طالب غير معروف"}</h2>
                      <p>{activeSubmission.item_title || "قراءة مسجلة"} · {submissionDate(activeSubmission.submitted_at)}</p>
                    </div>
                  </div>
                  {activeSubmission.student_id && (
                    <Link href={`/admin/students/${activeSubmission.student_id}`} className="audio-review-profile-link">
                      <UserRound size={16} aria-hidden="true" />
                      فتح ملف الطالب
                    </Link>
                  )}
                </header>

                <div className="audio-review-flow audio-review-flow-inline" aria-label="تسلسل المراجعة">
                  <span className="is-current"><b>1</b> الاستماع والنص</span>
                  <span><b>2</b> القرار</span>
                  <span><b>3</b> الأدلة والملاحظات</span>
                  <span><b>4</b> الحفظ</span>
                </div>

                <div className="audio-review-evidence-grid">
                  <section className="audio-review-reference" aria-label="النص المطلوب">
                    <div className="audio-review-section-heading">
                      <span className="audio-review-section-icon">أ</span>
                      <div>
                        <strong>النص المطلوب</strong>
                        <span>قارن القراءة بهذا النص المرجعي.</span>
                      </div>
                    </div>
                    <p>{activeSubmission.expected_reading_text || "لا يوجد نص مرجعي محفوظ لهذا التسجيل."}</p>
                  </section>

                  <AudioPlayer storageKey={activeSubmission.storage_key} />
                </div>

                <section className="audio-review-decision" aria-label="نموذج قرار المراجعة">
                  <div className="audio-review-section-title">
                    <div>
                      <span className="audio-review-step-number">2</span>
                      <div>
                        <h3>قرار المراجعة</h3>
                        <p>اختر القرار أولًا. الحقول التالية تتغير بحسب القرار.</p>
                      </div>
                    </div>
                  </div>

                  <div className="audio-review-decision-grid" role="group" aria-label="نوع قرار التسجيل">
                    <button
                      type="button"
                      className={`audio-review-decision-card approve ${isValid ? "is-selected" : ""}`}
                      onClick={() => { setIsValid(true); setMessage({ kind: "success", text: "" }); }}
                      aria-pressed={isValid}
                    >
                      <CheckCircle2 size={22} aria-hidden="true" />
                      <span><strong>اعتماد القراءة</strong><small>القراءة صالحة ويمكن تسجيل نتيجة الأداء.</small></span>
                    </button>
                    <button
                      type="button"
                      className={`audio-review-decision-card rerecord ${!isValid ? "is-selected" : ""}`}
                      onClick={() => { setIsValid(false); setMessage({ kind: "success", text: "" }); }}
                      aria-pressed={!isValid}
                    >
                      <RotateCcw size={22} aria-hidden="true" />
                      <span><strong>طلب إعادة تسجيل</strong><small>ينشأ للطالب طلب مستقل ويُحفظ التسجيل السابق.</small></span>
                    </button>
                  </div>
                </section>

                {isValid ? (
                  <section className="audio-review-metrics" aria-label="أدلة تقييم القراءة">
                    <div className="audio-review-section-title">
                      <div>
                        <span className="audio-review-step-number">3</span>
                        <div>
                          <h3>أدلة التقييم</h3>
                          <p>أدخل الوحدات المستهدفة ثم أخطاء الحذف والاستبدال والإضافة.</p>
                        </div>
                      </div>
                    </div>
                    <div className="audio-review-metrics-grid">
                      <label>
                        <span>الوحدات المستهدفة</span>
                        <input className="input" type="number" min={1} step={1} value={targetUnits} onChange={(event) => setTargetUnits(Number(event.target.value))} />
                        <small>إجمالي الوحدات المقروءة في النص.</small>
                      </label>
                      <label>
                        <span>الحذف</span>
                        <input className="input" type="number" min={0} step={1} value={deletions} onChange={(event) => setDeletions(Number(event.target.value))} />
                        <small>وحدات لم يقرأها الطالب.</small>
                      </label>
                      <label>
                        <span>الاستبدال</span>
                        <input className="input" type="number" min={0} step={1} value={substitutions} onChange={(event) => setSubstitutions(Number(event.target.value))} />
                        <small>وحدات قُرئت بدلًا من الأصل.</small>
                      </label>
                      <label>
                        <span>الإضافة</span>
                        <input className="input" type="number" min={0} step={1} value={insertions} onChange={(event) => setInsertions(Number(event.target.value))} />
                        <small>وحدات زائدة على النص.</small>
                      </label>
                    </div>
                  </section>
                ) : (
                  <section className="audio-review-rerecord-note" aria-label="أثر طلب إعادة التسجيل">
                    <RotateCcw size={20} aria-hidden="true" />
                    <div>
                      <strong>إعادة التسجيل لن توقف مسار الطالب</strong>
                      <p>يظهر الطلب كمهمة مستقلة، ويبقى السؤال أو النشاط الحالي كما هو، ويُحفظ التسجيل السابق في سجل المراجعة.</p>
                    </div>
                  </section>
                )}

                <section className="audio-review-notes" aria-label="ملاحظات المراجعة">
                  <div className="audio-review-section-title compact">
                    <div>
                      <span className="audio-review-step-number">3</span>
                      <div>
                        <h3>ملاحظات المشرف</h3>
                        <p>سجّل فقط ما يفيد المتابعة الأكاديمية.</p>
                      </div>
                    </div>
                  </div>
                  <div className="audio-review-notes-grid">
                    <label>
                      <span>ملاحظات النطق</span>
                      <textarea className="input" value={pronunciationNotes} onChange={(event) => setPronunciationNotes(event.target.value)} placeholder="مثال: تكرار صعوبة في نطق صوت محدد..." />
                    </label>
                    <label>
                      <span>ملاحظات الطلاقة</span>
                      <textarea className="input" value={fluencyNotes} onChange={(event) => setFluencyNotes(event.target.value)} placeholder="مثال: توقفات متكررة أو سرعة غير مستقرة..." />
                    </label>
                  </div>
                </section>

                <footer className="audio-review-actions">
                  <div>
                    <span className="audio-review-step-number">4</span>
                    <div>
                      <strong>{isValid ? "اعتماد نتيجة المراجعة" : "إرسال طلب إعادة التسجيل"}</strong>
                      <small>راجع القرار قبل الحفظ؛ سيزال التسجيل من قائمة الانتظار بعد النجاح.</small>
                    </div>
                  </div>
                  <div className="audio-review-action-buttons">
                    <button type="button" className="btn-secondary" onClick={closeReview} disabled={gradingId === activeSubmission.id}>
                      <XCircle size={16} aria-hidden="true" /> إلغاء
                    </button>
                    <button type="button" className="btn-primary" onClick={() => void handleGrade(activeSubmission.id)} disabled={gradingId === activeSubmission.id}>
                      {gradingId === activeSubmission.id
                        ? "جاري الحفظ..."
                        : isValid
                          ? <><Save size={17} aria-hidden="true" /> حفظ واعتماد القراءة</>
                          : <><RotateCcw size={17} aria-hidden="true" /> إرسال طلب إعادة التسجيل</>}
                    </button>
                  </div>
                </footer>
              </div>
            )}
          </section>
        </div>
      )}
    </AdminPage>
  );
}
