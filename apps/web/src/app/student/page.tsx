"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

interface StudentMe {
  id: number;
  full_name: string;
  grade_level: number;
  next_action: "resume" | "pretest" | "learning" | "posttest" | "completed";
  active_session: { id: number; session_type: "pretest" | "posttest" } | null;
}

export default function StudentHomePage() {
  const router = useRouter();
  const [student, setStudent] = useState<StudentMe | null>(null);
  const [loading, setLoading] = useState(true);
  const [startingSession, setStartingSession] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const profileRes = await fetch("/api/profile");
        if (!profileRes.ok) throw new Error("تعذر تحميل مسار الطالب");
        setStudent(await profileRes.json());
      } catch (err) {
        console.error("Error fetching student info or active session", err);
        setError("تعذر تحميل بياناتك. يرجى تحديث الصفحة.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleStartAssessment = async () => {
    if (!student) return;
    if (student.active_session) {
      router.push(`/student/session/${student.active_session.id}`);
      return;
    }
    if (student.next_action !== "pretest" && student.next_action !== "posttest") return;
    
    setStartingSession(true);
    setError("");
    try {
      const res = await fetch("/api/assessment/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_type: student.next_action })
      });
      if (res.ok) {
        const session = await res.json();
        router.push(`/student/session/${session.id}`);
      } else {
        const data = await res.json().catch(() => null);
        setError(data?.detail || "تعذر بدء الاختبار");
        setStartingSession(false);
      }
    } catch (err) {
      console.error("Error starting assessment", err);
      setError("تعذر الاتصال بالخادم");
      setStartingSession(false);
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
          <div className="spinner w-12 h-12 border-4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="student-home-root" dir="rtl">
      <div className="student-login-amb-1" />
      <div className="student-login-amb-2" />

      <header className="student-home-header">
        <Image src="/brand/logo-gradient.svg" alt="Himma Logo" width={140} height={45} />
        <button onClick={handleLogout} className="student-logout-btn">
          <LogOut size={16} />
          <span>خروج</span>
        </button>
      </header>

      <main className="student-home-main">
        <Image 
          src="/characters/boy/welcome.png" 
          alt="Welcome" 
          width={220} 
          height={280}
          className="student-home-char" 
          priority
        />
        
        <h1 className="student-greeting">
          أهلاً بك يا بطل، {student?.full_name?.split(' ')[0] || "طالب"}!
        </h1>
        {student?.grade_level && (
          <div className="student-grade-badge">الصف {student.grade_level}</div>
        )}
        <p className="student-subtitle">
          {student?.next_action === "learning"
            ? "أكملت الاختبار القبلي. ستظهر أنشطة مستواك في المرحلة التعليمية التالية."
            : student?.next_action === "completed"
              ? "أكملت الاختبارين القبلي والبعدي بنجاح."
              : student?.next_action === "posttest"
                ? "أصبح الاختبار البعدي متاحًا لك."
                : "هل أنت مستعد لنبدأ رحلة التعلم والتطور معاً؟"}
        </p>
        {error && <p className="alert-error">{error}</p>}
        
        <button
          onClick={handleStartAssessment}
          disabled={startingSession || student?.next_action === "learning" || student?.next_action === "completed"}
          className="student-start-btn"
        >
          {startingSession ? (
            <span className="flex items-center justify-center gap-3">
              <span className="spinner border-4 w-6 h-6"></span>
              <span>جاري التجهيز...</span>
            </span>
          ) : student?.next_action === "resume" ? (
            "استئناف الاختبار"
          ) : student?.next_action === "posttest" ? (
            "ابدأ الاختبار البعدي"
          ) : student?.next_action === "learning" ? (
            "بانتظار الأنشطة التعليمية"
          ) : student?.next_action === "completed" ? (
            "اكتمل المسار"
          ) : (
            "ابدأ الاختبار القبلي"
          )}
        </button>
      </main>
    </div>
  );
}
