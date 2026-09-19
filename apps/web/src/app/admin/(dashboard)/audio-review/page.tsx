"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ChevronDown,
  Clock3,
  Headphones,
  ListMusic,
  MessageSquareText,
  Play,
  RefreshCw,
  RotateCcw,
  Save,
  UserRound,
  XCircle,
} from "lucide-react";
import AdminFeedbackToast from "@/components/admin/AdminFeedbackToast";
import {
  AdminAction,
  AdminEmptyState,
  AdminNotice,
  AdminPage,
  AdminPageHeader,
  AdminPanel,
  AdminToolbar,
} from "@/components/admin/AdminUI";
import styles from "./audio-review.module.css";

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
    <div className={styles.audioBlock} aria-label="التسجيل الصوتي">
      <div className={styles.sectionHeading}>
        <span className={styles.sectionIcon}><Headphones size={18} aria-hidden="true" /></span>
        <div>
          <strong>التسجيل الصوتي</strong>
          <span>استمع إلى التسجيل قبل اعتماد القرار.</span>
        </div>
      </div>

      {src ? (
        <audio src={src} controls className={styles.audioPlayer} preload="metadata" />
      ) : (
        <button type="button" className={styles.listenButton} onClick={() => void loadRecording()} disabled={loading}>
          <Play size={17} aria-hidden="true" />
          {loading ? "جاري تجهيز التسجيل..." : "تشغيل التسجيل"}
        </button>
      )}

      {error && <p className="alert-error text-sm" role="alert">{error}</p>}
    </div>
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
  description,
  value,
  min,
  onChange,
}: {
  id: string;
  label: string;
  description: string;
  value: number;
  min: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className={styles.scoreField} htmlFor={id}>
      <span className={styles.scoreLabel}>{label}</span>
      <input
        id={id}
        className={styles.scoreInput}
        type="number"
        inputMode="numeric"
        min={min}
        step={1}
        value={value}
        aria-describedby={`${id}-help`}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <span id={`${id}-help`} className={styles.scoreHelp}>{description}</span>
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
  const didApplySubmissionFilter = useRef(false);
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
          if (
            submissionFilter
            && !didApplySubmissionFilter.current
            && data.some((submission) => submission.id === submissionFilter)
          ) {
            didApplySubmissionFilter.current = true;
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

  const resetReviewFields = () => {
    setIsValid(true);
    setTargetUnits(10);
    setDeletions(0);
    setSubstitutions(0);
    setInsertions(0);
    setPronunciationNotes("");
    setFluencyNotes("");
    setNotesOpen(false);
  };

  const openReview = (id: number) => {
    if (editingId !== null && editingId !== id) {
      setMessage({ kind: "error", text: "احفظ المراجعة الحالية أو ألغها قبل الانتقال إلى تسجيل آخر." });
      return;
    }
    editingRef.current = id;
    setEditingId(id);
    resetReviewFields();
    setMessage({ kind: "success", text: "" });
  };

  const closeReview = () => {
    editingRef.current = null;
    setEditingId(null);
    resetReviewFields();
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
      resetReviewFields();
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
    <AdminPage className={styles.page}>
      <AdminPageHeader
        eyebrow="المراجعة الأكاديمية"
        icon={Headphones}
        title="مراجعة التسجيلات"
        description={studentFilter ? `تسجيلات الطالب #${studentFilter} التي تنتظر قرار المشرف.` : "اختر تسجيلًا، استمع إلى القراءة، ثم قيّمها واحفظ القرار من مساحة واحدة."}
        actions={<AdminAction icon={RefreshCw} onClick={() => void refreshQueue()} disabled={refreshing || editingId !== null}>{refreshing ? "جاري التحديث..." : "تحديث"}</AdminAction>}
      />

      <AdminFeedbackToast feedback={message} onDismiss={() => setMessage({ kind: "success", text: "" })} />

      {studentFilter && (
        <AdminNotice>
          <UserRound size={18} aria-hidden="true" />
          <span>تعرض القائمة تسجيلات هذا الطالب فقط.</span>
          <Link href="/admin/audio-review" className={styles.filterLink}>عرض جميع التسجيلات</Link>
        </AdminNotice>
      )}

      {loading ? (
        <AdminPanel>
          <div className={styles.loading} role="status">
            <span className="spinner w-8 h-8 border-4" aria-hidden="true" />
            <span>جاري تحميل التسجيلات التي تحتاج مراجعة...</span>
          </div>
        </AdminPanel>
      ) : submissions.length === 0 ? (
        <AdminEmptyState
          title="لا توجد تسجيلات تنتظر المراجعة"
          description={studentFilter ? "لا توجد حاليًا تسجيلات معلقة لهذا الطالب." : "ستظهر هنا التسجيلات فقط عندما تحتاج إلى قرار المشرف."}
          action={<Headphones size={24} aria-hidden="true" />}
        />
      ) : (
        <div className={styles.workspace} data-testid="audio-review-queue">
          <AdminPanel className={styles.queuePanel}>
            <AdminToolbar>
              <div className={styles.queueLabel}>
                <span className={styles.queueIcon}><ListMusic size={18} aria-hidden="true" /></span>
                <div>
                  <label htmlFor="audio-review-selection">اختر الطالب والتسجيل</label>
                  <span>التسجيل النشط يظهر مباشرة في مساحة المراجعة.</span>
                </div>
              </div>

              <div className={styles.selectorWrap}>
                <select
                  id="audio-review-selection"
                  className={styles.selector}
                  value={editingId ?? ""}
                  onChange={(event) => {
                    const id = Number(event.target.value);
                    if (id > 0) openReview(id);
                  }}
                  disabled={gradingId !== null}
                  data-testid="audio-review-selector"
                >
                  <option value="">اختر تسجيلًا...</option>
                  {submissions.map((submission) => (
                    <option key={submission.id} value={submission.id}>
                      {(submission.student_name || "طالب غير معروف")} — {sessionLabel(submission.session_type)}
                      {submission.item_title ? ` — ${submission.item_title}` : ""} — {submissionDate(submission.submitted_at)}
                    </option>
                  ))}
                </select>
                <ChevronDown size={17} aria-hidden="true" />
              </div>

              <span className={styles.queueCount}>{submissions.length} {submissions.length === 1 ? "معلق" : "معلقة"}</span>
            </AdminToolbar>
          </AdminPanel>

          {!activeSubmission ? (
            <AdminPanel className={styles.emptyReview}>
              <Headphones size={26} aria-hidden="true" />
              <strong>اختر تسجيلًا لبدء المراجعة</strong>
              <span>ستظهر القراءة المرجعية والتسجيل وحقول التقييم هنا دون الانتقال إلى صفحة أخرى.</span>
            </AdminPanel>
          ) : (
            <AdminPanel className={styles.reviewPanel}>
              <div className={styles.reviewHeader} data-testid="audio-review-meta">
                <div className={styles.studentIdentity}>
                  <span className={styles.avatar} aria-hidden="true">{(activeSubmission.student_name || "ط").trim().charAt(0)}</span>
                  <div>
                    <h2>{activeSubmission.student_name || "طالب غير معروف"}</h2>
                    <p>{activeSubmission.item_title || "قراءة مسجلة"}</p>
                  </div>
                </div>

                <div className={styles.meta}>
                  <span className={styles.metaChip}>{sessionLabel(activeSubmission.session_type)}</span>
                  <span className={styles.pendingChip}><Clock3 size={14} aria-hidden="true" /> بانتظار المراجعة</span>
                  <span className={styles.dateText}>{submissionDate(activeSubmission.submitted_at)}</span>
                  {activeSubmission.student_id && (
                    <Link href={`/admin/students/${activeSubmission.student_id}`} className={styles.profileLink}>
                      <UserRound size={15} aria-hidden="true" />
                      ملف الطالب
                    </Link>
                  )}
                </div>
              </div>

              <div className={styles.reviewGrid} data-testid="audio-review-form">
                <section className={styles.evidenceColumn} aria-labelledby="evidence-title">
                  <div className={styles.columnHeading}>
                    <div>
                      <h3 id="evidence-title">المرجع والتسجيل</h3>
                      <p>قارن ما تسمعه بالنص المطلوب.</p>
                    </div>
                  </div>

                  <div className={styles.referenceBlock}>
                    <div className={styles.sectionHeading}>
                      <span className={styles.sectionIcon}>أ</span>
                      <div>
                        <strong>النص المطلوب</strong>
                        <span>النص المرجعي للقراءة.</span>
                      </div>
                    </div>
                    <p className={styles.referenceText}>{activeSubmission.expected_reading_text || "لا يوجد نص مرجعي محفوظ لهذا التسجيل."}</p>
                  </div>

                  <AudioPlayer key={activeSubmission.storage_key} storageKey={activeSubmission.storage_key} />
                </section>

                <section className={styles.assessmentColumn} aria-labelledby="assessment-title">
                  <div className={styles.columnHeading}>
                    <div>
                      <h3 id="assessment-title">التقييم والقرار</h3>
                      <p>حدد النتيجة ثم أدخل البيانات المطلوبة فقط.</p>
                    </div>
                  </div>

                  <fieldset className={styles.decisionGroup}>
                    <legend className="sr-only">قرار المراجعة</legend>
                    <button
                      type="button"
                      className={`${styles.decision} ${isValid ? styles.decisionSelected : ""}`}
                      onClick={() => { setIsValid(true); setMessage({ kind: "success", text: "" }); }}
                      aria-pressed={isValid}
                      aria-label="اعتماد القراءة"
                    >
                      <CheckCircle2 size={20} aria-hidden="true" />
                      <span><strong>اعتماد القراءة</strong><small>صالح للتقييم</small></span>
                    </button>

                    <button
                      type="button"
                      className={`${styles.decision} ${styles.rerecordDecision} ${!isValid ? styles.decisionSelected : ""}`}
                      onClick={() => { setIsValid(false); setMessage({ kind: "success", text: "" }); }}
                      aria-pressed={!isValid}
                      aria-label="طلب إعادة تسجيل"
                    >
                      <RotateCcw size={20} aria-hidden="true" />
                      <span><strong>إعادة تسجيل</strong><small>محاولة جديدة</small></span>
                    </button>
                  </fieldset>

                  {isValid ? (
                    <div className={styles.scoreGrid} data-testid="audio-review-score-fields">
                      <NumberField
                        id="target-units"
                        label="إجمالي الوحدات"
                        description="كل الوحدات المستهدفة."
                        value={targetUnits}
                        min={1}
                        onChange={setTargetUnits}
                      />
                      <NumberField
                        id="deletions"
                        label="الحذف"
                        description="وحدات لم تُقرأ."
                        value={deletions}
                        min={0}
                        onChange={setDeletions}
                      />
                      <NumberField
                        id="substitutions"
                        label="الاستبدال"
                        description="وحدات قُرئت بشكل مختلف."
                        value={substitutions}
                        min={0}
                        onChange={setSubstitutions}
                      />
                      <NumberField
                        id="insertions"
                        label="الإضافة"
                        description="وحدات زائدة."
                        value={insertions}
                        min={0}
                        onChange={setInsertions}
                      />
                    </div>
                  ) : (
                    <div className={styles.rerecordNote}>
                      <RotateCcw size={18} aria-hidden="true" />
                      <p><strong>سيُنشأ طلب إعادة تسجيل مستقل.</strong> يبقى التسجيل الحالي محفوظًا ولا يتوقف مسار الطالب.</p>
                    </div>
                  )}

                  <div className={styles.notesSection}>
                    <button
                      type="button"
                      className={styles.notesToggle}
                      aria-expanded={notesOpen}
                      onClick={() => setNotesOpen((current) => !current)}
                    >
                      <span><MessageSquareText size={17} aria-hidden="true" /> إضافة ملاحظات <small>اختياري</small></span>
                      <ChevronDown size={17} className={notesOpen ? styles.chevronOpen : ""} aria-hidden="true" />
                    </button>

                    {notesOpen && (
                      <div className={styles.notesGrid} data-testid="audio-review-notes">
                        <label>
                          <span>ملاحظات النطق</span>
                          <textarea
                            className={styles.notesTextarea}
                            value={pronunciationNotes}
                            onChange={(event) => setPronunciationNotes(event.target.value)}
                            placeholder="اكتب ملاحظة مختصرة عند الحاجة..."
                          />
                        </label>
                        <label>
                          <span>ملاحظات الطلاقة</span>
                          <textarea
                            className={styles.notesTextarea}
                            value={fluencyNotes}
                            onChange={(event) => setFluencyNotes(event.target.value)}
                            placeholder="اكتب ملاحظة مختصرة عند الحاجة..."
                          />
                        </label>
                      </div>
                    )}
                  </div>
                </section>
              </div>

              <footer className={styles.actionBar}>
                <div className={styles.actionSummary}>
                  {isValid ? <CheckCircle2 size={18} aria-hidden="true" /> : <RotateCcw size={18} aria-hidden="true" />}
                  <span>{isValid ? "اعتماد التسجيل وحفظ التقييم" : "إرسال طلب إعادة تسجيل"}</span>
                </div>
                <div className={styles.actionButtons}>
                  <button type="button" className={styles.cancelButton} onClick={closeReview} disabled={gradingId === activeSubmission.id}>
                    <XCircle size={16} aria-hidden="true" />
                    إلغاء
                  </button>
                  <button
                    type="button"
                    className={`${styles.saveButton} ${!isValid ? styles.saveRerecord : ""}`}
                    onClick={() => void handleGrade(activeSubmission.id)}
                    disabled={gradingId === activeSubmission.id}
                  >
                    {gradingId === activeSubmission.id
                      ? "جاري الحفظ..."
                      : isValid
                        ? <><Save size={17} aria-hidden="true" /> حفظ واعتماد</>
                        : <><RotateCcw size={17} aria-hidden="true" /> إرسال الطلب</>}
                  </button>
                </div>
              </footer>
            </AdminPanel>
          )}
        </div>
      )}
    </AdminPage>
  );
}
