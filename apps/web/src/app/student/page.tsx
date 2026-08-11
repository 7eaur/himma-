"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import type { StudentProfile, AssessmentSession } from "../../types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function StudentDashboard() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [activeSession, setActiveSession] = useState<AssessmentSession | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let active = true;
    async function loadData() {
      try {
        const [profileRes, activeRes] = await Promise.all([
          fetch(`${API_URL}/profile`, { credentials: "include" }),
          fetch(`${API_URL}/assessment/active`, { credentials: "include" }),
        ]);

        if (!profileRes.ok) {
          router.push("/student/login");
          return;
        }

        if (active) {
          setProfile(await profileRes.json());
          if (activeRes.ok) {
            const session = await activeRes.json();
            if (session) {
              setActiveSession(session);
            }
          }
        }
      } catch (e) {
        console.error("Failed to load student data", e);
      } finally {
        if (active) setLoading(false);
      }
    }
    loadData();
    return () => { active = false; };
  }, [router]);

  const handleLogout = async () => {
    try {
      await fetch(`${API_URL}/auth/logout`, { method: "POST", credentials: "include" });
      router.push("/student/login");
    } catch {
      // Force redirect anyway
      router.push("/student/login");
    }
  };

  const startPretest = async () => {
    try {
      const res = await fetch(`${API_URL}/assessment/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ session_type: "pretest" }),
      });
      if (res.ok) {
        const session = await res.json();
        router.push(`/student/session/${session.id}`);
      }
    } catch (e) {
      console.error("Failed to start pretest", e);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <h2>جاري التحميل...</h2>
      </div>
    );
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto", textAlign: "center" }}>
      {/* Header */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "3rem" }}>
        <Image src="/brand/logo-navy.svg" alt="هِمّة" width={100} height={50} />
        <button onClick={handleLogout} className="btn" style={{ background: "transparent", color: "var(--error)" }}>
          خروج
        </button>
      </header>

      {profile && (
        <div style={{ background: "white", padding: "3rem", borderRadius: "var(--radius-lg)", boxShadow: "0 4px 20px rgba(0,0,0,0.05)" }}>
          <h1 style={{ color: "var(--primary)", fontSize: "2.5rem", marginBottom: "1rem" }}>
            أهلاً بك يا {profile.full_name.split(' ')[0]}! 👋
          </h1>
          
          <div style={{ margin: "2rem 0", padding: "2rem", background: "var(--bg-light)", borderRadius: "var(--radius-md)" }}>
            <h2 style={{ marginBottom: "1rem" }}>رحلتك التعليمية</h2>
            
            {activeSession ? (
              <div>
                <p style={{ fontSize: "1.2rem", marginBottom: "1.5rem" }}>
                  لديك اختبار قيد التقدم! هل أنت مستعد لإكماله؟
                </p>
                <Link href={`/student/session/${activeSession.id}`} className="btn btn-primary btn-large">
                  متابعة الاختبار
                </Link>
              </div>
            ) : profile.current_level === 1 && profile.grade === 1 ? (
              // Very basic heuristic for new student, in reality we check DB if they finished pretest
              <div>
                <p style={{ fontSize: "1.2rem", marginBottom: "1.5rem" }}>
                  هيا نبدأ رحلتنا باختبار بسيط لنعرف مستواك ونختار لك الأنشطة المناسبة!
                </p>
                <button onClick={startPretest} className="btn btn-primary btn-large">
                  ابدأ اختبار تحديد المستوى
                </button>
              </div>
            ) : (
              <div>
                <p style={{ fontSize: "1.2rem", marginBottom: "1.5rem" }}>
                  أنت الآن في المستوى {profile.current_level}
                </p>
                <Link href="/student/activity/next" className="btn btn-primary btn-large" style={{ backgroundColor: "var(--secondary)" }}>
                  بدء نشاط جديد
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
