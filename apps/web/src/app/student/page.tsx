"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { BookOpenCheck, Check, LogOut, Map, RotateCcw, Star } from "lucide-react";
import styles from "./home.module.css";

interface StudentMe {
  id: number;
  full_name: string;
  grade_level: number;
  current_level: number;
  posttest_enabled: boolean;
  next_action: "resume" | "pretest" | "learning" | "posttest" | "completed";
  active_session: {
    id: number;
    session_type: "pretest" | "posttest" | "core";
    status: "in_progress" | "answering" | "waiting_audio_review" | "rerecord_required" | "ready_to_finalize" | string;
  } | null;
}

interface LearningStatus {
  available: boolean;
  reason?: string;
  level_id: number;
  completed_items: number;
  total_items: number;
  completed: boolean;
  session_id: number | null;
}

interface RewardEvent {
  id: number;
  type: string;
  key?: string | null;
  stars: number | null;
  label: string;
  catalog_version?: string | null;
  asset_id?: string | null;
  asset_slug?: string | null;
  asset_path?: string | null;
}

interface RerecordTask {
  submission_id: number;
  session_id: number;
  attempt_id: number;
  item_id: number;
  step_id: number;
  stable_key: string;
  title: string;
  expected_reading_text?: string | null;
  opened?: boolean;
}

interface JourneyLevel {
  level_id: number;
  name: string;
  state: "locked" | "skipped" | "ready" | "active" | "completed";
  completed_items: number;
  total_items: number;
  session_id: number | null;
}

interface JourneySummary {
  pretest_completed: boolean;
  pretest_score?: number | null;
  starting_level: number | null;
  current_level: number;
  levels: JourneyLevel[];
  learning_journey_completed: boolean;
  posttest_enabled: boolean;
  posttest_completed: boolean;
  posttest_score?: number | null;
  posttest_ready: boolean;
}

type JourneyStepState = "done" | "current" | "upcoming" | "conditional";

const LEVEL_NAMES: Record<number, string> = {
  1: "الاستعداد للقراءة",
  2: "بناء الكلمة",
  3: "الطلاقة والفهم",
};

const LEVEL_STATE_LABELS: Record<JourneyLevel["state"], string> = {
  locked: "لاحقًا",
  skipped: "تجاوزته في الاختبار القبلي",
  ready: "جاهز للبدء",
  active: "أنت هنا",
  completed: "مكتمل",
};

function scoreLabel(score?: number | null) {
  return score == null ? "—" : `${Math.round(score)}%`;
}

