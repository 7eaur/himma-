"use client";

import { useState, useEffect } from 'react';

export default function ResearcherPage() {
  const [pending, setPending] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPending = async () => {
    try {
      const res = await fetch('/api/review/pending-audio');
      const data = await res.json();
      setPending(data || []);
    } catch (e) {
      console.error("Failed to fetch", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, []);

  const handleGrade = async (submissionId: number, isValid: boolean) => {
    // Basic mock grading for V1
    const payload = isValid 
      ? { is_valid: true, target_units: 5, deletions: 0, substitutions: 0, insertions: 0 } 
      : { is_valid: false };

    try {
      await fetch(`/api/review/audio/${submissionId}/grade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      fetchPending(); // Refresh list
    } catch (e) {
      alert("Error grading submission");
    }
  };

  if (loading) return <div>جاري التحميل...</div>;

  return (
    <div style={{ padding: "2rem", direction: "rtl", fontFamily: "sans-serif" }}>
      <h1>لوحة الباحثة</h1>
      <p>مرحبًا بك في لوحة تحكم الباحثة.</p>

      <section style={{ marginTop: "2rem", padding: "1rem", border: "1px solid #e2e8f0", borderRadius: "8px" }}>
        <h2>المراجعات المعلقة (التسجيلات الصوتية)</h2>
        
        <div style={{ marginTop: "1rem" }}>
          {pending.length === 0 ? (
            <p>لا توجد مراجعات معلقة.</p>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "right" }}>
              <thead>
                <tr style={{ backgroundColor: "#f8fafc", borderBottom: "2px solid #cbd5e1" }}>
                  <th style={{ padding: "0.5rem" }}>رقم التسجيل</th>
                  <th style={{ padding: "0.5rem" }}>تاريخ التقديم</th>
                  <th style={{ padding: "0.5rem" }}>الملف الصوتي</th>
                  <th style={{ padding: "0.5rem" }}>الإجراء</th>
                </tr>
              </thead>
              <tbody>
                {pending.map((sub: any) => (
                  <tr key={sub.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "0.5rem" }}>{sub.id}</td>
                    <td style={{ padding: "0.5rem" }}>{new Date(sub.submitted_at).toLocaleDateString()}</td>
                    <td style={{ padding: "0.5rem" }}>
                      <audio controls src={`https://mock-s3-bucket.local/${sub.storage_key}`} />
                    </td>
                    <td style={{ padding: "0.5rem" }}>
                      <button 
                        onClick={() => handleGrade(sub.id, true)}
                        style={{ padding: "0.25rem 0.75rem", backgroundColor: "#10b981", color: "white", border: "none", borderRadius: "4px", marginLeft: "0.5rem", cursor: "pointer" }}
                      >
                        صحيح (100%)
                      </button>
                      <button 
                        onClick={() => handleGrade(sub.id, false)}
                        style={{ padding: "0.25rem 0.75rem", backgroundColor: "#ef4444", color: "white", border: "none", borderRadius: "4px", cursor: "pointer" }}
                      >
                        غير صالح للإعتماد
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}
