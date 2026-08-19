"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import styles from "../../admin.module.css";
import type { StudentProfile } from "@/types/api";



export default function StudentDetail() {
  const params = useParams();
  const router = useRouter();
  const [student, setStudent] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/api/researcher/students`, { credentials: "include" });
        if (!res.ok) throw new Error("فشل تحميل بيانات الطالب");
        const list: StudentProfile[] = await res.json();
        const found = list.find(s => s.id === Number(params.id));
        if (found) {
          setStudent(found);
        } else {
          setError("لم يتم العثور على الطالب");
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.id]);

  if (loading) return <div>جاري التحميل...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div style={{ maxWidth: "800px" }}>
      <button onClick={() => router.back()} className="btn btn-secondary" style={{ marginBottom: "2rem" }}>
        ← العودة للقائمة
      </button>

      {student && (
        <>
          <h1 style={{ marginBottom: "2rem" }}>ملف الطالب: {student.full_name}</h1>
          
          <div className={styles.statsGrid}>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>الصف الدراسي</span>
              <span className={styles.statValue}>{student.grade}</span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>المستوى الحالي</span>
              <span className={styles.statValue}>{student.current_level}</span>
            </div>
            <div className={styles.statCard}>
              <span className={styles.statLabel}>الحالة</span>
              <span className={styles.statValue} style={{ color: student.status === "active" ? "var(--success)" : "var(--error)" }}>
                {student.status === "active" ? "نشط" : "غير نشط"}
              </span>
            </div>
          </div>
          
          <div className={styles.statCard} style={{ marginTop: "2rem", textAlign: "right" }}>
            <h3 style={{ marginBottom: "1rem" }}>معلومات الدخول</h3>
            <p style={{ marginBottom: "0.5rem" }}>رمز الدخول للطالب:</p>
            <code style={{ fontSize: "1.5rem", color: "var(--primary)" }}>{student.access_code}</code>
          </div>
        </>
      )}
    </div>
  );
}
