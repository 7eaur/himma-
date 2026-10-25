"use client";

import { useEffect, useMemo, useState } from "react";
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
  LockKeyhole,
  Play,
  Power,
  RefreshCw,
  Save,
  ShieldCheck,
  Star,
  User,
} from "lucide-react";
import CanonicalRewardBadge from "@/components/rewards/CanonicalRewardBadge";
import type { StudentV2Home } from "@/app/student/V2StudentDashboard";

type V2LessonItem = { lesson_id: string; title: string; level: string;
  state: "skipped" | "completed" | "waiting_review" | "in_progress" | "current" | "not_started"; session_id: number | null };
type SupervisorV2Home = StudentV2Home & {
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
  access_code: string;
  created_at: string;
  current_level: number;
  status: "active" | "inactive";
  posttest_enabled: boolean;
  posttest_eligible: boolean;
  core_completed_items: number;
  core_total_items: number;
  core_completed: boolean;
}

interface AdaptationDecision {
  decision_id: number;
  source: "automatic" | "manual";
  action: "promote" | "stay" | "support" | "demote" | "hold" | "override";
  mastery_score: number | null;
  previous_level: number;
  new_level: number;
  weakest_skill_id: number | null;
  recommended_item_id: number | null;
  valid_attempt_count: number;
  consecutive_low_count: number;
  explanation: Record<string, unknown>;
  manual_reason?: string | null;
  created_at: string;
}

