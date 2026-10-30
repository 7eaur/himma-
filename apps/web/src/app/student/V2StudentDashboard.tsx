"use client";

import { useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BookOpenCheck, CheckCircle2, ClipboardList, LogOut, Sparkles, Star } from "lucide-react";
import V2Rewards, { type V2RewardsData } from "@/components/rewards/V2Rewards";
import StudentRetryTasks from "@/components/learning/StudentRetryTasks";
import styles from "./home.module.css";

export interface StudentV2Home {
  mode: "v2" | "legacy";
  student: { id: number; full_name: string; grade_level: number };
  current_action: {
    action: "assessment" | "start_pretest" | "lesson" | "start_posttest" | "waiting_posttest_enable" | "complete" | "lesson_catalog" | "migration_review" | "placement_review" | "rerecord_required";
    kind?: "pretest" | "posttest" | "lesson" | "assessment";
    task_id?: number;
    session_id?: number;
    state?: string;
    href: string | null;
    label: string;
  };
  journey: {
    current_level: number;
    placement_state: string;
    current_lesson_id: string | null;
    content_release_version: string | null;
  } | null;
  progress: {
    completed_lessons: number;
    assigned_lessons: number | null;
    skipped_by_placement: number;
    pending_review: number;
    display_percent: number | null;
  };
  assessments: {
    pretest: { state: string | null; session_id: number; official: boolean; score_percent: number | null } | null;
    posttest: { state: string | null; session_id: number; official: boolean; score_percent: number | null } | null;
  };
  levels?: { level: number; state: "skipped" | "completed" | "current" | "locked"; assigned_lessons: number; completed_lessons: number; display_percent: number | null }[];
  rewards: V2RewardsData;
  data_status: "ready" | "partial";
}

// The action comes from an API response. Next router.push must never receive
// external schemes or an escaped path even when the response is malformed.
function isSafeStudentRoute(href: unknown): href is string {
  if (typeof href !== "string" || !href.startsWith("/") || href.startsWith("//") ||
      [...href].some(char => char === "\\" || char.charCodeAt(0) <= 32 || char.charCodeAt(0) === 127)) return false;
  try {
    const route = new URL(href, "https://himma.invalid");
    return route.origin === "https://himma.invalid" &&
      (route.pathname === "/student" || route.pathname.startsWith("/student/"));
  } catch {
    return false;
  }
}

const levelNames: Record<number, string> = {
  1: "الحروف والأصوات",
  2: "الحركات والكلمات",
  3: "الجمل والفهم",
};

function stage(home: StudentV2Home) {
  const action = home.current_action;
  if (action.action === "rerecord_required")
    return { title: "لنقرأ مرة أخرى", detail: "طلب المشرف إعادة تسجيل قراءتك. اقرأ النص نفسه، ثم أرسل تسجيلك الجديد.", disabled: false };
  if (action.action === "assessment" && action.state === "placement_pending_review")
    return { title: "نحدد مستواك تلقائيًا", detail: "إجاباتك محفوظة، وستظهر دروسك بعد اكتمال مراجعة القراءة.", disabled: false };
  if (action.action === "assessment" && action.state === "waiting_review")
    return { title: "بانتظار مراجعة القراءة", detail: "تم حفظ إجاباتك، وستكمل رحلتك بعد مراجعة المشرف.", disabled: false };
  if (action.action === "lesson" && action.state === "waiting_review")
    return { title: "درسُك ينتظر المراجعة", detail: "قراءتك محفوظة، ولا تحتاج إلى إعادة الدرس من البداية.", disabled: false };
  if (action.action === "placement_review")
    return { title: "نراجع بيانات رحلتك", detail: "تقدمك محفوظ. لا يمكن فتح الدروس حتى نتأكد من نتيجة الاختبار القبلي؛ اطلب مساعدة المشرف.", disabled: true };
  if (action.action === "migration_review")
    return { title: "رحلتك جاهزة للمراجعة", detail: "تقدمك محفوظ. يراجع المشرف بيانات رحلتك قبل الخطوة التالية.", disabled: true };
  if (action.action === "waiting_posttest_enable")
    return { title: "أنهيت الدروس المطلوبة", detail: "نراجع اكتمال مسارك قبل إتاحة الاختبار البعدي.", disabled: true };
  if (action.action === "complete")
    return { title: "أكملت رحلة هِمّة!", detail: "أنجزت الرحلة والاختبار البعدي. يمكنك مراجعة تقدمك.", disabled: false };
  if (action.action === "start_pretest")
    return { title: "نكتشف نقطة البداية", detail: "اختبار قبلي بسيط يساعدنا على اختيار الدروس المناسبة لك.", disabled: false };
  if (action.action === "start_posttest")
    return { title: "وصلت للاختبار البعدي", detail: "اختبار أخير لمراجعة ما تعلمته، من دون حساب نتيجة قبل اعتمادها.", disabled: false };
  return { title: action.action === "lesson" ? "أكمل درسك من حيث توقفت" : "هيا نكمل تعلّم القراءة", detail: "المقدمة، ثم الشرح والتدريب والاختبار، مع التقوية عند الحاجة.", disabled: false };
}

