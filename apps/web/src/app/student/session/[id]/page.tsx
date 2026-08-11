"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import type { AssessmentSession } from "../../../../types/api";
import { AssessmentRunner } from "../../../../components/AssessmentRunner";
import styles from "../../student.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type StudentProfile = {
  id: number;
  full_name: string;
  grade: number;
  access_code: string;
};

export default function StudentPage() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [activeSession, setActiveSession] = useState<AssessmentSession | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [profileRes, sessionRes] = await Promise.all([
          fetch(`${API_URL}/profile`, { credentials: "include" }),
          fetch(`${API_URL}/assessment/active`, { credentials: "include" }),
        ]);

        if (!profileRes.ok) {
          router.push("/login?role=student");
          return;
        }

        if (!active) return;
        const profileData: StudentProfile = await profileRes.json();
        setProfile(profileData);

        if (sessionRes.ok) {
          const sessionData: AssessmentSession | null = await sessionRes.json();
          if (active) setActiveSession(sessionData);
        }
      } catch {
        if (active) setError("تعذّر الاتصال بالخادم");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, [router]);

  const startPretest = async () => {
    setError(null);
    try {
      const res = await fetch(`${API_URL}/assessment/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ session_type: "pretest" }),
      });
      if (!res.ok) throw new Error("Failed to start");
      const data: AssessmentSession = await res.json();
      setActiveSession(data);
    } catch {
      setError("تعذّر بدء الاختبار. حاول مرة أخرى.");
    }
  };

  const handleComplete = async () => {
    if (!activeSession) return;
    try {
      await fetch(`${API_URL}/assessment/session/${activeSession.id}/finish`, {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        credentials: "include",
      });
    } finally {
      setActiveSession(null);
      setCompleted(true);
    }
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <div className="spinner" />
      </div>
    );
  }

  if (completed) {
    return (
      <div className={styles.page}>
        <div className={styles.completedCard}>
          <Image src="/characters/boy-success.png" alt="أحسنت!" width={200} height={200} />
          <h2 className={styles.completedTitle}>أحسنت! انتهيت من الاختبار 🎉</h2>
          <p className={styles.completedSub}>سيقيّم المعلم نتيجتك قريباً</p>
          <button
            className="btn btn-primary btn-child"
            onClick={() => setCompleted(false)}
          >
            العودة للبداية
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <Image src="/brand/logo-gradient.svg" alt="هِمّة" width={100} height={50} />
        {profile && (
          <div className={styles.studentInfo}>
            <span className={styles.studentName}>{profile.full_name}</span>
            <span className={styles.studentGrade}>الصف {profile.grade}</span>
          </div>
        )}
      </header>

      {/* Main content */}
      <main className={styles.main}>
        {error && <div className="alert alert-error">{error}</div>}

        {!activeSession ? (
          <div className={styles.welcomeSection}>
            <Image
              src="/characters/boy-welcome.png"
              alt="أهلاً وسهلاً"
              width={220}
              height={220}
              className="character"
            />
            <h1 className={`${styles.welcomeTitle} font-child`}>
              أهلاً {profile?.full_name ?? "بك"}! 👋
            </h1>
            <p className={styles.welcomeText}>
              هل أنت مستعد لبدء اختبار القراءة؟
            </p>
            <button
              className="btn btn-primary btn-child"
              onClick={startPretest}
              data-testid="btn-start-assessment"
            >
              ابدأ الاختبار 🚀
            </button>
          </div>
        ) : (
          <div className={styles.assessmentWrap}>
            <AssessmentRunner
              sessionId={activeSession.id}
              onComplete={handleComplete}
            />
          </div>
        )}
      </main>
    </div>
  );
}
