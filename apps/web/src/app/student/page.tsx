"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

interface StudentMe {
  id: string;
  full_name: string;
  grade_level: number;
}

export default function StudentHomePage() {
  const router = useRouter();
  const [student, setStudent] = useState<StudentMe | null>(null);
  const [loading, setLoading] = useState(true);
  const [startingSession, setStartingSession] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [meRes, activeRes] = await Promise.all([
          fetch("/api/me"),
          fetch("/api/assessment/active")
        ]);
        if (meRes.ok) {
          setStudent(await meRes.json());
        }
        if (activeRes.ok) {
          const activeSession = await activeRes.json();
          if (activeSession && activeSession.id) {
            setActiveSessionId(activeSession.id);
          }
        }
      } catch (err) {
        console.error("Error fetching student info or active session", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleStartAssessment = async () => {
    if (activeSessionId) {
      router.push(`/student/session/${activeSessionId}`);
      return;
    }
    
    setStartingSession(true);
    try {
      const res = await fetch("/api/assessment/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_type: "pretest" })
      });
      if (res.ok) {
        const session = await res.json();
        router.push(`/student/session/${session.id}`);
      }
    } catch (err) {
      console.error("Error starting assessment", err);
      setStartingSession(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      window.location.href = "/";
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
          هل أنت مستعد لنبدأ رحلة التعلم والتطور معاً؟
        </p>
        
        <button
          onClick={handleStartAssessment}
          disabled={startingSession}
          className="student-start-btn"
        >
          {startingSession ? (
            <span className="flex items-center justify-center gap-3">
              <span className="spinner border-4 w-6 h-6"></span>
              <span>جاري التجهيز...</span>
            </span>
          ) : activeSessionId ? (
            "استئناف الاختبار"
          ) : (
            "ابدأ الاختبار"
          )}
        </button>
      </main>
    </div>
  );
}