export default function V2StudentDashboard({ home }: { home: StudentV2Home }) {
  const router = useRouter();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");
  const [logoutState, setLogoutState] = useState<"idle" | "pending" | "failed" | "auth_blocked">("idle");
  const leavingRef = useRef(false);
  const startingRef = useRef(false);
  const logoutRequestRef = useRef(false);
  const name = home.student.full_name.split(" ")[0] || "بطل هِمّة";
  const action = home.current_action;
  const info = stage(home);
  const progress = home.progress;
  const percent = home.data_status === "ready" ? progress.display_percent : null;
  const placed = home.journey && ["placed", "posttest_ready", "completed"].includes(home.journey.placement_state);
  const currentLevel = placed && home.journey ? levelNames[home.journey.current_level] || `المستوى ${home.journey.current_level}` : null;

  const start = async () => {
    if (starting || startingRef.current || info.disabled || leavingRef.current) return;
    setError("");
    if (action.href !== null || (action.action !== "start_pretest" && action.action !== "start_posttest")) {
      if (!isSafeStudentRoute(action.href)) {
        setError("تعذر التحقق من رابط الرحلة. يرجى المحاولة لاحقًا.");
        return;
      }
      startingRef.current = true;
      setStarting(true);
      router.push(action.href);
      return;
    }
    if (action.action !== "start_pretest" && action.action !== "start_posttest") return;
    startingRef.current = true;
    setStarting(true);
    try {
      const kind = action.action === "start_pretest" ? "pretest" : "posttest";
      const response = await fetch(`/api/v2/assessments/${kind}/start`, { method: "POST" });
      // An authorization failure must hide the learner identity immediately.
      // Check before parsing a potentially slow error body, and never override logout.
      if (leavingRef.current) return;
      if (response.status === 401 || response.status === 403) {
        leavingRef.current = true;
        setLogoutState("auth_blocked");
        router.replace("/student/login");
        return;
      }
      const result = await response.json().catch(() => null);
      // A late pretest acknowledgement must not reopen a learner who logged out.
      if (leavingRef.current) return;
      if (!response.ok) {
        const safeMessage = response.status === 409
            ? "لا يمكن بدء اختبار جديد الآن. راجع المشرف للتأكد من جلستك السابقة."
            : response.status === 503
              ? "الاختبار غير متاح حاليًا. يرجى المحاولة لاحقًا."
              : "تعذر فتح الاختبار. تقدّمك محفوظ.";
        throw new Error(safeMessage);
      }
      if (!Number.isSafeInteger(result?.session?.session_id) || result.session.session_id <= 0)
        throw new Error("تعذر التحقق من جلسة الاختبار. حاول مرة أخرى.");
      router.push(`/student/assessment-v2/${result.session.session_id}`);
    } catch (cause) {
      if (leavingRef.current) return;
      startingRef.current = false;
      setError(cause instanceof Error ? cause.message : "تعذر الاتصال بالخادم");
      setStarting(false);
    }
  };

  const logout = async () => {
    // React state may not commit between two rapid taps; guard the request synchronously.
    if (logoutState === "pending" || logoutRequestRef.current) return;
    logoutRequestRef.current = true;
    // Remove the previous student's identity before awaiting the network.
    leavingRef.current = true;
    setLogoutState("pending");
    try {
      const response = await fetch("/api/auth/logout", { method: "POST" });
      if (!response.ok) throw new Error("logout not confirmed");
      router.replace("/");
      router.refresh();
    } catch {
      // Only a failed attempt unlocks explicit retry; identity stays hidden.
      logoutRequestRef.current = false;
      setLogoutState("failed");
    }
  };

  if (logoutState !== "idle") {
    return <main className={styles.page} dir="rtl"><div className={styles.container}>
      {logoutState === "pending" ? <p role="status">جاري تسجيل الخروج...</p> :
        logoutState === "auth_blocked" ? <section>
          <p role="alert">تعذر التحقق من صلاحية الدخول. يرجى تسجيل الدخول من جديد.</p>
          <button type="button" className={styles.button} onClick={() => router.replace("/student/login")}>العودة لتسجيل الدخول</button>
        </section> :
        <section>
          <p role="alert">تعذر تأكيد تسجيل الخروج. أعد المحاولة قبل ترك الجهاز.</p>
          <button type="button" className={styles.button} onClick={() => void logout()}>إعادة محاولة تسجيل الخروج</button>
        </section>}
    </div></main>;
  }

  return <div className={styles.page} dir="rtl" data-testid="student-home" data-learning-version="v2">
    <header className={styles.header}>
      <Image src="/brand/logo-gradient.svg" alt="هِمّة" width={132} height={44} priority />
      <div className={styles.headerTools}><a href="#student-achievements" className={styles.achievementLink} aria-label="عرض إنجازاتي"><Star size={18} aria-hidden="true"/><strong>{home.rewards?.source === "himma_v2_reward_ledger" && home.rewards.state === "ready" ? home.rewards.total_stars : "—"}</strong><span>نجومي</span></a><div className={styles.userChip}>
        <span className={styles.avatar}>{name.charAt(0)}</span>
        <div><strong>{name}</strong><button type="button" className={styles.logout} onClick={() => void logout()}><LogOut size={14} /> خروج</button></div>
      </div></div>
    </header>

    <main className={styles.container}>
      <section className={styles.welcome} data-testid="student-identity">
        <div>
          <span className={styles.eyebrow}><Sparkles size={15} /> رحلة القراءة</span>
          <h1>مرحبًا يا {name}</h1>
          <p>خطوتك التالية واضحة، وهِمّة تحفظ تقدّمك.</p>
          <div className={styles.currentStatus} data-testid="student-status-summary">
            <span>أنت الآن في</span>
            <strong data-testid="student-journey-status">{currentLevel ?? "تحديد نقطة البداية"}</strong>
            <small>{placed ? "الدروس تُفتح حسب تقدمك الحقيقي." : "سنحدد مستواك تلقائيًا بعد الاختبار القبلي ومراجعة القراءة."}</small>
          </div>
        </div>
      </section>

      <section className={styles.hero} data-testid="student-next-action">
        <div className={styles.heroContent}>
          <span className={styles.stepLabel}><BookOpenCheck size={16} /> الخطوة التالية</span>
          <h2>{info.title}</h2>
          <p>{info.detail}</p>
          <div className={styles.meta}>
            <span>{currentLevel ?? "الاختبار القبلي"}</span>
            <span>•</span>
            <span>مهمة واحدة في كل مرة</span>
          </div>
          {action.action !== "complete" && <button type="button" className={styles.button} disabled={starting || info.disabled} aria-busy={starting}
            onClick={() => void start()} data-testid="student-primary-action">
            {starting ? (action.action === "rerecord_required" ? "جارٍ فتح سؤال القراءة..." : action.action === "lesson" ? "جارٍ فتح الدرس..." : action.action === "lesson_catalog" ? "جارٍ فتح الدروس..." : "جارٍ فتح الاختبار...") : action.label}
          </button>}
          {error && <div role="alert" className={styles.error}>{error}</div>}
        </div>
        <div className={styles.heroVisual}>
          <Image src={action.action === "complete" ? "/characters/girl/success.png" : "/characters/girl/explain.png"}
            alt="شخصية هِمّة التعليمية" width={190} height={228} priority />
        </div>
      </section>

      <section className={styles.journey} aria-label="تقدم رحلتك في هِمّة" data-testid="student-v2-progress">
        {placed && home.data_status === "ready" && percent !== null
          ? <>
              <div className={styles.journeyHeader}>
                <div><h3>تقدمك في الدروس</h3><p>أكملت {progress.completed_lessons} من {progress.assigned_lessons} درسًا مخصصًا لك.</p></div>
                <span>{percent}%</span>
              </div>
              <div className={styles.progressTrack} aria-label={`تقدمك ${percent} بالمئة`}>
                <span style={{ width: `${Math.max(0, Math.min(100, percent))}%` }} />
              </div>
            </>
          : <>
              <h3>رحلتك في هِمّة</h3>
              <p className="mt-2 text-sm text-muted">{home.data_status === "partial"
                ? "تعذر عرض تقدمك الآن. بياناتك محفوظة، وراجع المشرف إذا استمرت المشكلة."
                : placed ? "سنظهر تقدمك بعد اكتمال بيانات الدروس."
                : "يظهر تقدم الدروس بعد تحديد مستواك."}</p>
            </>}
      </section>

      <section className={styles.journey} aria-label="مراحل الرحلة">
        <div className={styles.journeyHeader}><div><h3>مراحل رحلة هِمّة</h3><p>اختبار قبلي ← دروس وتمارين وتقوية ← اختبار بعدي</p></div></div>
        <div className={styles.journeySteps} data-testid="student-journey-steps">
          <div data-testid="student-journey-step" className={styles.journeyStep}>
            <ClipboardList size={20} aria-hidden="true" /><strong className={styles.journeyTitle}>الاختبار القبلي</strong>
            <span className={styles.journeyDetail}>{home.assessments.pretest?.official ? "نتيجة معتمدة" : "تحديد المستوى بعد مراجعة القراءة"}</span>
          </div>
          <div data-testid="student-journey-step" className={styles.journeyStep}>
            <BookOpenCheck size={20} aria-hidden="true" /><strong className={styles.journeyTitle}>رحلة الدروس</strong>
            <span className={styles.journeyDetail}>{placed ? currentLevel : "تفتح بعد التسكين"}</span>
          </div>
          <div data-testid="student-journey-step" className={styles.journeyStep}>
            <CheckCircle2 size={20} aria-hidden="true" /><strong className={styles.journeyTitle}>الاختبار البعدي</strong>
            <span className={styles.journeyDetail}>{home.assessments.posttest?.official ? "نتيجة معتمدة" : "بعد إكمال الدروس المطلوبة"}</span>
          </div>
        </div>
      </section>

      {placed && home.levels && home.levels.length > 0 && <section className={styles.journey} aria-label="مستويات رحلتي">
        <div className={styles.journeyHeader}><h3>مستويات رحلتي</h3><Link href="/student/learning-v2">خريطة الدروس</Link></div>
        <ol className={styles.levelList}>{home.levels.map((level) => <li key={level.level} data-level-state={level.state}>
          <span className={styles.levelNumber}>{level.level}</span><div><strong>{levelNames[level.level]}</strong><p>{level.state === "skipped" ? "بدأت من مستوى أعلى" : level.state === "completed" ? "أنجزت دروس المستوى" : level.state === "current" ? "مستواك الحالي" : "خطوة قادمة"}</p>
            {level.state !== "skipped" && <span className={styles.levelCount}>{level.completed_lessons} من {level.assigned_lessons} دروس</span>}
          </div><span className={styles.levelMarker}>{level.state === "completed" ? <CheckCircle2 size={19}/> : level.state === "current" ? "الآن" : ""}</span>
        </li>)}</ol>
      </section>}
      <div id="student-achievements" className={styles.achievements}><V2Rewards data={home.rewards} /></div>
      {action.action !== "rerecord_required" && <StudentRetryTasks dashboard />}
    </main>
  </div>;
}
