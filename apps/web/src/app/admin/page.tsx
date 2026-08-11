"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "./admin.module.css";
import type { AudioSubmission, StudentListItem } from "../../types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function AdminDashboard() {
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [pendingAudio, setPendingAudio] = useState<AudioSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [meRes, studentsRes, audioRes] = await Promise.all([
          fetch(`${API_URL}/me`, { credentials: "include" }),
          fetch(`${API_URL}/researcher/students`, { credentials: "include" }),
          fetch(`${API_URL}/review/pending-audio`, { credentials: "include" }),
        ]);

        if (!meRes.ok) { router.push("/admin/login"); return; }
        if (!active) return;

        if (studentsRes.ok) setStudents(await studentsRes.json());
        if (audioRes.ok) setPendingAudio(await audioRes.json());
      } catch (e) {
        console.error("Dashboard load failed", e);
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, [router]);

  if (loading) return <div>جاري التحميل...</div>;

  return (
    <div>
      <h1 style={{ marginBottom: "2rem" }}>لوحة القيادة</h1>
      
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{students.length}</span>
          <span className={styles.statLabel}>إجمالي الطلاب</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{pendingAudio.length}</span>
          <span className={styles.statLabel}>تسجيلات معلقة للمراجعة</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statValue}>
            {students.filter(s => s.status === "active").length}
          </span>
          <span className={styles.statLabel}>طلاب نشطون</span>
        </div>
      </div>
      
      <h3>نظرة سريعة</h3>
      <p>اختر من القائمة الجانبية لإدارة الطلاب ومراجعة التسجيلات الصوتية.</p>
    </div>
  );
}
