"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { BookOpen, CheckCircle2, LogOut } from "lucide-react";
import pathStyles from "./studentPath.module.css";

interface StudentMe {
  id: number;
  full_name: string;
  grade_level: number;
  current_level: number;
  posttest_enabled: boolean;
  next_action: "resume" | "pretest" | "learning" | "posttest" | "completed";
  active_session: { id: number; session_type: "pretest" | "posttest" | "core" } | null;
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

const LEVEL_NAMES: Record<number, string> = {
  1: "الاستعداد للقراءة",
  2: "بناء الكلمة",
  3: "الطلاقة والفهم",
};

export default function StudentHomePage() {
  const router = useRouter();
  const [student, setStudent] = useState<StudentMe | null>(null);
  const [learning, setLearning] = useState<LearningStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const profileRes = await fetch("/api/profile");
        if (!profileRes.ok) throw new Error("تعذر تحميل مسار الطالب");
        const profile: StudentMe = await profileRes.json();
        setStudent(profile);

        if (profile.next_action === "learning" || profile.active_session?.session_type === "core") {
          const learningRes = await fetch("/api/activities/status");
          if (learningRes.ok) setLearning(await learningRes.json());
        }
      } catch (err) {
        console.error("Error fetching student path", err);
        setError("تعذر تحميل بياناتك. يرجى تحديث الصفحة.");
      } finally {
        setLoading(false);
      }
    };
    void fetchData();
  }, []);

  const handlePrimaryAction = async () => {
    if (!student) return;
    setStarting(true);
    setError("");

    try {
      if (student.active_session?.session_type === "pretest" || student.active_session?.session_type === "posttest") {
        router.push(`/student/session/${student.active_session.id}`);
        return;
      }

      if (student.next_action === "learning" || student.active_session?.session_type === "core") {
        const existingSession = student.active_session?.session_type === "core"
          ? student.active_session.id
          : learning?.session_id;
        if (existingSession) {
          router.push(`/student/activity/${existingSession}`);
          return;
        }
        if (learning?.completed) {
          setStarting(false);
          return;
        }
        const res = await fetch("/api/activities/start", { method: "POST" });
        const data = await res.json().catch(() => null);
        if (!res.ok) throw new Error(data?.detail || "تعذر بدء الأنشطة التعليمية");
        router.push(`/student/activity/${data.session_id}`);
        return;
      }

      if (student.next_action === "pretest" || student.next_action === "posttest") {
        const res = await fetch("/api/assessment/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_type: student.next_action }),
        });
        const data = await res.json().catch(() => null);
        if (!res.ok) throw new Error(data?.detail || "تعذر بدء الاختبار");
        router.push(`/student/session/${data.id}`);
        return;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر الاتصال بالخادم");
      setStarting(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      router.replace("/");
      router.refresh();
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  if (loading) {
    return (
      <div className="student-home-root">
        <div className="flex-1 flex items-center justify-center">
          <div className="spinner w-12 h-12 border-4" />
        </div>
      </div>
    );
  }

  const isLearning = student?.next_action === "learning" || student?.active_session?.session_type === "core";
  const learningCompleted = Boolean(learning?.completed);
  const learningProgress = learning
    ? Math.min(100, Math.round((learning.completed_items / Math.max(1, learning.total_items)) * 100))
    : 0;

  let primaryLabel = "ابدأ الاختبار القبلي";
  const primaryDisabled = starting || student?.next_action === "completed" || (isLearning && learningCompleted);
  if (starting) primaryLabel = "جاري التجهيز...";
  else if (student?.active_session?.session_type === "pretest" || student?.active_session?.session_type === "posttest") primaryLabel = "استئناف الاختبار";
  else if (isLearning && (student?.active_session?.session_type === "core" || learning?.session_id)) primaryLabel = "متابعة الأنشطة";
  else if (isLearning && !learningCompleted) primaryLabel = "ابدأ أنشطة مستواك";
  else if (student?.next_action === "posttest") primaryLabel = "ابدأ الاختبار البعدي";
  else if (student?.next_action === "completed") primaryLabel = "اكتمل المسار";
  else if (learningCompleted) primaryLabel = "أكملت أنشطة مستواك";

  return (
    <div className="student-home-root" dir="rtl">
      <div className="student-login-amb-1" />
      <div className="student-login-amb-2" />

      <header className="student-home-header">
        <Image src="/brand/logo-gradient.svg" alt="هِمّة" width={140} height={45} priority />
        <button onClick={handleLogout} className="student-logout-btn">
          <LogOut size={16} />
          <span>خروج</span>
        </button>
      </header>

      <main className="student-home-main">
        <Image
          src={learningCompleted ? "/characters/boy/success.png" : "/characters/boy/welcome.png"}
          alt="شخصية هِمّة"
          width={220}
          height={280}
          className="student-home-char"
          priority
        />

        <h1 className="student-greeting">
          أهلاً بك يا بطل، {student?.full_name?.split(" ")[0] || "يا بطل"}!
        </h1>
        {student?.grade_level && <div className="student-grade-badge">الصف {student.grade_level}</div>}

        {isLearning && student && (
          <section className={pathStyles.learningCard} aria-label="تقدم الأنشطة التعليمية">
            <div className={pathStyles.learningTitle}>
              <BookOpen size={21} aria-hidden="true" />
              <span>مستواك: {LEVEL_NAMES[student.current_level] || `المستوى ${student.current_level}`}</span>
            </div>
            <div className={pathStyles.progressRow}>
              <span>{learning?.completed_items ?? 0} من {learning?.total_items ?? 10}</span>
              <span>{learningProgress}%</span>
            </div>
            <div className={pathStyles.progressTrack} aria-hidden="true">
              <span className={pathStyles.progressFill} style={{ width: `${learningProgress}%` }} />
            </div>
            <p className={pathStyles.learningNote}>
              {learningCompleted
                ? "أحسنت، أكملت أنشطة مستواك. سيظهر الاختبار البعدي عندما تفتحه الباحثة."
                : "أمامك عشرة أنشطة قصيرة. كل شاشة فيها مهمة واحدة واضحة."}
            </p>
            {learningCompleted && <CheckCircle2 size={26} className={pathStyles.learningCheck} aria-hidden="true" />}
          </section>
        )}

        <p className="student-subtitle">
          {student?.next_action === "completed"
            ? "أكملت الاختبارين القبلي والبعدي. أحسنت التقدم."
            : student?.next_action === "posttest"
              ? "أصبح الاختبار البعدي متاحًا لك."
              : isLearning
                ? "هيا نكمل خطوة جديدة في رحلة التعلّم."
                : "هل أنت مستعد لنبدأ رحلة التعلّم والتطور؟"}
        </p>

        {error && <p className="alert-error">{error}</p>}

        <button onClick={handlePrimaryAction} disabled={primaryDisabled} className="student-start-btn">
          {starting && <span className="spinner border-4 w-6 h-6" />}
          <span>{primaryLabel}</span>
        </button>
      </main>
    </div>
  );
}
