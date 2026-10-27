"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Activity,
  ArrowRight,
  BookOpen,
  Check,
  ClipboardList,
  Copy,
  Headphones,
  History,
  KeyRound,
  LayoutDashboard,
  LockKeyhole,
  Power,
  RefreshCw,
  Save,
  Star,
  User,
} from "lucide-react";
import V2Rewards from "@/components/rewards/V2Rewards";
import type { StudentV2Home } from "@/app/student/V2StudentDashboard";

type V2LessonItem = { lesson_id: string; title: string; level: string;
  state: "skipped" | "completed" | "waiting_review" | "in_progress" | "current" | "not_started"; session_id: number | null };
type SupervisorV2Home = StudentV2Home & {
  adaptation_decisions?: Array<{id: number; kind: string; reason_code: string; policy_version: string; unmastered_gap: boolean; created_at: string}>;
  support_assignments?: Array<{id: number; lesson_id: string; target_skill: string; focus: string; mode: string; status: string; created_at: string}>;
  lesson_overview?: { state: "ready" | "unavailable" | "awaiting_journey"; content_release_version: string | null; items: V2LessonItem[] };
};

const lessonStateLabels: Record<V2LessonItem["state"], string> = {
  skipped: "متجاوز بالتسكين", completed: "مكتمل", waiting_review: "بانتظار المراجعة",
  in_progress: "قيد الدرس", current: "التالي في المسار", not_started: "لم يبدأ",
};

import styles from "./student-detail.module.css";

interface Student {
  id: number;
  full_name: string;
  grade_level: number;
  created_at: string;
  current_level?: number;
  status: "active" | "inactive";
  posttest_enabled: boolean;
  posttest_eligible?: boolean;
  core_completed_items?: number;
  core_total_items?: number;
  core_completed?: boolean;
}

type TabKey = "overview" | "journey" | "tests" | "recordings" | "adaptation" | "account" | "history";
const TABS: Array<{key: TabKey; label: string; icon: typeof User}> = [
  {key: "overview", label: "نظرة عامة", icon: LayoutDashboard},
  {key: "journey", label: "المسار والدروس", icon: BookOpen},
  {key: "tests", label: "الاختبارات", icon: ClipboardList},
  {key: "recordings", label: "التسجيلات", icon: Headphones},
  {key: "adaptation", label: "التكيف والتقوية", icon: Activity},
  {key: "account", label: "الحساب", icon: KeyRound},
  {key: "history", label: "سجل المتابعة", icon: History},
];
const isTabKey = (candidate: string | null): candidate is TabKey =>
  TABS.some(tab => tab.key === candidate);
const tabDescription: Record<Exclude<TabKey, "account">, string> = {
  overview: "ملخص حالة الطالب وخطوته التالية.",
  journey: "دروس الطالب بحسب المستوى دون خلط ما تجاوزه بالتسكين بما أتقنه.",
  tests: "الاختبارات الرسمية ونتائجها المعتمدة.",
  recordings: "القراءات التي تحتاج مراجعة وآخر التسجيلات المقيمة.",
  adaptation: "قرارات الدعم التي تتخذها المنصة آليًا وأدلتها.",
  history: "آخر قرارات التكيف الموثقة لهذا الطالب.",
};

function apiError(data: unknown, fallback: string) {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return detail[0].msg;
  }
  return fallback;
}

export default function StudentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  // Next.js may preserve a dynamic route component across client-side URL changes.
  // Remounting by identity discards every previous student's local state and async setters.
  return <StudentDetailView key={id} id={id} />;
}

