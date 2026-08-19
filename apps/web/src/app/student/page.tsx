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

interface ActiveSession {
  id: string;
  status: string;
}

export default function StudentHomePage() {
  const router = useRouter();
  const [student, setStudent] = useState<StudentMe | null>(null);
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [startingSession, setStartingSession] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const meRes = await fetch("/api/me");
        if (meRes.ok) {
          setStudent(await meRes.json());
        }

        // Ideally fetch active session, but for now we'll just check if one exists via a try/catch or endpoint
        // Let's assume there's an endpoint to get the active session, or we just always create a new one for now if none.
        // For simplicity, we'll let the start assessment button handle it.
      } catch (err) {
        console.error("Error fetching student info", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  const handleStartAssessment = async () => {
    setStartingSession(true);
    try {
      const res = await fetch("/api/assessment/start", {
        method: "POST"
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
      window.location.href = "/student/login";
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center font-tajawal">
        <div className="spinner w-12 h-12 border-4"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg flex flex-col font-tajawal relative overflow-hidden">
      {/* Decorative background */}
      <div className="absolute top-[-10%] right-[-5%] w-64 h-64 bg-yellow/20 rounded-full blur-3xl -z-10"></div>
      <div className="absolute bottom-[-10%] left-[-5%] w-80 h-80 bg-primary/20 rounded-full blur-3xl -z-10"></div>

      <header className="p-6 flex justify-between items-center bg-white/50 backdrop-blur-sm border-b border-white">
        <Image src="/brand/logo-gradient.svg" alt="Himma Logo" width={140} height={45} />
        <button 
          onClick={handleLogout}
          className="flex items-center gap-2 text-muted hover:text-red-500 bg-white px-4 py-2 rounded-full shadow-sm font-bold transition-colors"
        >
          <LogOut size={20} />
          <span>خروج</span>
        </button>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto w-full">
        <Image 
          // Using boy-welcome as default, in a real app we'd use gender from profile if available
          src="/characters/boy-welcome.png" 
          alt="Welcome" 
          width={220} 
          height={280}
          className="mb-8 drop-shadow-lg" 
        />
        
        <h1 className="text-4xl font-bold text-navy mb-4">
          أهلاً بك يا بطل، {student?.full_name?.split(' ')[0] || "طالب"}!
        </h1>
        <p className="text-xl text-muted mb-12 max-w-md">
          هل أنت مستعد لنبدأ رحلة التعلم والتطور معاً؟
        </p>
        
        <button
          onClick={handleStartAssessment}
          disabled={startingSession}
          className="w-full sm:w-auto px-16 py-6 bg-primary hover:bg-[#276bb8] text-white font-bold text-2xl rounded-full shadow-xl transition-transform hover:-translate-y-2 active:translate-y-0 min-h-[64px]"
        >
          {startingSession ? (
            <span className="flex items-center justify-center gap-3">
              <span className="spinner border-4 w-6 h-6"></span>
              <span>جاري التجهيز...</span>
            </span>
          ) : (
            "ابدأ الاختبار"
          )}
        </button>
      </main>
    </div>
  );
}
