"use client";

import { useState, useEffect } from 'react';
import { AssessmentRunner } from '../../components/AssessmentRunner';

export default function StudentPage() {
  const [activeSession, setActiveSession] = useState<{id: number} | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/assessment/active')
      .then(res => res.json())
      .then(data => {
        setActiveSession(data ? data : null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const startAssessment = async () => {
    const res = await fetch('/api/assessment/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_type: 'pretest' })
    });
    const data = await res.json();
    setActiveSession(data);
  };
  if (loading) return <div>جاري التحميل...</div>;

  return (
    <div style={{ padding: "2rem", direction: "rtl", fontFamily: "sans-serif" }}>
      <h1>صفحة الطالب</h1>
      <p>مرحبًا بك في منصة همة.</p>
      
      {!activeSession ? (
        <section style={{ marginTop: "2rem", padding: "1rem", border: "1px solid #e2e8f0", borderRadius: "8px" }}>
          <h2>التقييم القبلي</h2>
          <button 
            onClick={startAssessment}
            style={{ padding: "0.5rem 1rem", backgroundColor: "#3b82f6", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}
          >
            بدء التقييم
          </button>
        </section>
      ) : (
        <section style={{ marginTop: "2rem" }}>
          <AssessmentRunner 
            sessionId={activeSession.id} 
            onComplete={async () => {
              await fetch(`/api/assessment/session/${activeSession.id}/finish`, { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() } });
              setActiveSession(null);
              alert("تم الانتهاء من التقييم بنجاح!");
            }} 
          />
        </section>
      )}
    </div>
  );
}