function StudentDetailView({ id }: { id: string }) {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [accessCode, setAccessCode] = useState<string | null>(null);
  const [student, setStudent] = useState<Student | null>(null);
  const [loadedStudentId, setLoadedStudentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  // Scope both data and errors to the URL student ID; never show a previous child's projection.
  const [v2Result, setV2Result] = useState<{ studentId: string; home: SupervisorV2Home | null; error: string } | null>(null);
  const [v2Reload, setV2Reload] = useState(0);
  const [editName, setEditName] = useState("");
  const [manualCode, setManualCode] = useState("");
  const [lessonLevel, setLessonLevel] = useState<"L1" | "L2" | "L3" | null>(null);
  const [copied, setCopied] = useState(false);
  const [visibleCodeForId, setVisibleCodeForId] = useState<string | null>(null);
  const codeVisible = visibleCodeForId === id;
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string }>({ kind: "success", text: "" });

  useEffect(() => {
    const fromUrl = new URLSearchParams(window.location.search).get("tab");
    if (isTabKey(fromUrl)) setActiveTab(fromUrl);
    const syncHistory = () => {
      const selected = new URLSearchParams(window.location.search).get("tab");
      setActiveTab(isTabKey(selected) ? selected : "overview");
    };
    window.addEventListener("popstate", syncHistory);
    return () => window.removeEventListener("popstate", syncHistory);
  }, [id]);

  const selectTab = (tab: TabKey) => {
    setVisibleCodeForId(null);
    setAccessCode(null);
    setCopied(false);
    setActiveTab(tab);
    const target = new URL(window.location.href);
    if (tab === "overview") target.searchParams.delete("tab");
    else target.searchParams.set("tab", tab);
    window.history.replaceState(null, "", target.pathname + target.search + target.hash);
  };

  useEffect(() => {
    let cancelled = false;
    if (!id) return;
    // Account identity is independent from the academic V2 projection.
    void fetch(`/api/v2/student/admin/students/${id}/account`, { cache: "no-store" })
      .then(async studentResponse => {
        if (!studentResponse.ok) {
          const body = await studentResponse.json().catch(() => null);
          throw new Error(apiError(body, studentResponse.status === 404 ? "لم يتم العثور على الطالب" : "تعذر تحميل بيانات الطالب"));
        }
        const studentData: Student & {source: string} = await studentResponse.json();
        if (studentData.source !== "himma_v2_account") throw new Error("مصدر الحساب غير متطابق مع V2.");
        if (String(studentData.id) !== id) throw new Error("ملف الطالب لا يطابق الحساب المطلوب.");
        if (cancelled) return;
        setStudent(current => ({...current, ...studentData}));
        setLoadedStudentId(id);
        setEditName(studentData.full_name);

      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setStudent(null);
          setLoadedStudentId(id);
          setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحميل بيانات الطالب" });
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [id]);

  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();
    const getStudentV2 = async () => {
      try {
        const reply = await fetch(`/api/v2/student/admin/students/${id}/home`, {
          cache: "no-store", signal: controller.signal,
        });
        if (!reply.ok) throw new Error("تعذر تحميل التقدم الدراسي لهذا الطالب.");
        const data = await reply.json() as SupervisorV2Home;
        if (data.mode !== "v2" || !data.current_action || !data.progress ||
            String(data.student?.id) !== id)
          throw new Error("ملف هِمّة V2 غير متطابق مع حساب الطالب المطلوب.");
        if (!controller.signal.aborted) setV2Result({ studentId: id, home: data, error: "" });
      } catch (reason) {
        if (!controller.signal.aborted) {
          setV2Result({
            studentId: id, home: null,
            error: reason instanceof Error ? reason.message : "تعذر الاتصال بسجل الطالب.",
          });
        }
      }
    };
    void getStudentV2();
    return () => controller.abort();
  }, [id, v2Reload]);

  const currentV2 = v2Result?.studentId === id ? v2Result : null;
  const v2Home = currentV2?.home ?? null;
  const placedV2 = v2Home?.journey && ["placed", "posttest_ready", "completed"].includes(v2Home.journey.placement_state);
  const currentV2Level = placedV2 ? v2Home?.journey?.current_level : null;
  const lessonCount = v2Home?.data_status === "ready" ? v2Home.progress.assigned_lessons : null;
  const officialPercent = v2Home?.data_status === "ready" ? v2Home.progress.display_percent : null;
  const officialCount = lessonCount == null || officialPercent == null ? null : v2Home?.progress.completed_lessons ?? null;
  const v2Score = (kind: "pretest" | "posttest") => {
    const assessment = v2Home?.assessments[kind];
    return assessment?.official && assessment.score_percent != null
      ? `${Math.round(assessment.score_percent * 10) / 10}%`
      : "لم تُعتمد نتيجة";
  };

  const saveStudentName = async () => {
    if (!student || editName.trim() === student.full_name) return;
    setBusy("name"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/v2/student/admin/students/${student.id}/account`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ full_name: editName }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر حفظ اسم الطالب"));
      setStudent(current => current ? {...current, ...data} : current); setEditName(data.full_name); setMessage({ kind: "success", text: "تم تحديث اسم الطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر حفظ اسم الطالب" }); }
    finally { setBusy(""); }
  };

  const toggleStudentStatus = async () => {
    if (!student) return;
    setBusy("status"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/v2/student/admin/students/${student.id}/account`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_active: student.status !== "active" }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث حالة الطالب"));
      setStudent(current => current ? {...current, ...data} : current); setMessage({ kind: "success", text: data.status === "active" ? "تم تفعيل حساب الطالب." : "تم إيقاف حساب الطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث حالة الطالب" }); }
    finally { setBusy(""); }
  };

  const changeAccessCode = async (manual: boolean) => {
    if (!student) return;
    if (manual && !/^\d{6}$/.test(manualCode)) { setMessage({ kind: "error", text: "الرمز اليدوي يجب أن يتكون من 6 أرقام." }); return; }
    setBusy("code"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/v2/student/admin/students/${student.id}/access-code`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ access_code: manual ? manualCode : null }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث رمز الدخول"));
      setStudent(current => current ? {...current, ...data} : current); setAccessCode(null); setManualCode(""); setVisibleCodeForId(null); setMessage({ kind: "success", text: "تم تحديث رمز دخول الطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث رمز الدخول" }); }
    finally { setBusy(""); }
  };

  const getAccessCode = async (): Promise<string> => {
    if (accessCode) return accessCode;
    const response = await fetch(`/api/v2/student/admin/students/${id}/access-code/reveal`, {method: "POST", cache: "no-store"});
    const body = await response.json().catch(() => null);
    if (!response.ok || String(body?.student_id) !== id || typeof body?.access_code !== "string") throw new Error("تعذر إظهار رمز الدخول.");
    setAccessCode(body.access_code);
    return body.access_code;
  };
  const revealAccessCode = async () => {
    if (codeVisible) { setVisibleCodeForId(null); setAccessCode(null); return; }
    setBusy("reveal");
    try { await getAccessCode(); setVisibleCodeForId(id); }
    catch (error) { setMessage({kind: "error", text: error instanceof Error ? error.message : "تعذر إظهار الرمز"}); }
    finally { setBusy(""); }
  };
  const copyAccessCode = async () => {
    setBusy("copy");
    try { await navigator.clipboard.writeText(await getAccessCode()); setCopied(true); window.setTimeout(() => setCopied(false), 1500); }
    catch { setMessage({kind:"error",text:"تعذر نسخ الرمز. أظهر الرمز وأعد المحاولة."}); }
    finally { setBusy(""); }
  };
  const reconcileV2Rewards = async () => {
    if (busy) return;
    setBusy("rewards-v2");
    try {
      const response=await fetch(`/api/v2/rewards/admin/students/${id}/reconcile`,{method:"POST"});
      const body=await response.json().catch(()=>null);
      if (!response.ok) throw new Error(apiError(body,"تعذر مزامنة الاستحقاقات"));
      setV2Reload(value=>value+1);setMessage({kind:"success",text:`تم التحقق من الاستحقاقات. منح جديدة: ${body.inserted}.`});
    } catch(error) {setMessage({kind:"error",text:error instanceof Error?error.message:"تعذر مزامنة الاستحقاقات"});}
    finally{setBusy("");}
  };


  if (loading || loadedStudentId !== id) return <div className={styles.loading}><span /><span /><span /></div>;
  if (!student) return <div className={styles.page}><div className="alert-error">{message.text || "لم يتم العثور على الطالب"}</div><Link href="/admin/students" className="btn-primary mt-4">العودة إلى الطلاب</Link></div>;

  const tabContent = (() => {
    if (activeTab !== "account") return (
      <section className={styles.panel} data-testid="supervisor-v2-overview">
        <div className={styles.panelHeader}>
          <div><h2>{TABS.find(tab => tab.key === activeTab)?.label}</h2>
            <p>{tabDescription[activeTab as Exclude<TabKey, "account">]}</p>
          </div><BookOpen size={20} aria-hidden="true" />
        </div>
        {!currentV2 && <p role="status" className={styles.muted}>جاري تحميل التقدم الدراسي...</p>}
        {currentV2?.error && <div className="alert-error" role="alert">
          {currentV2.error}
          <button className={styles.secondary} type="button" onClick={() => setV2Reload(value => value + 1)}>إعادة المحاولة</button>
        </div>}
        {v2Home && <>
          {v2Home.data_status !== "ready" && <p className={styles.notice}>بيانات المحتوى غير مكتملة؛ التقدم معلق حتى استعادتها.</p>}
          {activeTab === "overview" && <>
          <div className={styles.grid3}>
            <div className={styles.infoCard}><span>التسكين المعتمد</span>
              <strong data-testid="supervisor-v2-level">{currentV2Level == null ? "لم يُعتمد بعد" : `المستوى ${currentV2Level}`}</strong>
            </div>
            <div className={styles.infoCard}><span>تقدم الدروس المعيّنة</span>
              <strong data-testid="supervisor-v2-progress">{officialCount == null || lessonCount == null ? "بانتظار الاعتماد" : `${officialCount} من ${lessonCount} درس`}</strong>
            </div>
            <div className={styles.infoCard}><span>دروس تجاوزها التسكين</span>
              <strong>{currentV2Level == null ? "—" : v2Home.progress.skipped_by_placement}</strong>
            </div>
          </div>
          <div className={styles.progressBlock} style={{ marginTop: 14 }}>
            <div className={styles.progressMeta}><span>الدروس المنجزة</span>
              <strong>{officialPercent == null ? "غير متاح" : `${officialPercent}%`}</strong>
            </div>
            {officialPercent != null && <div className={styles.track} role="progressbar"
              aria-label="تقدم الدروس" aria-valuemin={0} aria-valuemax={100}
              aria-valuenow={officialPercent}>
              <div className={styles.fill} style={{ width: `${Math.min(100, Math.max(0, officialPercent))}%` }} />
            </div>}
            <p className={styles.muted} style={{ marginTop: 8 }}>القراءات التي تنتظر مراجعة المشرف لا تُحسب دروسًا مكتملة.</p>
          </div>
          <div className={styles.notice} data-testid="supervisor-v2-action" style={{ marginTop: 14 }}>
            <strong>الخطوة الحالية:</strong> {v2Home.current_action.label}
            {v2Home.current_action.action === "migration_review" && <p role="status">توجد جلسة تحتاج مراجعة المشرف قبل متابعة التعلم. لا يُحذف دليل الطالب ولا يُعتمد تلقائيًا.</p>}
            {v2Home.progress.pending_review > 0 && <p>توجد مراجعة قراءة معلّقة؛ لا تُحوَّل إلى نجاح تلقائي.</p>}
          </div>
          </>}
          {(activeTab === "overview" || activeTab === "tests") && <div className={styles.grid2} style={{ marginTop: 14 }}>
            <div className={styles.infoCard}><span>الاختبار القبلي</span><strong>{v2Score("pretest")}</strong></div>
            <div className={styles.infoCard}><span>الاختبار البعدي</span><strong>{v2Score("posttest")}</strong></div>
          </div>}
          {activeTab === "tests" && <p className={styles.muted}>النتائج غير المكتملة أو التي تنتظر مراجعة القراءة لا تُعامل على أنها صفر. الاختبار البعدي يُتاح تلقائيًا وفق شروط الرحلة.</p>}
          {activeTab === "journey" && <details className={styles.disclosure} data-testid="supervisor-lesson-disclosure" open>
            <summary>تفاصيل الدروس ({v2Home.lesson_overview?.items.length ?? 0})</summary>
            {v2Home.lesson_overview?.state === "unavailable" && <p className={styles.notice}>إصدار بنك المحتوى المثبت غير متاح؛ لم تُستخدم دروس إصدار آخر بديلًا.</p>}
            {(!v2Home.lesson_overview || v2Home.lesson_overview.state === "awaiting_journey") &&
              <p className={styles.muted}>تظهر حالة الدروس بعد بدء الرحلة واعتماد التسكين.</p>}
            {v2Home.lesson_overview?.state === "ready" && <>
              <div className={styles.levelFilter} role="group" aria-label="اختر المستوى لعرض دروسه">
                {(["L1", "L2", "L3"] as const).map((level, index) => {
                  const selected = lessonLevel ?? (currentV2Level ? `L${currentV2Level}` : "L1");
                  return <button key={level} type="button" aria-pressed={selected === level}
                    className={selected === level ? styles.levelFilterActive : styles.levelFilterButton}
                    onClick={() => setLessonLevel(level)}>
                    المستوى {["الأول", "الثاني", "الثالث"][index]}
                    <small> ({v2Home.lesson_overview?.items.filter(lesson => lesson.level === level).length ?? 0})</small>
                  </button>;
                })}
              </div>
              <div className={styles.journey} data-testid="supervisor-v2-lessons">
                {v2Home.lesson_overview.items.filter(lesson => lesson.level ===
                  (lessonLevel ?? (currentV2Level ? `L${currentV2Level}` : "L1"))).map(lesson => (
                  <div key={lesson.lesson_id}
                    className={`${styles.level} ${lesson.state === "completed" ? styles.levelDone : ["in_progress", "waiting_review", "current"].includes(lesson.state) ? styles.levelCurrent : styles.levelLocked}`}
                    data-testid="supervisor-v2-lesson" data-level-state={lesson.state}>
                    <small>{lesson.level} · {lesson.lesson_id}</small>
                    <strong>{lesson.title}</strong>
                    <span className={styles.muted}>{lessonStateLabels[lesson.state]}</span>
                  </div>
                ))}
              </div></>}
          </details>}
          {activeTab === "overview" && <>
            <details className={styles.disclosure}><summary>النجوم والشارات</summary><V2Rewards data={v2Home.rewards} variant="admin" /></details>
            <button type="button" className={styles.secondary} disabled={Boolean(busy)} onClick={() => void reconcileV2Rewards()}>مزامنة الاستحقاقات المثبتة</button>
          </>}
          {activeTab === "overview" && v2Home.journey?.placement_state === "posttest_ready" && <p className={styles.muted}>الاختبار البعدي متاح تلقائيًا للطالب بعد اكتمال الدروس والدعم ومراجعة القراءة.</p>}
          {activeTab === "recordings" && <>
            <p className={styles.muted}>عدد القراءات المعلقة في الدرس الحالي: {v2Home.progress.pending_review}. لا تُحتسب قراءة قبل مراجعتها.</p>
            <div className={styles.actions}>
              <Link className={styles.primary} href="/admin/v2-review-center?tab=assessments">مراجعة تسجيلات الاختبارات</Link>
              <Link className={styles.secondary} href="/admin/v2-review-center?tab=lessons">مراجعة قراءات الدروس</Link>
              <Link className={styles.secondary} href={`/admin/v2-review-center?tab=reviewed&student_id=${encodeURIComponent(id)}`}>تسجيلات الطالب المقيّمة</Link>
            </div>
          </>}
          {activeTab === "adaptation" && <>
            <p className={styles.muted}>الدعم والتكيف يحددهما النظام تلقائيًا. انتهاء نشاط الدعم لا يعني بالضرورة إتقان المهارة.</p>
            {(v2Home.support_assignments ?? []).length === 0
              ? <p className={styles.notice}>لا توجد مهام تقوية مسجلة لهذا الطالب في إصدار المحتوى الحالي.</p>
              : <div className={styles.history}>{v2Home.support_assignments?.map(item => (
                <div key={item.id} className={styles.historyItem}>
                  <div><strong>{item.lesson_id} · المهارة {item.target_skill}</strong>
                    <p className={styles.muted}>نوع الدعم: {item.mode === "targeted_support" ? "تقوية موجهة" : "تحقق إضافي"} · التركيز: {item.focus}</p></div>
                  <span>{item.status === "resolved" ? "انتهى النشاط" : item.status === "waiting_review" ? "بانتظار مراجعة الصوت" : item.status === "active" ? "جارٍ" : "حالة تاريخية"}</span>
                </div>
              ))}</div>}
          </>}
          {activeTab === "history" && <>
            {(v2Home.adaptation_decisions ?? []).length === 0
              ? <p className={styles.notice}>لا توجد قرارات تكيف مسجلة في الإصدار الحالي.</p>
              : <div className={styles.history}>{v2Home.adaptation_decisions?.map(item => (
                <div className={styles.historyItem} key={item.id}>
                  <div><strong>{item.kind === "next_lesson" ? "متابعة المسار" : item.kind === "targeted_support" ? "دعم موجه" : item.kind === "additional_check" ? "تحقق إضافي" : item.kind === "waiting_review" ? "بانتظار مراجعة الصوت" : "قرار سابق"}</strong>
                    <p className={styles.muted}>{item.reason_code}{item.unmastered_gap ? " · المهارة لم يُثبت إتقانها" : ""}</p></div>
                  <small>{new Date(item.created_at).toLocaleDateString("ar")}</small>
                </div>
              ))}</div>}
            <p className={styles.muted}>آخر 30 قرارًا من محرك التكيف V2 فقط. لا يتضمن هذا العرض سجلات الحساب الأمنية.</p>
          </>
        </>}
      </section>
    );
    if (activeTab === "account") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>الحساب والدخول</h2><p>اسم الطالب ورمز الدخول وحالة الحساب.</p></div><LockKeyhole size={20} aria-hidden="true" /></div>
        <div className={styles.formGrid}>
          <div className={styles.field}><label htmlFor="student-name">اسم الطالب</label><input id="student-name" className={styles.input} value={editName} onChange={(event) => setEditName(event.target.value)} minLength={2} maxLength={80} /></div>
          <button className={styles.primary} onClick={() => void saveStudentName()} disabled={busy === "name" || editName.trim() === student.full_name}><Save size={17} aria-hidden="true" />{busy === "name" ? "جاري الحفظ..." : "حفظ الاسم"}</button>
        </div>
        <div className={styles.codeBox} style={{ marginTop: 16 }}><div><span className={styles.muted}>رمز الدخول الحالي</span><strong className={styles.code} dir="ltr">{codeVisible ? accessCode : "••••••"}</strong></div><button type="button" className={styles.secondary} aria-pressed={codeVisible} disabled={Boolean(busy)} onClick={() => void revealAccessCode()}>{codeVisible ? "إخفاء الرمز" : "إظهار الرمز"}</button><button className={styles.secondary} disabled={Boolean(busy)} onClick={() => void copyAccessCode()}>{copied ? <Check size={17} aria-hidden="true" /> : <Copy size={17} aria-hidden="true" />}{copied ? "تم النسخ" : "نسخ الرمز"}</button></div>
        <div className={styles.grid2}>
          <button className={styles.secondary} onClick={() => void changeAccessCode(false)} disabled={busy === "code"}><RefreshCw size={17} aria-hidden="true" /> توليد رمز جديد</button>
          <div className={styles.formGrid}><div className={styles.field}><label htmlFor="manual-code">رمز يدوي من 6 أرقام</label><input id="manual-code" className={styles.input} inputMode="numeric" maxLength={6} value={manualCode} onChange={(event) => setManualCode(event.target.value.replace(/\D/g, "").slice(0,6))} placeholder="123456" dir="ltr" /></div><button className={styles.primary} onClick={() => void changeAccessCode(true)} disabled={busy === "code" || manualCode.length !== 6}>حفظ</button></div>
        </div>
      </section>
    );

  })();

  return (
    <div className={styles.page} dir="rtl">
      <header className={styles.header}>
        <div className={styles.identity}>
          <Link href="/admin/students" className={styles.back} aria-label="العودة إلى الطلاب"><ArrowRight size={22} aria-hidden="true" /></Link>
          <div className={styles.avatar}><User size={25} aria-hidden="true" /></div>
          <div className={styles.identityText}><small>ملف الطالب</small><h1>{student.full_name}</h1><p>الصف الثالث الابتدائي · المعرف #{student.id}</p></div>
        </div>
        <button className={`${styles.statusButton} ${student.status === "active" ? styles.statusButtonActive : styles.statusButtonInactive}`} onClick={() => void toggleStudentStatus()} disabled={busy === "status"}><Power size={17} aria-hidden="true" />{busy === "status" ? "جاري الحفظ..." : student.status === "active" ? "إيقاف الحساب" : "تفعيل الحساب"}</button>
      </header>

      {message.text && <div className={styles.message}><div className={message.kind === "success" ? "alert-success" : "alert-error"}>{message.text}</div></div>}

      <section className={styles.summary} aria-label="ملخص الطالب">
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><User size={20} aria-hidden="true" /></span><div><strong>{student.status === "active" ? "حساب نشط" : "حساب موقوف"}</strong><span>حالة الطالب</span></div></div>
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><BookOpen size={20} aria-hidden="true" /></span><div><strong>{currentV2Level == null ? "غير معتمد" : `المستوى ${currentV2Level}`}</strong><span>المستوى الحالي</span></div></div>
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><Star size={20} aria-hidden="true" /></span><div><strong>{officialPercent == null ? "—" : `${officialPercent}%`}</strong><span>تقدم الدروس</span></div></div>
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><ClipboardList size={20} aria-hidden="true" /></span><div><strong>{v2Home?.progress.pending_review ?? "—"}</strong><span>مراجعات معلّقة</span></div></div>
      </section>

      <nav className={styles.tabs} role="tablist" aria-label="أقسام ملف الطالب">
        {TABS.map((tab, index) => { const Icon = tab.icon; return <button key={tab.key} id={`student-tab-${tab.key}`}
          type="button" role="tab" aria-selected={activeTab === tab.key}
          aria-controls="student-detail-tabpanel" tabIndex={activeTab === tab.key ? 0 : -1}
          className={`${styles.tab} ${activeTab === tab.key ? styles.tabActive : ""}`}
          onClick={() => selectTab(tab.key)}
          onKeyDown={event => {
            const nextIndex = event.key === "ArrowLeft" ? (index + 1) % TABS.length
              : event.key === "ArrowRight" ? (index - 1 + TABS.length) % TABS.length
                : event.key === "Home" ? 0 : event.key === "End" ? TABS.length - 1 : null;
            if (nextIndex !== null) {
              event.preventDefault();
              selectTab(TABS[nextIndex].key);
              document.getElementById(`student-tab-${TABS[nextIndex].key}`)?.focus();
            }
          }}><Icon size={16} aria-hidden="true" />{tab.label}</button>; })}
      </nav>

      <div id="student-detail-tabpanel" role="tabpanel" aria-labelledby={`student-tab-${activeTab}`} tabIndex={0}>
        {tabContent}
      </div>
    </div>
  );
}
