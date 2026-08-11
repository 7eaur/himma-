"use client";

import { useState, useEffect, useCallback } from "react";
import styles from "../admin.module.css";
import type { AudioSubmission } from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function AudioReview() {
  const [pendingAudio, setPendingAudio] = useState<AudioSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/review/pending-audio`, { credentials: "include" });
      if (!res.ok) throw new Error("فشل تحميل التسجيلات");
      setPendingAudio(await res.json());
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleGrade = async (submissionId: number, isValid: boolean) => {
    const payload = isValid
      ? { is_valid: true, target_units: 5, deletions: 0, substitutions: 0, insertions: 0 }
      : { is_valid: false };
      
    try {
      const res = await fetch(`${API_URL}/review/audio/${submissionId}/grade`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("تعذر حفظ التقييم");
      
      // Remove from list locally for speed, then refresh
      setPendingAudio(prev => prev.filter(s => s.id !== submissionId));
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading) return <div>جاري التحميل...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div>
      <h1 style={{ marginBottom: "2rem" }}>مراجعة التسجيلات الصوتية</h1>
      
      <div className={styles.audioList}>
        {pendingAudio.length === 0 ? (
          <div className={styles.statCard}>
            <p>لا توجد تسجيلات معلقة للمراجعة. عمل رائع! ✅</p>
          </div>
        ) : (
          pendingAudio.map((sub) => (
            <div key={sub.id} className={styles.statCard} style={{ display: "flex", flexDirection: "column", gap: "1rem", textAlign: "right" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--bg-muted)", paddingBottom: "1rem" }}>
                <strong>تسجيل #{sub.id}</strong>
                <span style={{ fontSize: "0.9rem", color: "var(--dark)", opacity: 0.7 }}>
                  {new Date(sub.submitted_at).toLocaleString("ar-SA")}
                </span>
              </div>
              
              <audio
                controls
                src={`${API_URL}/recordings/stream/${sub.storage_key}`}
                style={{ width: "100%", margin: "1rem 0" }}
              />
              
              <div style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
                <button
                  className="btn btn-primary"
                  style={{ flex: 1, backgroundColor: "var(--success)" }}
                  onClick={() => handleGrade(sub.id, true)}
                >
                  ✅ قراءة صحيحة
                </button>
                <button
                  className="btn btn-primary"
                  style={{ flex: 1, backgroundColor: "var(--error)" }}
                  onClick={() => handleGrade(sub.id, false)}
                >
                  ❌ غير صالح
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