interface RewardEvent {
  id: number;
  type: "stars" | "badge";
  key?: string | null;
  stars: number | null;
  label: string;
  catalog_version?: string | null;
  asset_id?: string | null;
  asset_slug?: string | null;
  asset_path?: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

type JourneyLevelState = "locked" | "active" | "completed" | "skipped" | "ready";
interface JourneyLevel {
  level_id: number;
  name: string;
  state: JourneyLevelState;
  completed_items: number;
  total_items: number;
  session_id: number | null;
}
interface JourneySummary {
  pretest_completed: boolean;
  starting_level: number | null;
  current_level: number;
  levels: JourneyLevel[];
  learning_journey_completed: boolean;
  posttest_enabled: boolean;
  posttest_completed: boolean;
  posttest_ready: boolean;
}

type SourceState = "loading" | "loaded" | "error";
type TabKey = "v2" | "overview" | "journey" | "tests" | "recordings" | "adaptation" | "account" | "history";

const TABS: Array<{ key: TabKey; label: string; icon: typeof User }> = [
  { key: "v2", label: "مسار هِمّة V2", icon: BookOpen },
  { key: "overview", label: "نظرة عامة", icon: User },
  { key: "journey", label: "المسار والتقدم", icon: BookOpen },
  { key: "tests", label: "الاختبارات", icon: ClipboardList },
  { key: "recordings", label: "التسجيلات", icon: Headphones },
  { key: "adaptation", label: "التقوية والتكيف", icon: Activity },
  { key: "account", label: "الحساب", icon: KeyRound },
  { key: "history", label: "السجل", icon: History },
];

const ACTION_LABEL: Record<string, string> = {
  promote: "ترقية مستوى",
  stay: "استمرار في المستوى",
  support: "تقوية موجهة",
  demote: "خفض مستوى واحد",
  hold: "انتظار بيانات كافية",
  override: "تعديل يدوي",
};

const REASON_LABEL: Record<string, string> = {
  second_consecutive_low_mastery: "انخفاض الإتقان في قرارين متتاليين",
  low_mastery_support_first: "الإتقان منخفض؛ تبدأ التقوية قبل أي قرار آخر",
  top_level_mastery: "إتقان مرتفع في أعلى مستوى",
  promotion_waiting_for_skill_coverage: "الإتقان مرتفع لكن تغطية المهارات لم تكتمل",
  promotion_blocked_by_skill_floor: "توجد مهارة مطلوبة لم تصل إلى الحد المطلوب",
  mastery_and_skill_gates_passed: "اجتاز الإتقان وتغطية المهارات والبوابات المطلوبة",
  mastery_in_stability_band: "الأداء في نطاق الاستمرار الحالي",
  researcher_manual_override: "قرار يدوي موثق من المشرف",
};

const JOURNEY_STATE_LABEL: Record<JourneyLevelState, string> = {
  completed: "مكتمل",
  active: "قيد التعلم",
  ready: "جاهز للبدء",
  skipped: "تم تجاوزه وفق نقطة البداية",
  locked: "لاحقًا",
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
  const [activeTab, setActiveTab] = useState<TabKey>("v2");
  const [student, setStudent] = useState<Student | null>(null);
  const [journey, setJourney] = useState<JourneySummary | null>(null);
  const [history, setHistory] = useState<AdaptationDecision[]>([]);
  const [rewards, setRewards] = useState<RewardEvent[]>([]);
  const [historyState, setHistoryState] = useState<SourceState>("loading");
  const [rewardsState, setRewardsState] = useState<SourceState>("loading");
  const [journeyState, setJourneyState] = useState<SourceState>("loading");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  // Scope both data and errors to the URL student ID; never show a previous child's projection.
  const [v2Result, setV2Result] = useState<{ studentId: string; home: SupervisorV2Home | null; error: string } | null>(null);
  const [v2Reload, setV2Reload] = useState(0);
  const [overrideLevel, setOverrideLevel] = useState("1");
  const [overrideReason, setOverrideReason] = useState("");
  const [editName, setEditName] = useState("");
  const [manualCode, setManualCode] = useState("");
  const [copied, setCopied] = useState(false);
  const [visibleCodeForId, setVisibleCodeForId] = useState<string | null>(null);
  const codeVisible = visibleCodeForId === id;
  const [message, setMessage] = useState<{ kind: "success" | "error"; text: string }>({ kind: "success", text: "" });

  const loadSecondarySource = async <T,>(response: Response, setter: (value: T) => void, stateSetter: (state: SourceState) => void) => {
    if (!response.ok) {
      stateSetter("error");
      return;
    }
    setter(await response.json() as T);
    stateSetter("loaded");
  };

  useEffect(() => {
    let cancelled = false;
    if (!id) return;
    void Promise.all([
      fetch(`/api/researcher/students/${id}`, { cache: "no-store" }),
      fetch(`/api/researcher/students/${id}/journey`, { cache: "no-store" }),
      fetch(`/api/researcher/students/${id}/adaptation/history`, { cache: "no-store" }),
      fetch(`/api/researcher/students/${id}/rewards`, { cache: "no-store" }),
    ])
      .then(async ([studentResponse, journeyResponse, historyResponse, rewardsResponse]) => {
        if (!studentResponse.ok) {
          const body = await studentResponse.json().catch(() => null);
          throw new Error(apiError(body, studentResponse.status === 404 ? "لم يتم العثور على الطالب" : "تعذر تحميل بيانات الطالب"));
        }
        const studentData: Student = await studentResponse.json();
        if (cancelled) return;
        setStudent(studentData);
        setEditName(studentData.full_name);
        setOverrideLevel(String(studentData.current_level));
        await Promise.all([
          loadSecondarySource<JourneySummary>(journeyResponse, setJourney, setJourneyState),
          loadSecondarySource<AdaptationDecision[]>(historyResponse, setHistory, setHistoryState),
          loadSecondarySource<RewardEvent[]>(rewardsResponse, setRewards, setRewardsState),
        ]);
      })
      .catch((error: unknown) => {
        if (!cancelled) setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحميل بيانات الطالب" });
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
        if (!reply.ok) throw new Error("تعذر تحميل سجل هِمّة V2 لهذا الطالب. لا يمكن عرض أرقام V1 بدلًا عنه.");
        const data = await reply.json() as SupervisorV2Home;
        if (data.mode !== "v2" || !data.current_action || !data.progress ||
            String(data.student?.id) !== id)
          throw new Error("ملف هِمّة V2 غير متطابق مع حساب الطالب المطلوب.");
        if (!controller.signal.aborted) setV2Result({ studentId: id, home: data, error: "" });
      } catch (reason) {
        if (!controller.signal.aborted) {
          setV2Result({
            studentId: id, home: null,
            error: reason instanceof Error ? reason.message : "تعذر الاتصال بمصدر V2.",
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

  const latestDecision = useMemo(() => history.at(-1) ?? null, [history]);
  const totalStars = rewards.reduce((sum, reward) => sum + (reward.stars ?? 0), 0);
  const badges = rewards.filter((reward) => reward.type === "badge");
  const visualBadges = badges.filter((reward): reward is RewardEvent & { asset_path: string } => Boolean(reward.asset_path));

  const refreshJourney = async () => {
    if (!student) return;
    setJourneyState("loading");
    try {
      const response = await fetch(`/api/researcher/students/${student.id}/journey`, { cache: "no-store" });
      await loadSecondarySource<JourneySummary>(response, setJourney, setJourneyState);
    } catch {
      setJourneyState("error");
    }
  };

  const refreshAdaptiveEvidence = async () => {
    if (!student) return;
    setHistoryState("loading");
    setRewardsState("loading");
    try {
      const [historyResponse, rewardsResponse] = await Promise.all([
        fetch(`/api/researcher/students/${student.id}/adaptation/history`, { cache: "no-store" }),
        fetch(`/api/researcher/students/${student.id}/rewards`, { cache: "no-store" }),
      ]);
      await Promise.all([
        loadSecondarySource<AdaptationDecision[]>(historyResponse, setHistory, setHistoryState),
        loadSecondarySource<RewardEvent[]>(rewardsResponse, setRewards, setRewardsState),
      ]);
    } catch {
      setHistoryState("error");
      setRewardsState("error");
    }
  };

  const saveStudentName = async () => {
    if (!student || editName.trim() === student.full_name) return;
    setBusy("name"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ full_name: editName }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر حفظ اسم الطالب"));
      setStudent(data); setEditName(data.full_name); setMessage({ kind: "success", text: "تم تحديث اسم الطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر حفظ اسم الطالب" }); }
    finally { setBusy(""); }
  };

  const toggleStudentStatus = async () => {
    if (!student) return;
    setBusy("status"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_active: student.status !== "active" }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث حالة الطالب"));
      setStudent(data); setMessage({ kind: "success", text: data.status === "active" ? "تم تفعيل حساب الطالب." : "تم إيقاف حساب الطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث حالة الطالب" }); }
    finally { setBusy(""); }
  };

  const changeAccessCode = async (manual: boolean) => {
    if (!student) return;
    if (manual && !/^\d{6}$/.test(manualCode)) { setMessage({ kind: "error", text: "الرمز اليدوي يجب أن يتكون من 6 أرقام." }); return; }
    setBusy("code"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}/access-code`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ access_code: manual ? manualCode : null }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث رمز الدخول"));
      setStudent(data); setManualCode(""); setVisibleCodeForId(null); setMessage({ kind: "success", text: "تم تحديث رمز دخول الطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث رمز الدخول" }); }
    finally { setBusy(""); }
  };

  const copyAccessCode = async () => {
    if (!student) return;
    await navigator.clipboard.writeText(student.access_code); setCopied(true); window.setTimeout(() => setCopied(false), 1500);
  };

  const updatePosttestAccess = async () => {
    if (!student) return;
    setBusy("posttest"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}/posttest-access`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enabled: !student.posttest_enabled }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر تحديث إتاحة الاختبار البعدي"));
      setStudent(data); await refreshJourney(); setMessage({ kind: "success", text: data.posttest_enabled ? "تم فتح الاختبار البعدي للطالب." : "تم إيقاف الاختبار البعدي للطالب." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر تحديث إتاحة الاختبار البعدي" }); }
    finally { setBusy(""); }
  };

  const saveManualOverride = async () => {
    if (!student) return;
    setBusy("override"); setMessage({ kind: "success", text: "" });
    try {
      const response = await fetch(`/api/researcher/students/${student.id}/adaptation/manual-override`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ new_level: Number(overrideLevel), reason: overrideReason.trim() }) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiError(data, "تعذر حفظ التعديل اليدوي"));
      const refreshed = await fetch(`/api/researcher/students/${student.id}`, { cache: "no-store" });
      if (refreshed.ok) { const updated: Student = await refreshed.json(); setStudent(updated); setEditName(updated.full_name); }
      setOverrideReason(""); await Promise.all([refreshAdaptiveEvidence(), refreshJourney()]); setMessage({ kind: "success", text: "تم حفظ قرار المشرف مع سببه في السجل." });
    } catch (error) { setMessage({ kind: "error", text: error instanceof Error ? error.message : "تعذر حفظ التعديل اليدوي" }); }
    finally { setBusy(""); }
  };

  if (loading) return <div className={styles.loading}><span /><span /><span /></div>;
  if (!student) return <div className={styles.page}><div className="alert-error">{message.text || "لم يتم العثور على الطالب"}</div><Link href="/admin/students" className="btn-primary mt-4">العودة إلى الطلاب</Link></div>;

  const activeJourneyLevel = journey?.levels.find((level) => level.state === "active" || level.state === "ready") ?? journey?.levels.find((level) => level.level_id === student.current_level);
  const progressCompleted = activeJourneyLevel?.completed_items ?? student.core_completed_items;
  const progressTotal = activeJourneyLevel?.total_items ?? student.core_total_items;
  const progressPercent = Math.round((progressCompleted / Math.max(1, progressTotal)) * 100);
  const reasonKey = typeof latestDecision?.explanation?.reason === "string" ? latestDecision.explanation.reason : "";

  const sourceError = (label: string, retry: () => void) => <div className="alert-error" role="status">تعذر تحميل {label}. <button type="button" className={styles.secondary} onClick={retry}>إعادة المحاولة</button></div>;

  const tabContent = (() => {
    if (activeTab === "v2") return (
      <section className={styles.panel} data-testid="supervisor-v2-overview">
        <div className={styles.panelHeader}>
          <div><h2>ملف الطالب الأكاديمي · هِمّة V2</h2>
            <p>تسكين ودروس واختبارات من المصدر الحالي فقط. أرشيف V1 محفوظ في الأقسام الأخرى ولا يختلط بهذه الأرقام.</p>
          </div><BookOpen size={20} aria-hidden="true" />
        </div>
        {!currentV2 && <p role="status" className={styles.muted}>جاري تحميل التقدم المعتمد من V2...</p>}
        {currentV2?.error && <div className="alert-error" role="alert">
          {currentV2.error}
          <button className={styles.secondary} type="button" onClick={() => setV2Reload(value => value + 1)}>إعادة المحاولة</button>
        </div>}
        {v2Home && <>
          {v2Home.data_status !== "ready" && <p className={styles.notice}>بيانات إصدار المحتوى غير مكتملة؛ التقدم معلق ولا يمكن تقديره من النسخة القديمة.</p>}
          <div className={styles.grid3}>
            <div className={styles.infoCard}><span>التسكين المعتمد V2</span>
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
            <div className={styles.progressMeta}><span>الإنجاز الرسمي من دروس V2 فقط</span>
              <strong>{officialPercent == null ? "غير متاح" : `${officialPercent}%`}</strong>
            </div>
            {officialPercent != null && <div className={styles.track} role="progressbar"
              aria-label="تقدم دروس همة V2" aria-valuemin={0} aria-valuemax={100}
              aria-valuenow={officialPercent}>
              <div className={styles.fill} style={{ width: `${Math.min(100, Math.max(0, officialPercent))}%` }} />
            </div>}
            <p className={styles.muted} style={{ marginTop: 8 }}>القراءات التي تنتظر مراجعة المشرف لا تُحسب دروسًا مكتملة.</p>
          </div>
          <div className={styles.notice} data-testid="supervisor-v2-action" style={{ marginTop: 14 }}>
            <strong>الخطوة الحالية:</strong> {v2Home.current_action.label}
            {v2Home.current_action.action === "migration_review" && <p>يلزم قرار مشرف بشأن الانتقال من البيانات التاريخية قبل السماح بإعادة الاختبار القبلي.</p>}
            {v2Home.progress.pending_review > 0 && <p>توجد مراجعة قراءة معلّقة؛ لا تُحوَّل إلى نجاح تلقائي.</p>}
          </div>
          <div className={styles.grid2} style={{ marginTop: 14 }}>
            <div className={styles.infoCard}><span>الاختبار القبلي V2</span><strong>{v2Score("pretest")}</strong></div>
            <div className={styles.infoCard}><span>الاختبار البعدي V2</span><strong>{v2Score("posttest")}</strong></div>
          </div>
          <div style={{ marginTop: 20 }}>
            <h3 className="font-bold text-navy mb-2">دروس V2 المعتمدة (19 درسًا)</h3>
            {v2Home.lesson_overview?.state === "unavailable" && <p className={styles.notice}>إصدار بنك المحتوى المثبت غير متاح؛ لم تُستخدم دروس إصدار آخر بديلًا.</p>}
            {(!v2Home.lesson_overview || v2Home.lesson_overview.state === "awaiting_journey") &&
              <p className={styles.muted}>تظهر حالة الدروس بعد بدء الرحلة واعتماد التسكين.</p>}
            {v2Home.lesson_overview?.state === "ready" &&
              <div className={styles.journey} data-testid="supervisor-v2-lessons">
                {v2Home.lesson_overview.items.map(lesson => (
                  <div key={lesson.lesson_id}
                    className={`${styles.level} ${lesson.state === "completed" ? styles.levelDone : ["in_progress", "waiting_review", "current"].includes(lesson.state) ? styles.levelCurrent : styles.levelLocked}`}
                    data-testid="supervisor-v2-lesson" data-level-state={lesson.state}>
                    <small>{lesson.level} · {lesson.lesson_id}</small>
                    <strong>{lesson.title}</strong>
                    <span className={styles.muted}>{lessonStateLabels[lesson.state]}</span>
                  </div>
                ))}
              </div>}
          </div>
          <div className={styles.actions} style={{ marginTop: 16 }}>
            <Link className={styles.primary} href="/admin/v2-assessments">تقييمات ومراجعات V2</Link>
            <Link className={styles.secondary} href="/admin/v2-lesson-review">مراجعة الدروس</Link>
            <Link className={styles.secondary} href="/admin/v2-reviewed-recordings">التسجيلات المُقيَّمة</Link>
          </div>
        </>}
      </section>
    );
    if (activeTab === "overview") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>أرشيف الطالب التاريخي V1</h2><p>معلومات محفوظة للتوثيق والمقارنة، وليست تقدم V2.</p></div><User size={20} aria-hidden="true" /></div>
        <div className={styles.grid3}>
          <div className={styles.infoCard}><span>الصف</span><strong>الثالث الابتدائي</strong></div>
          <div className={styles.infoCard}><span>المستوى الحالي</span><strong>المستوى التاريخي V1: {student.current_level}</strong></div>
          <div className={styles.infoCard}><span>تاريخ الإضافة</span><strong>{new Date(student.created_at).toLocaleDateString("ar-SA")}</strong></div>
        </div>
        <div className={styles.rewardRow} style={{ marginTop: 14 }}>
          <div className={styles.reward}><span className={styles.muted}>نجوم V1 التاريخية</span><strong>{rewardsState === "loaded" ? totalStars : "—"}</strong></div>
          <div className={styles.reward}><span className={styles.muted}>شارات V1 التاريخية</span><strong>{rewardsState === "loaded" ? badges.length : "—"}</strong></div>
          <div className={styles.reward}><span className={styles.muted}>تقدم أنشطة V1 التاريخي</span><strong>{journeyState === "loaded" ? `${progressPercent}%` : "—"}</strong></div>
        </div>
        {rewardsState === "error" && <div style={{ marginTop: 12 }}>{sourceError("المكافآت", () => void refreshAdaptiveEvidence())}</div>}
        {rewardsState === "loaded" && badges.length === 0 && <p className={styles.muted} style={{ marginTop: 12 }}>لا توجد شارات مكتسبة لهذا الطالب بعد.</p>}
        {rewardsState === "loaded" && visualBadges.length > 0 && <div className={styles.badgeGallery} style={{ marginTop: 12 }}>{visualBadges.map((badge) => <CanonicalRewardBadge key={badge.id} label={badge.label} assetPath={badge.asset_path} rewardKey={badge.key} variant="admin" />)}</div>}
        {rewardsState === "loaded" && badges.length > visualBadges.length && <div className={styles.notice} style={{ marginTop: 12 }}>توجد شارة تاريخية بلا أصل مرئي معروف في النسخة الحالية من Reward Catalog؛ لم يتم اختلاق صورة بديلة لها.</div>}
      </section>
    );

    if (activeTab === "journey") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>المسار التاريخي V1</h2><p>سجل مستويات النسخة القديمة فقط، وليس مسار دروس V2.</p></div><BookOpen size={20} aria-hidden="true" /></div>
        {journeyState === "loading" && <p className={styles.muted}>جاري تحميل المسار الأكاديمي...</p>}
        {journeyState === "error" && sourceError("المسار الأكاديمي", () => void refreshJourney())}
        {journeyState === "loaded" && journey && <>
          <div className={styles.progressBlock}>
            <div className={styles.progressMeta}><span>الأنشطة الأساسية في مسار V1 التاريخي</span><strong>{progressCompleted} من {progressTotal}</strong></div>
            <div className={styles.track} role="progressbar" aria-label="تقدم الأنشطة الأساسية في المستوى النشط" aria-valuemin={0} aria-valuemax={progressTotal} aria-valuenow={progressCompleted} aria-valuetext={`${progressCompleted} من ${progressTotal}`}><div className={styles.fill} style={{ width: `${progressPercent}%` }} /></div>
          </div>
          <div className={styles.journey}>
            {journey.levels.map((level) => {
              const cls = level.state === "completed" ? styles.levelDone : (level.state === "active" || level.state === "ready") ? styles.levelCurrent : styles.levelLocked;
              return <div key={level.level_id} className={`${styles.level} ${cls}`} data-level-state={level.state}><small>المستوى {level.level_id} · {level.name}</small><strong>{JOURNEY_STATE_LABEL[level.state]}</strong>{level.state !== "skipped" && <span className={styles.muted}>{level.completed_items} من {level.total_items} أساسي</span>}</div>;
            })}
          </div>
          <p className={styles.muted} style={{ marginTop: 14 }}>{journey.starting_level ? `نقطة البداية المعتمدة: المستوى ${journey.starting_level}. ` : ""}الاختبار البعدي لا يصبح جاهزًا إلا بعد اكتمال رحلة التعلم المعتمدة حتى المستوى الثالث.</p>
        </>}
      </section>
    );

    if (activeTab === "tests") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>الاختبارات التاريخية V1</h2><p>معلومات النسخة القديمة؛ لا تتحكم في بوابة الاختبار البعدي V2.</p></div><ClipboardList size={20} aria-hidden="true" /></div>
        <div className={styles.grid2}>
          <div className={styles.infoCard}><span>الاختبار القبلي</span><strong>جزء من مسار الطالب وتحديد نقطة البداية</strong></div>
          <div className={styles.infoCard}><span>الاختبار البعدي</span><strong>{student.posttest_enabled ? "مفتوح الآن" : student.posttest_eligible ? "جاهز للفتح" : "غير جاهز بعد"}</strong></div>
        </div>
        <div className={styles.notice} style={{ marginTop: 14 }}>{student.posttest_enabled ? "الاختبار البعدي متاح للطالب الآن." : student.posttest_eligible ? "اكتمل المستوى الثالث ويمكن للمشرف فتح الاختبار البعدي." : "لا يمكن فتح الاختبار البعدي قبل إكمال رحلة التعلم حتى المستوى الثالث."}</div>
        <div className={styles.actions} style={{ marginTop: 14 }}><button className={styles.primary} onClick={() => void updatePosttestAccess()} disabled={busy === "posttest" || (!student.posttest_eligible && !student.posttest_enabled)}><Play size={17} aria-hidden="true" />{busy === "posttest" ? "جاري الحفظ..." : student.posttest_enabled ? "إيقاف الإتاحة" : "فتح الاختبار البعدي"}</button></div>
      </section>
    );

    if (activeTab === "recordings") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>التسجيلات الصوتية</h2><p>الوصول إلى مراجعة قراءات هذا الطالب مع الاحتفاظ بسياقه.</p></div><Headphones size={20} aria-hidden="true" /></div>
        <div className={styles.linkCard}><div><strong>مراجعة تسجيلات {student.full_name}</strong><p>تفتح قائمة المراجعة في سياق هذا الطالب بدل الانتقال إلى قائمة عامة غير مفلترة.</p></div><Link href={`/admin/audio-review?student_id=${student.id}`} className={styles.primary}><Headphones size={17} aria-hidden="true" /> فتح مراجعة الصوت</Link></div>
        <p className={styles.muted} style={{ marginTop: 12 }}>بيانات المراجعة تؤخذ من قائمة التسجيلات الفعلية، ولا تُعرض أرقام تقديرية.</p>
      </section>
    );

    if (activeTab === "adaptation") return (
      <section className={styles.panel} data-testid="adaptation-panel">
        <div className={styles.panelHeader}><div><h2>سجل التكيف التاريخي V1</h2><p>آخر قرار محفوظ ضمن نسخة V1 فقط؛ لا يُستعمل لتسكين V2.</p></div><Activity size={20} aria-hidden="true" /></div>
        {historyState === "loading" && <p className={styles.muted}>جاري تحميل قرارات التكيف...</p>}
        {historyState === "error" && sourceError("سجل التكيف", () => void refreshAdaptiveEvidence())}
        {historyState === "loaded" && !latestDecision ? <p className={styles.muted}>لا يوجد قرار تكيف محفوظ بعد.</p> : historyState === "loaded" && latestDecision ? (
          <div className={styles.grid3}>
            <div className={styles.infoCard}><span>آخر قرار</span><strong>{ACTION_LABEL[latestDecision.action] || latestDecision.action}</strong></div>
            <div className={styles.infoCard}><span>الإتقان المتحرك</span><strong>{latestDecision.mastery_score == null ? "—" : `${latestDecision.mastery_score.toFixed(1)}%`}</strong></div>
            <div className={styles.infoCard}><span>المستوى</span><strong>{latestDecision.previous_level} ← {latestDecision.new_level}</strong></div>
          </div>
        ) : null}
        {historyState === "loaded" && latestDecision && <p className={styles.muted} style={{ marginTop: 12 }}>{REASON_LABEL[reasonKey] || reasonKey || "سبب القرار محفوظ ضمن السجل."}</p>}
        <div className={styles.notice} style={{ marginTop: 14 }}>التعديل اليدوي لا يحذف القرار الآلي ولا يعني إكمال المستوى؛ يُحفظ كحدث مستقل مع السبب والتاريخ.</div>
        <div className={styles.grid2} style={{ marginTop: 14 }}>
          <div className={styles.field}><label htmlFor="override-level">المستوى</label><select id="override-level" className={styles.select} value={overrideLevel} onChange={(event) => setOverrideLevel(event.target.value)}><option value="1">المستوى 1</option><option value="2">المستوى 2</option><option value="3">المستوى 3</option></select></div>
          <div className={styles.field}><label htmlFor="override-reason">سبب التعديل</label><input id="override-reason" className={styles.input} value={overrideReason} onChange={(event) => setOverrideReason(event.target.value)} placeholder="اكتب سبب القرار" maxLength={1000} /></div>
        </div>
        <div className={styles.actions} style={{ marginTop: 12 }}><button className={styles.primary} onClick={() => void saveManualOverride()} disabled={busy === "override" || overrideReason.trim().length < 5}><ShieldCheck size={17} aria-hidden="true" />{busy === "override" ? "جاري الحفظ..." : "حفظ القرار اليدوي"}</button></div>
      </section>
    );

    if (activeTab === "account") return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>الحساب والدخول</h2><p>اسم الطالب ورمز الدخول وحالة الحساب.</p></div><LockKeyhole size={20} aria-hidden="true" /></div>
        <div className={styles.formGrid}>
          <div className={styles.field}><label htmlFor="student-name">اسم الطالب</label><input id="student-name" className={styles.input} value={editName} onChange={(event) => setEditName(event.target.value)} minLength={2} maxLength={80} /></div>
          <button className={styles.primary} onClick={() => void saveStudentName()} disabled={busy === "name" || editName.trim() === student.full_name}><Save size={17} aria-hidden="true" />{busy === "name" ? "جاري الحفظ..." : "حفظ الاسم"}</button>
        </div>
        <div className={styles.codeBox} style={{ marginTop: 16 }}><div><span className={styles.muted}>رمز الدخول الحالي</span><strong className={styles.code} dir="ltr">{codeVisible ? student.access_code : "••••••"}</strong></div><button type="button" className={styles.secondary} aria-pressed={codeVisible} onClick={() => setVisibleCodeForId(current => current === id ? null : id)}>{codeVisible ? "إخفاء الرمز" : "إظهار الرمز"}</button><button className={styles.secondary} onClick={() => void copyAccessCode()}>{copied ? <Check size={17} aria-hidden="true" /> : <Copy size={17} aria-hidden="true" />}{copied ? "تم النسخ" : "نسخ الرمز"}</button></div>
        <div className={styles.grid2}>
          <button className={styles.secondary} onClick={() => void changeAccessCode(false)} disabled={busy === "code"}><RefreshCw size={17} aria-hidden="true" /> توليد رمز جديد</button>
          <div className={styles.formGrid}><div className={styles.field}><label htmlFor="manual-code">رمز يدوي من 6 أرقام</label><input id="manual-code" className={styles.input} inputMode="numeric" maxLength={6} value={manualCode} onChange={(event) => setManualCode(event.target.value.replace(/\D/g, "").slice(0,6))} placeholder="123456" dir="ltr" /></div><button className={styles.primary} onClick={() => void changeAccessCode(true)} disabled={busy === "code" || manualCode.length !== 6}>حفظ</button></div>
        </div>
      </section>
    );

    return (
      <section className={styles.panel}>
        <div className={styles.panelHeader}><div><h2>السجل</h2><p>قرارات التكيف والتعديلات المحفوظة زمنيًا.</p></div><History size={20} aria-hidden="true" /></div>
        {historyState === "loading" && <p className={styles.muted}>جاري تحميل السجل...</p>}
        {historyState === "error" && sourceError("سجل القرارات", () => void refreshAdaptiveEvidence())}
        {historyState === "loaded" && history.length === 0 ? <p className={styles.muted}>لا يوجد سجل قرارات حتى الآن.</p> : historyState === "loaded" ? <div className={styles.history}>{[...history].reverse().map((decision) => <div key={decision.decision_id} className={styles.historyItem}><div><strong>{ACTION_LABEL[decision.action] || decision.action}</strong><p className={styles.muted}>{decision.source === "manual" ? "قرار يدوي" : "قرار آلي"}{decision.manual_reason ? ` · ${decision.manual_reason}` : ""}</p></div><small>{new Date(decision.created_at).toLocaleString("ar-SA")}</small></div>)}</div> : null}
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
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><BookOpen size={20} aria-hidden="true" /></span><div><strong>{currentV2Level == null ? "غير معتمد" : `المستوى ${currentV2Level}`}</strong><span>المستوى الحالي V2</span></div></div>
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><Star size={20} aria-hidden="true" /></span><div><strong>{officialPercent == null ? "—" : `${officialPercent}%`}</strong><span>تقدم دروس V2</span></div></div>
        <div className={styles.summaryCard}><span className={styles.summaryIcon}><ClipboardList size={20} aria-hidden="true" /></span><div><strong>{v2Home?.progress.pending_review ?? "—"}</strong><span>مراجعات V2 المعلّقة</span></div></div>
      </section>

      <nav className={styles.tabs} aria-label="أقسام ملف الطالب">
        {TABS.map((tab) => { const Icon = tab.icon; return <button key={tab.key} className={`${styles.tab} ${activeTab === tab.key ? styles.tabActive : ""}`} onClick={() => setActiveTab(tab.key)} aria-current={activeTab === tab.key ? "page" : undefined}><Icon size={16} aria-hidden="true" />{tab.label}</button>; })}
      </nav>

      {tabContent}
    </div>
  );
}
