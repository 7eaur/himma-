"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { CheckCircle2, Headphones, Play, RefreshCw, RotateCcw, Save, UserRound, XCircle } from "lucide-react";
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

  if (src) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700"><Headphones size={16} aria-hidden="true" /> التسجيل المرسل</div>
        <audio src={src} controls className="w-full" preload="metadata" />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <button type="button" className="btn-secondary" onClick={() => void loadRecording()} disabled={loading}>
        <Play size={16} aria-hidden="true" /> {loading ? "جاري تجهيز التسجيل..." : "استمع إلى التسجيل"}
      </button>
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

function studentFilterFromLocation(): number | null {
  if (typeof window === "undefined") return null;
  const raw = new URLSearchParams(window.location.search).get("student_id");
  if (!raw || !/^\d+$/.test(raw)) return null;
  const parsed = Number(raw);
  return parsed > 0 ? parsed : null;
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
        description={studentFilter ? `تسجيلات الطالب #${studentFilter} التي تنتظر قرار المشرف.` : "استمع إلى قراءة الطالب ثم اتخذ قرارًا واضحًا: اعتماد القراءة أو طلب إعادة التسجيل."}
        actions={<AdminAction icon={RefreshCw} onClick={() => void refreshQueue()} disabled={refreshing || editingId !== null}>{refreshing ? "جاري التحديث..." : "تحديث القائمة"}</AdminAction>}
      />

      <AdminFeedbackToast feedback={message} onDismiss={() => setMessage({ kind: "success", text: "" })} />

      {studentFilter && (
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4">
          <UserRound size={18} aria-hidden="true" />
          <span className="text-sm text-slate-700">القائمة مفلترة لهذا الطالب فقط.</span>
          <Link href="/admin/audio-review" className="btn-secondary">عرض جميع التسجيلات</Link>
        </div>
      )}

      {loading ? (
        <AdminPanel><p>جاري تحميل التسجيلات...</p></AdminPanel>
      ) : submissions.length === 0 ? (
        <AdminEmptyState
          title="لا توجد تسجيلات تنتظر المراجعة"
          description={studentFilter ? "لا توجد حاليًا تسجيلات معلقة لهذا الطالب." : "ستظهر هنا التسجيلات الحالية فقط عندما تحتاج إلى قرار المشرف."}
          action={<Headphones size={24} aria-hidden="true" />}
        />
      ) : (
        <div className="space-y-4" data-testid="audio-review-queue">
          {submissions.map((submission) => {
            const editing = editingId === submission.id;
            return (
              <AdminPanel key={submission.id}>
                <article className="space-y-4" data-testid="audio-review-item">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <strong className="text-base text-slate-900">{submission.student_name || "طالب غير معروف"}</strong>
                        {submission.student_id && <Link href={`/admin/students/${submission.student_id}`} className="text-sm font-medium text-teal-700 hover:underline">فتح ملف الطالب</Link>}
                      </div>
                      <p className="mt-1 text-sm text-slate-500">{sessionLabel(submission.session_type)}{submission.item_title ? ` · ${submission.item_title}` : ""}</p>
                    </div>
                    <span className="text-xs text-slate-500">{new Date(submission.submitted_at).toLocaleString("ar-SA")}</span>
                  </div>

                  {submission.expected_reading_text && (
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <span className="text-xs font-medium text-slate-500">النص المطلوب من الطالب</span>
                      <p className="mt-2 text-lg font-semibold leading-8 text-slate-900">{submission.expected_reading_text}</p>
                    </div>
                  )}

                  <AudioPlayer storageKey={submission.storage_key} />

                  {!editing ? (
                    <div className="flex justify-end">
                      <button type="button" className="btn-primary min-h-11" onClick={() => openReview(submission.id)}>
                        <Headphones size={17} aria-hidden="true" /> بدء المراجعة
                      </button>
                    </div>
                  ) : (
                    <section className="space-y-5 rounded-2xl border-2 border-slate-200 bg-white p-4 sm:p-5" aria-label="نموذج قرار المراجعة" data-testid="audio-review-form">
                      <div>
                        <h3 className="font-bold text-slate-900">قرار المراجعة</h3>
                        <p className="mt-1 text-sm text-slate-500">اختر القرار أولًا، ثم أدخل الأدلة اللازمة إن كانت القراءة صالحة.</p>
                      </div>

                      <div className="grid gap-3 sm:grid-cols-2" role="group" aria-label="نوع قرار التسجيل">
                        <button
                          type="button"
                          className={`min-h-14 rounded-xl border-2 px-4 font-semibold transition ${isValid ? "border-emerald-500 bg-emerald-50 text-emerald-800" : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"}`}
                          onClick={() => { setIsValid(true); setMessage({ kind: "success", text: "" }); }}
                          aria-pressed={isValid}
                        >
                          <span className="flex items-center justify-center gap-2"><CheckCircle2 size={19} aria-hidden="true" /> اعتماد القراءة</span>
                        </button>
                        <button
                          type="button"
                          className={`min-h-14 rounded-xl border-2 px-4 font-semibold transition ${!isValid ? "border-amber-500 bg-amber-50 text-amber-900" : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"}`}
                          onClick={() => { setIsValid(false); setMessage({ kind: "success", text: "" }); }}
                          aria-pressed={!isValid}
                        >
                          <span className="flex items-center justify-center gap-2"><RotateCcw size={19} aria-hidden="true" /> طلب إعادة تسجيل</span>
                        </button>
                      </div>

                      {isValid ? (
                        <div className="grid gap-3 md:grid-cols-4">
                          <label className="space-y-1"><span className="text-sm font-medium">الوحدات المستهدفة</span><input className="input" type="number" min={1} step={1} value={targetUnits} onChange={(event) => setTargetUnits(Number(event.target.value))} /></label>
                          <label className="space-y-1"><span className="text-sm font-medium">الحذف</span><input className="input" type="number" min={0} step={1} value={deletions} onChange={(event) => setDeletions(Number(event.target.value))} /></label>
                          <label className="space-y-1"><span className="text-sm font-medium">الاستبدال</span><input className="input" type="number" min={0} step={1} value={substitutions} onChange={(event) => setSubstitutions(Number(event.target.value))} /></label>
                          <label className="space-y-1"><span className="text-sm font-medium">الإضافة</span><input className="input" type="number" min={0} step={1} value={insertions} onChange={(event) => setInsertions(Number(event.target.value))} /></label>
                        </div>
                      ) : (
                        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm leading-6 text-amber-950">
                          الطالب سيشاهد مهمة إعادة التسجيل بشكل مستقل في مساره. لن يُجبر على ترك السؤال أو النشاط الحالي، وسيبقى التسجيل السابق محفوظًا في سجل المراجعة.
                        </div>
                      )}

                      <div className="grid gap-3 md:grid-cols-2">
                        <label className="space-y-1"><span className="text-sm font-medium">ملاحظات النطق</span><textarea className="input min-h-24" value={pronunciationNotes} onChange={(event) => setPronunciationNotes(event.target.value)} placeholder="اختياري" /></label>
                        <label className="space-y-1"><span className="text-sm font-medium">ملاحظات الطلاقة</span><textarea className="input min-h-24" value={fluencyNotes} onChange={(event) => setFluencyNotes(event.target.value)} placeholder="اختياري" /></label>
                      </div>

                      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                        <button type="button" className="btn-secondary min-h-11" onClick={closeReview} disabled={gradingId === submission.id}><XCircle size={16} aria-hidden="true" /> إلغاء</button>
                        <button type="button" className="btn-primary min-h-11" onClick={() => void handleGrade(submission.id)} disabled={gradingId === submission.id}>
                          {gradingId === submission.id ? "جاري الحفظ..." : isValid ? <><Save size={17} aria-hidden="true" /> حفظ واعتماد القراءة</> : <><RotateCcw size={17} aria-hidden="true" /> إرسال طلب إعادة التسجيل</>}
                        </button>
                      </div>
                    </section>
                  )}
                </article>
              </AdminPanel>
            );
          })}
        </div>
      )}
    </AdminPage>
  );
}