export default function StudentHomePage() {
  const router = useRouter();
  const [student, setStudent] = useState<StudentMe | null>(null);
  const [learning, setLearning] = useState<LearningStatus | null>(null);
  const [journey, setJourney] = useState<JourneySummary | null>(null);
  const [rewards, setRewards] = useState<RewardEvent[] | null>(null);
  const [rerecordTasks, setRerecordTasks] = useState<RerecordTask[]>([]);
  const [openingRerecordId, setOpeningRerecordId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const profileResponse = await fetch("/api/profile", { cache: "no-store" });
        const profileData = await profileResponse.json().catch(() => null);
        if (!profileResponse.ok) throw new Error(profileData?.detail || "تعذر تحميل مسارك");
        const profile: StudentMe = profileData;
        setStudent(profile);

        const requests: Promise<void>[] = [];
        if (profile.next_action === "learning" || profile.active_session?.session_type === "core") {
          requests.push(
            fetch("/api/activities/status", { cache: "no-store" }).then(async (response) => {
              if (response.ok) setLearning(await response.json());
            }),
          );
        }
        requests.push(
          fetch("/api/journey", { cache: "no-store" }).then(async (response) => {
            if (response.ok) setJourney(await response.json());
          }),
        );
        requests.push(
          fetch("/api/rewards", { cache: "no-store" })
            .then(async (response) => {
              if (!response.ok) {
                setRewards(null);
                return;
              }
              const rewardData = await response.json().catch(() => null);
              setRewards(Array.isArray(rewardData) ? rewardData : null);
            })
            .catch(() => setRewards(null)),
        );
        if (
          profile.active_session?.session_type === "pretest"
          || profile.active_session?.session_type === "posttest"
        ) {
          requests.push(
            fetch(`/api/assessment/session/${profile.active_session.id}/rerecord-tasks`, { cache: "no-store" })
              .then(async (response) => {
                if (!response.ok) {
                  setRerecordTasks([]);
                  return;
                }
                const taskData = await response.json().catch(() => []);
                setRerecordTasks(Array.isArray(taskData) ? taskData : []);
              })
              .catch(() => setRerecordTasks([])),
          );
        }
        await Promise.all(requests);
      } catch (err) {
        setError(err instanceof Error ? err.message : "تعذر تحميل بياناتك. حدّث الصفحة وحاول مرة أخرى.");
      } finally {
        setLoading(false);
      }
    };
    void fetchData();
  }, []);

  const waitingForAudioReview = student?.active_session?.status === "waiting_audio_review";
  const rerecordRequired = student?.active_session?.status === "rerecord_required";
  const terminalAssessmentHold = waitingForAudioReview || rerecordRequired;

  const handlePrimaryAction = async () => {
    if (!student || terminalAssessmentHold) return;
    setStarting(true);
    setError("");
    try {
      if (student.active_session?.session_type === "pretest" || student.active_session?.session_type === "posttest") {
        router.push(`/student/session/${student.active_session.id}`);
        return;
      }

      const isLearning = student.next_action === "learning" || student.active_session?.session_type === "core";
      if (isLearning) {
        const existingSession = student.active_session?.session_type === "core" ? student.active_session.id : learning?.session_id;
        if (existingSession) {
          router.push(`/student/activity/${existingSession}`);
          return;
        }
        if (learning?.completed) return;
        const response = await fetch("/api/activities/start", { method: "POST" });
        const data = await response.json().catch(() => null);
        if (!response.ok) throw new Error(data?.detail || "تعذر بدء الأنشطة التعليمية");
        router.push(`/student/activity/${data.session_id}`);
        return;
      }

      if (student.next_action === "pretest" || student.next_action === "posttest") {
        const response = await fetch("/api/assessment/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_type: student.next_action }),
        });
        const data = await response.json().catch(() => null);
        if (!response.ok) throw new Error(data?.detail || "تعذر بدء الاختبار");
        router.push(`/student/session/${data.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر الاتصال بالخادم");
      setStarting(false);
    }
  };

  const handleOpenRerecord = async (task: RerecordTask) => {
    if (openingRerecordId !== null) return;
    setOpeningRerecordId(task.submission_id);
    setError("");
    try {
      const response = await fetch(
        `/api/assessment/session/${task.session_id}/attempt/${task.item_id}/step/${task.step_id}/rerecord/start`,
        { method: "POST" },
      );
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "تعذر فتح مهمة إعادة التسجيل");
      router.push(`/student/session/${task.session_id}?task=rerecord`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر فتح مهمة إعادة التسجيل");
      setOpeningRerecordId(null);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      router.replace("/");
      router.refresh();
    }
  };

  const totalStars = useMemo(() => rewards?.reduce((sum, reward) => sum + (Number.isFinite(Number(reward.stars)) ? Number(reward.stars) : 0), 0) ?? 0, [rewards]);
  const earnedBadges = useMemo(() => rewards?.filter((reward) => reward.type === "badge" && Boolean(reward.asset_path)) ?? [], [rewards]);

  if (loading) {
    return (
      <div className={styles.page} dir="rtl">
        <div className="min-h-screen flex flex-col items-center justify-center gap-4">
          <Image src="/brand/logo-gradient.svg" alt="هِمّة" width={130} height={44} priority />
          <div className="spinner w-12 h-12 border-4" />
          <p className="text-muted">جاري تجهيز رحلتك...</p>
        </div>
      </div>
    );
  }

  if (!student) {
    return (
      <div className={styles.page} dir="rtl">
        <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-6 text-center">
          <h1 className="text-2xl font-bold">تعذر فتح حساب الطالب</h1>
          <p className="text-muted">{error || "سجّل الدخول مرة أخرى."}</p>
          <button className={styles.button} onClick={() => router.replace("/student/login")}>العودة إلى الدخول</button>
        </div>
      </div>
    );
  }

  const isLearning = student.next_action === "learning" || student.active_session?.session_type === "core";
  const learningCompleted = Boolean(learning?.completed);
  const learningProgress = learning ? Math.min(100, Math.round((learning.completed_items / Math.max(1, learning.total_items)) * 100)) : 0;
  const firstName = student.full_name.split(" ")[0] || "بطل هِمّة";
  const activeJourneyLevel = journey?.levels.find((level) => level.state === "active" || level.state === "ready")
    ?? journey?.levels.find((level) => level.level_id === student.current_level)
    ?? null;
  const journeyProgress = activeJourneyLevel
    ? Math.min(100, Math.round((activeJourneyLevel.completed_items / Math.max(1, activeJourneyLevel.total_items)) * 100))
    : 0;

  let heroTitle = "الاختبار القبلي";
  let heroDescription = "أسئلة قصيرة ومتنوعة تساعد هِمّة على اختيار البداية المناسبة لك.";
  let primaryLabel = "ابدأ الاختبار";
  let character = "/characters/girl/welcome.png";

  if (student.active_session?.session_type === "pretest") primaryLabel = "متابعة الاختبار";
  if (isLearning) {
    heroTitle = `مستواك: ${LEVEL_NAMES[student.current_level] || `المستوى ${student.current_level}`}`;
    if (learningCompleted && student.current_level < 3) {
      heroDescription = `أكملت ${LEVEL_NAMES[student.current_level]}. خطوتك التالية هي ${LEVEL_NAMES[student.current_level + 1]}.`;
    } else if (learningCompleted) {
      heroDescription = "أكملت المستوى الثالث. بقيت خطوة القياس البعدي عندما تصبح متاحة لك.";
    } else {
      heroDescription = "أنشطة قصيرة بالصوت والصورة والقراءة، وتتدخل التقوية عند الحاجة ثم تعيدك إلى مسارك.";
    }
    primaryLabel = learningCompleted ? "اكتمل هذا المستوى" : (student.active_session?.session_type === "core" || learning?.session_id ? "متابعة الأنشطة" : "ابدأ أنشطة مستواك");
    character = learningCompleted ? "/characters/girl/success.png" : "/characters/girl/explain.png";
  }
  if (student.next_action === "posttest" || student.active_session?.session_type === "posttest") {
    heroTitle = "الاختبار البعدي";
    heroDescription = "خطوتك الأخيرة لقياس التطور الذي حققته خلال رحلة هِمّة.";
    primaryLabel = student.active_session?.session_type === "posttest" ? "متابعة الاختبار" : "ابدأ الاختبار البعدي";
    character = "/characters/girl/encourage.png";
  }
  if (waitingForAudioReview) {
    heroTitle = "بانتظار مراجعة التسجيلات";
    heroDescription = "أنهيت أسئلة الاختبار. نتيجتك محفوظة جزئيًا ولن تعتمد أكاديميًا حتى ينتهي المشرف من مراجعة التسجيلات.";
    primaryLabel = "بانتظار المراجعة";
    character = "/characters/girl/encourage.png";
  }
  if (rerecordRequired) {
    heroTitle = "لديك مهمة إعادة تسجيل";
    heroDescription = "طلب المشرف إعادة إحدى القراءات. ستجد المهمة بشكل مستقل في الصفحة، ويمكنك فتحها عندما تكون مستعدًا.";
    primaryLabel = "افتح مهمة التسجيل أدناه";
    character = "/characters/girl/encourage.png";
  }
  if (student.next_action === "completed") {
    heroTitle = "أكملت رحلتك";
    heroDescription = "أنهيت الاختبارين ومسار التعلم. أحسنت التقدم!";
    primaryLabel = "اكتمل المسار";
    character = "/characters/girl/success.png";
  }

  const primaryDisabled = starting || terminalAssessmentHold || student.next_action === "completed" || (isLearning && learningCompleted);
  const pretestCompleted = Boolean(journey?.pretest_completed);
  const learningJourneyCompleted = Boolean(journey?.learning_journey_completed);
  const posttestCompleted = Boolean(journey?.posttest_completed);
  const posttestCurrent = !posttestCompleted && (student.next_action === "posttest" || student.active_session?.session_type === "posttest" || Boolean(journey?.posttest_ready));
  const coreCurrent = pretestCompleted && !learningJourneyCompleted && !posttestCurrent;
  const currentLevelLabel = pretestCompleted
    ? (LEVEL_NAMES[student.current_level] || `المستوى ${student.current_level}`)
    : "يُحدد بعد الاختبار القبلي";

  let journeyStatusTitle = "الاختبار القبلي";
  let journeyStatusDescription = "نحدد نقطة البداية أولًا، ثم يظهر لك مستوى التعلم المناسب.";
  if (isLearning) {
    journeyStatusTitle = "في مسار التعلم";
    journeyStatusDescription = `تعمل الآن في ${LEVEL_NAMES[student.current_level] || `المستوى ${student.current_level}`}، والتقوية تظهر فقط عند الحاجة.`;
  }
  if (posttestCurrent) {
    journeyStatusTitle = "الاختبار البعدي";
    journeyStatusDescription = "هذه خطوة القياس الأخيرة بعد إكمال رحلة التعلم.";
  }
  if (waitingForAudioReview) {
    journeyStatusTitle = "بانتظار المراجعة البشرية";
    journeyStatusDescription = "إجاباتك محفوظة، واعتماد النتيجة ينتظر مراجعة التسجيلات فقط.";
  }
  if (rerecordRequired) {
    journeyStatusTitle = "إعادة تسجيل مطلوبة";
    journeyStatusDescription = "المهمة مستقلة ولا تنقلك من سؤالك أو نشاطك الحالي تلقائيًا.";
  }
  if (student.next_action === "completed") {
    journeyStatusTitle = "اكتمل المسار";
    journeyStatusDescription = "اكتمل القياس القبلي والتعلم والقياس البعدي.";
  }

  const journeySteps: Array<{ key: string; label: string; sub: string; state: JourneyStepState }> = [
    {
      key: "pretest",
      label: "الاختبار القبلي",
      sub: pretestCompleted ? "مكتمل" : "نحدد نقطة البداية",
      state: pretestCompleted ? "done" : "current",
    },
    {
      key: "level",
      label: "مستوى التعلم",
      sub: pretestCompleted ? currentLevelLabel : "يتحدد بعد القبلي",
      state: pretestCompleted ? "done" : "upcoming",
    },
    {
      key: "core",
      label: "الأنشطة الأساسية",
      sub: learningJourneyCompleted ? "اكتملت" : coreCurrent ? "مسارك الحالي" : "بعد تحديد المستوى",
      state: learningJourneyCompleted ? "done" : coreCurrent ? "current" : "upcoming",
    },
    {
      key: "reinforcement",
      label: "التقوية",
      sub: "تظهر عند الحاجة فقط",
      state: "conditional",
    },
    {
      key: "posttest",
      label: "الاختبار البعدي",
      sub: posttestCompleted ? "مكتمل" : posttestCurrent ? "الخطوة الحالية" : "بعد اكتمال التعلم",
      state: posttestCompleted ? "done" : posttestCurrent ? "current" : "upcoming",
    },
  ];

  return (
    <div className={styles.page} dir="rtl" data-testid="student-home">
      <header className={styles.header}>
        <Image src="/brand/logo-gradient.svg" alt="هِمّة" width={132} height={44} priority />
        <div className={styles.userChip}>
          <div className={styles.avatar}>{firstName.charAt(0)}</div>
          <div><strong>{firstName}</strong><button className={styles.logout} onClick={() => void handleLogout()}><LogOut size={14} /> خروج</button></div>
        </div>
      </header>

      <main className={styles.container}>
        <section className={styles.welcome} data-testid="student-identity">
          <div>
            <span className={styles.eyebrow}><Star size={14} fill="currentColor" /> جاهز للتقدم</span>
            <h1>مرحبًا يا {firstName}</h1>
            <p>خطوتك التالية واضحة أمامك، وهِمّة تحفظ تقدمك تلقائيًا.</p>
            <div className="student-current-status" data-testid="student-status-summary" aria-label="حالتك الحالية">
              <span>أنت الآن في</span>
              <strong data-testid="student-journey-status">{journeyStatusTitle}</strong>
              <small>{journeyStatusDescription}</small>
              {pretestCompleted && <b data-testid="student-current-level">{currentLevelLabel}</b>}
            </div>
          </div>
        </section>

        <section className={`${styles.hero} ${student.next_action === "completed" ? styles.completed : ""}`} data-testid="student-next-action">
          <div className={styles.heroContent}>
            <span className={styles.stepLabel}><BookOpenCheck size={15} /> خطوتك التالية</span>
            <h2>{heroTitle}</h2>
            <p>{heroDescription}</p>
            <div className={styles.meta}>
              {terminalAssessmentHold
                ? <><span>تم حفظ إجاباتك</span><span>•</span><span>{rerecordRequired ? "توجد مهمة تسجيل" : "المراجعة جارية"}</span></>
                : isLearning
                  ? <><span>{learning?.completed_items ?? activeJourneyLevel?.completed_items ?? 0} من {learning?.total_items ?? activeJourneyLevel?.total_items ?? 10} أنشطة</span><span>•</span><span>مهمة واحدة في كل شاشة</span></>
                  : <><span>30 سؤالًا</span><span>•</span><span>يحفظ تلقائيًا</span></>}
            </div>
            <button className={styles.button} onClick={() => void handlePrimaryAction()} disabled={primaryDisabled} data-testid="student-primary-action">
              {starting && <span className="spinner w-5 h-5" />}{primaryLabel}
            </button>
            {error && <div className={styles.error} role="alert">{error}</div>}
          </div>
          <div className={styles.heroVisual}><Image src={character} alt="شخصية هِمّة" width={190} height={228} priority /></div>
        </section>

        {rerecordTasks.length > 0 && (
          <section className="rounded-[28px] border border-border bg-white p-4 sm:p-6 shadow-sm" data-testid="assessment-rerecord-tasks" aria-labelledby="assessment-rerecord-title">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
              <div className="flex items-center gap-3">
                <span className="w-11 h-11 rounded-2xl bg-amber-50 text-amber-700 flex items-center justify-center shrink-0"><RotateCcw size={20} aria-hidden="true" /></span>
                <div>
                  <h2 id="assessment-rerecord-title" className="font-bold text-navy text-lg">إعادة تسجيل مطلوبة</h2>
                  <p className="text-sm text-muted mt-1">هذه مهمة منفصلة عن مسارك. افتحها عندما تكون جاهزًا، ولن تعيدك إلى بداية الاختبار.</p>
                </div>
              </div>
              <span className="text-xs font-semibold rounded-full bg-amber-50 text-amber-800 px-3 py-1.5 self-start">{rerecordTasks.length} {rerecordTasks.length === 1 ? "مهمة" : "مهام"}</span>
            </div>
            <div className="grid gap-3">
              {rerecordTasks.map((task) => (
                <article key={task.submission_id} className="rounded-2xl border border-border bg-bg px-4 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div className="min-w-0">
                    <span className="text-xs text-muted">{task.title || "مهمة قراءة"}</span>
                    <strong className="block mt-1 text-navy text-base">{task.expected_reading_text || "أعد تسجيل القراءة المطلوبة"}</strong>
                  </div>
                  <button
                    type="button"
                    className="btn-primary shrink-0"
                    disabled={openingRerecordId !== null}
                    onClick={() => void handleOpenRerecord(task)}
                  >
                    {openingRerecordId === task.submission_id ? <span className="spinner w-4 h-4" /> : <RotateCcw size={16} aria-hidden="true" />}
                    {task.opened ? "متابعة إعادة التسجيل" : "ابدأ إعادة التسجيل"}
                  </button>
                </article>
              ))}
            </div>
          </section>
        )}

        <section className={styles.journey} aria-label="رحلة الطالب" data-testid="student-journey-overview">
          <div className={styles.journeyHeader}>
            <div>
              <h3>رحلتك في هِمّة</h3>
              <p>خط واحد واضح من القياس القبلي إلى القياس البعدي، والتقوية تدخل فقط عندما تحتاجها.</p>
            </div>
            <span>نبني على مستواك الحقيقي</span>
          </div>
          <div className={styles.steps} data-testid="student-journey-steps">
            {journeySteps.map((entry, index) => (
              <div
                key={entry.key}
                className={`${styles.step} ${entry.state === "done" ? styles.stepDone : ""} ${entry.state === "current" ? styles.stepCurrent : ""}`}
                aria-current={entry.state === "current" ? "step" : undefined}
                data-testid="student-journey-step"
                data-journey-key={entry.key}
                data-journey-state={entry.state}
              >
                <div className={styles.stepIcon}>{entry.state === "done" ? <Check size={20} /> : index + 1}</div>
                <strong>{entry.label}</strong><span>{entry.sub}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="student-progress-overview" data-testid="student-progress-overview" aria-labelledby="student-progress-title">
          <div className="student-progress-heading">
            <div className="student-progress-title">
              <span className={styles.tipIcon}><Map size={21} aria-hidden="true" /></span>
              <div>
                <span>تقدمك</span>
                <h2 id="student-progress-title">{pretestCompleted ? currentLevelLabel : "جاهز لبداية رحلتك"}</h2>
              </div>
            </div>
            <div className="student-progress-score" data-testid="student-level-progress-summary" aria-label="تقدم المستوى الحالي">
              <strong>{isLearning || activeJourneyLevel ? `${isLearning ? learningProgress : journeyProgress}%` : "—"}</strong>
              <span>{pretestCompleted ? "من المستوى" : "بعد الاختبار القبلي"}</span>
            </div>
          </div>

          <div className="student-progress-track" aria-hidden="true">
            <span style={{ width: `${isLearning || activeJourneyLevel ? (isLearning ? learningProgress : journeyProgress) : 0}%` }} />
          </div>

          <div className="student-progress-facts">
            <div role={rewards === null ? "status" : undefined} aria-label={rewards === null ? "تعذر تحميل النجوم" : `لديك ${totalStars} نجمة`}>
              <span>النجوم</span>
              <strong>{rewards === null ? "—" : totalStars}</strong>
            </div>
            <div>
              <span>الشارات</span>
              <strong>{rewards === null ? "—" : earnedBadges.length}</strong>
            </div>
            <div>
              <span>المسار</span>
              <strong>{pretestCompleted ? currentLevelLabel : "قبل تحديد المستوى"}</strong>
            </div>
          </div>

          {earnedBadges.length > 0 && (
            <div className="student-earned-badges" data-testid="student-badges" aria-label={`لديك ${earnedBadges.length} شارة`}>
              {earnedBadges.slice(0, 3).map((badge) => (
                <article key={badge.id} data-reward-key={badge.key || undefined}>
                  <Image src={badge.asset_path!} alt={`شارة ${badge.label}`} width={64} height={64} />
                  <span>{badge.label}</span>
                </article>
              ))}
            </div>
          )}

          {earnedBadges.length === 0 && (
            <div
              className="student-progress-hint"
              data-testid="student-badges"
              role={rewards === null ? "status" : undefined}
              aria-label={rewards === null ? "تعذر تحميل الشارات" : "لا توجد شارات مكتسبة"}
            >
              <strong>{rewards === null ? "الشارات غير متاحة الآن" : "لم تحصل على شارة بعد"}</strong>
              <span>{rewards === null ? "تقدمك محفوظ. حاول تحديث الصفحة لاحقًا لعرض شاراتك." : "أكمل خطوات رحلتك وستظهر شاراتك هنا."}</span>
            </div>
          )}
        </section>

        {journey?.pretest_completed && (
          <details className="student-secondary-details" data-testid="level-journey">
            <summary>تفاصيل مستويات رحلتك</summary>
            <p className="student-secondary-note">{journey.starting_level ? `بدأت من المستوى ${journey.starting_level}` : "مسارك التعليمي"}</p>
            <div className={styles.levelCards}>
              {journey.levels.map((level) => {
                const levelPercent = Math.min(100, Math.round((level.completed_items / Math.max(1, level.total_items)) * 100));
                return (
                  <article key={level.level_id} className={`${styles.levelCard} ${styles[`levelState${level.state.charAt(0).toUpperCase()}${level.state.slice(1)}`]}`} data-level-state={level.state}>
                    <div className={styles.levelTopline}>
                      <div className={styles.levelNumber}>{level.state === "completed" ? <Check size={20} /> : level.level_id}</div>
                      <span>{LEVEL_STATE_LABELS[level.state]}</span>
                    </div>
                    <h4>{level.name}</h4>
                    {level.state === "skipped" ? (
                      <p>نتيجة الاختبار القبلي وضعتك في مستوى أعلى، لذلك لا تحتاج لإعادة هذا المستوى.</p>
                    ) : (
                      <>
                        <div className={styles.levelProgressTrack} aria-label={`تقدم المستوى ${level.level_id}: ${level.completed_items} من ${level.total_items}`}>
                          <span style={{ width: `${level.state === "completed" ? 100 : levelPercent}%` }} />
                        </div>
                        <p>{level.state === "locked" ? "يفتح بعد إكمال المستوى السابق." : `${level.completed_items} من ${level.total_items} أنشطة أساسية`}</p>
                      </>
                    )}
                  </article>
                );
              })}
            </div>
          </details>
        )}

        {(journey?.pretest_completed || journey?.posttest_completed) && (
          <details className="student-secondary-details" data-testid="student-results">
            <summary>عرض النتائج والسجل</summary>
            <div className="student-results-grid">
              <article className="student-result-card">
                <span>الاختبار القبلي</span>
                <strong>{journey?.pretest_completed ? scoreLabel(journey.pretest_score) : "لم يكتمل"}</strong>
                <small>{journey?.pretest_completed && journey.starting_level ? `نقطة البداية: المستوى ${journey.starting_level}` : "تظهر النتيجة بعد الاعتماد"}</small>
              </article>
              <article className="student-result-card student-result-card-current">
                <span>المستوى الحالي</span>
                <strong>{currentLevelLabel}</strong>
                <small>{activeJourneyLevel ? `${activeJourneyLevel.completed_items} من ${activeJourneyLevel.total_items} أنشطة أساسية · ${journeyProgress}%` : "بانتظار بدء أنشطة المستوى"}</small>
              </article>
              <article className="student-result-card">
                <span>الاختبار البعدي</span>
                <strong>{journey?.posttest_completed ? scoreLabel(journey.posttest_score) : journey?.posttest_ready ? "جاهز" : "لاحقًا"}</strong>
                <small>{journey?.posttest_completed ? "نتيجة معتمدة" : journey?.posttest_ready ? "يمكن بدء القياس البعدي" : "يفتح بعد اكتمال رحلة التعلم"}</small>
              </article>
            </div>
          </details>
        )}
      </main>
    </div>
  );
}
