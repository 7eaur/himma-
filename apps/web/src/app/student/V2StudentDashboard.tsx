"use client";

import { useRef, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { BookOpenCheck, CheckCircle2, ClipboardList, LogOut, Sparkles } from "lucide-react";
import StudentRetryTasks from "@/components/learning/StudentRetryTasks";
import styles from "./home.module.css";

export interface StudentV2Home {
  mode: "v2" | "legacy";
  test_only: boolean;
  student: { id: number; full_name: string; grade_level: number };
  current_action: {
    action: "assessment" | "start_pretest" | "lesson" | "start_posttest" | "waiting_posttest_enable" | "complete" | "lesson_catalog" | "migration_review";
    kind?: "pretest" | "posttest";
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
  rewards: { state: "not_implemented_v2" };
  data_status: "ready" | "partial";
}

const levelNames: Record<number, string> = {
  1: "الحروف والأصوات",
  2: "الحركات والكلمات",
  3: "الجمل والفهم",
};

function stage(home: StudentV2Home) {
  const action = home.current_action;
  if (action.action === "assessment" && action.state === "placement_pending_review")
    return { title: "بانتظار تحديد مستواك", detail: "إجاباتك محفوظة، والمشرف يراجع التسكين قبل بدء الدروس.", disabled: false };
  if (action.action === "assessment" && action.state === "waiting_review")
    return { title: "بانتظار مراجعة القراءة", detail: "تم حفظ إجاباتك، وستكمل رحلتك بعد مراجعة المشرف.", disabled: false };
  if (action.action === "lesson" && action.state === "waiting_review")
    return { title: "درسُك ينتظر المراجعة", detail: "قراءتك محفوظة، ولا تحتاج إلى إعادة الدرس من البداية.", disabled: false };
  if (action.action === "migration_review")
    return { title: "رحلتك تحتاج مراجعة المشرف", detail: "نحتفظ بتعلّمك السابق. سيراجع المشرف انتقالك إلى هِمّة الجديدة دون تكرار اختبارك أو فقدان سجلك.", disabled: true };
  if (action.action === "waiting_posttest_enable")
    return { title: "أنهيت الدروس المطلوبة", detail: "بانتظار إتاحة الاختبار البعدي من المشرف.", disabled: true };
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
    if (action.href) { router.push(action.href); return; }
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
      <div className={styles.userChip}>
        <span className={styles.avatar}>{name.charAt(0)}</span>
        <div><strong>{name}</strong><button type="button" className={styles.logout} onClick={() => void logout()}><LogOut size={14} /> خروج</button></div>
      </div>
    </header>

    <main className={styles.container}>
      <section className={styles.welcome} data-testid="student-identity">
        <div>
          <span className={styles.eyebrow}><Sparkles size={15} /> رحلة القراءة</span>
          <h1>مرحبًا يا {name}</h1>
          <p>خطوتك التالية واضحة، وهِمّة تحفظ تقدّمك.</p>
          <div className="student-current-status" data-testid="student-status-summary">
            <span>أنت الآن في</span>
            <strong data-testid="student-journey-status">{currentLevel ?? "تحديد نقطة البداية"}</strong>
            <small>{placed ? "الدروس تُفتح حسب تقدمك الحقيقي." : "سنحدد مستواك بعد الاختبار القبلي ومراجعة المشرف."}</small>
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
          <button type="button" className={styles.button} disabled={starting || info.disabled}
            onClick={() => void start()} data-testid="student-primary-action">
            {starting ? "جاري فتح الاختبار..." : action.label}
          </button>
          {error && <div role="alert" className={styles.error}>{error}</div>}
        </div>
        <div className={styles.heroVisual}>
          <Image src={action.action === "complete" ? "/characters/girl/success.png" : "/characters/girl/explain.png"}
            alt="شخصية هِمّة التعليمية" width={190} height={228} priority />
        </div>
      </section>

      <section className={styles.journey} aria-label="تقدم رحلتك في هِمّة V2" data-testid="student-v2-progress">
        <div className={styles.journeyHeader}>
          <div><h3>تقدمك في الدروس</h3>
            <p>{home.data_status === "partial" ? "تعذر حساب التقدم من إصدار المحتوى المثبت؛ بياناتك محفوظة." :
              percent === null ? "يظهر تقدم الدروس بعد اعتماد التسكين." :
              `أكملت ${progress.completed_lessons} من ${progress.assigned_lessons} درسًا مخصصًا لك.`}</p>
          </div>
          <span>{percent === null ? "لم يُحسب بعد" : `${percent}%`}</span>
        </div>
        {percent !== null && <div className="student-progress-track" aria-label={`تقدمك ${percent} بالمئة`}>
          <span style={{ width: `${Math.max(0, Math.min(100, percent))}%` }} />
        </div>}
        <div className="student-progress-facts">
          <div><span>دروس أُنجزت</span><strong>{home.data_status === "partial" || !placed ? "—" : progress.completed_lessons}</strong></div>
          <div><span>تجاوزتها بالتسكين</span><strong>{home.data_status === "partial" || !placed ? "—" : progress.skipped_by_placement}</strong></div>
          <div><span>بانتظار المراجعة</span><strong>{progress.pending_review}</strong></div>
        </div>
        <p className="mt-4 text-sm text-muted">الدروس المتجاوزة بالتسكين لا تُحسب دروسًا منجزة، ولا نعرض نجومًا قبل اعتماد نظام مكافآت V2.</p>
      </section>

      <section className={styles.journey} aria-label="مراحل الرحلة">
        <div className={styles.journeyHeader}><div><h3>مراحل رحلة هِمّة</h3><p>اختبار قبلي ← دروس وتمارين وتقوية ← اختبار بعدي</p></div></div>
        <div className="grid gap-3 sm:grid-cols-3" data-testid="student-journey-steps">
          <div data-testid="student-journey-step" className="rounded-2xl border border-slate-200 p-4">
            <ClipboardList size={20} aria-hidden="true" /><strong className="block mt-2">الاختبار القبلي</strong>
            <span className="block text-sm text-muted mt-1">{home.assessments.pretest?.official ? "نتيجة معتمدة" : "تحديد المستوى ومراجعته"}</span>
          </div>
          <div data-testid="student-journey-step" className="rounded-2xl border border-slate-200 p-4">
            <BookOpenCheck size={20} aria-hidden="true" /><strong className="block mt-2">رحلة الدروس</strong>
            <span className="block text-sm text-muted mt-1">{placed ? currentLevel : "تفتح بعد التسكين"}</span>
          </div>
          <div data-testid="student-journey-step" className="rounded-2xl border border-slate-200 p-4">
            <CheckCircle2 size={20} aria-hidden="true" /><strong className="block mt-2">الاختبار البعدي</strong>
            <span className="block text-sm text-muted mt-1">{home.assessments.posttest?.official ? "نتيجة معتمدة" : "بعد إكمال الرحلة وإتاحته"}</span>
          </div>
        </div>
      </section>

      <StudentRetryTasks dashboard />
      {home.test_only && <p className="mt-4 text-xs text-muted">معاينة V2 مرحلية · TEST ONLY — لم تعتمد جميع الوسائط التعليمية للنشر النهائي.</p>}
    </main>
  </div>;
}
