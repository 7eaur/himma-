"use client";

import { useState, useEffect, useCallback } from 'react';
import type { AudioSubmission } from '../../types/api';

export default function ResearcherPage() {
  const [pending, setPending] = useState<AudioSubmission[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPending = useCallback(async () => {
    try {
      const res = await fetch('/api/review/pending-audio');
      const data: AudioSubmission[] = await res.json();
      setPending(data || []);
    } catch (err) {
      console.error("Failed to fetch pending submissions", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // fetchPending is async — setState runs inside the async callback, not synchronously
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const res = await fetch('/api/review/pending-audio');
        if (!active) return;
        const data: AudioSubmission[] = await res.json();
        setPending(data || []);
      } catch (err) {
        console.error("Failed to fetch pending submissions", err);
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, []);

  const handleGrade = useCallback(async (submissionId: number, isValid: boolean) => {
    const payload = isValid
      ? { is_valid: true, target_units: 5, deletions: 0, substitutions: 0, insertions: 0 }
      : { is_valid: false };

    try {
      await fetch(`/api/review/audio/${submissionId}/grade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      await fetchPending();
    } catch {
      alert("Error grading submission");
    }
  }, [fetchPending]);

  if (loading) return <div style={{ padding: '2rem' }}>جاري التحميل...</div>;

  return (
    <div style={{ padding: "2rem", direction: "rtl", fontFamily: "var(--font-noto-kufi), sans-serif" }}>
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
                {pending.map((sub) => (
                  <tr key={sub.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                    <td style={{ padding: "0.5rem" }}>{sub.id}</td>
                    <td style={{ padding: "0.5rem" }}>{new Date(sub.submitted_at).toLocaleDateString('ar-SA')}</td>
                    <td style={{ padding: "0.5rem" }}>
                      <audio controls src={`/api/recordings/stream/${sub.storage_key}`} />
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
                        غير صالح للاعتماد
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
