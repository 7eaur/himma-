"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import type { AudioSubmission } from "../../types/api";
import styles from "./researcher.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type ResearcherProfile = { id: number; username: string; full_name: string };
type Student = { id: number; full_name: string; access_code: string; grade: number; status: string };

export default function ResearcherPage() {
  const [profile, setProfile] = useState<ResearcherProfile | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [pendingAudio, setPendingAudio] = useState<AudioSubmission[]>([]);
  const [activeTab, setActiveTab] = useState<"students" | "audio" | "create">("students");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create student form
  const [newName, setNewName] = useState("");
  const [newGrade, setNewGrade] = useState("1");
  const [creating, setCreating] = useState(false);
  const [createdCode, setCreatedCode] = useState<string | null>(null);

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

        if (!meRes.ok) { router.push("/login?role=researcher"); return; }
        if (!active) return;

        setProfile(await meRes.json() as ResearcherProfile);
        if (studentsRes.ok) setStudents(await studentsRes.json() as Student[]);
        if (audioRes.ok) {
          const data: AudioSubmission[] = await audioRes.json();
          setPendingAudio(data || []);
        }
      } catch {
        if (active) setError("تعذّر الاتصال بالخادم");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, [router]);

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/researcher/students`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ full_name: newName, grade: parseInt(newGrade) }),
      });
      if (!res.ok) throw new Error("Failed to create student");
      const student: Student = await res.json();
      setCreatedCode(student.access_code);
      setStudents((prev) => [...prev, student]);
      setNewName("");
      setNewGrade("1");
    } catch {
      setError("تعذّر إنشاء الطالب");
    } finally {
      setCreating(false);
    }
  };

  const handleGrade = useCallback(async (submissionId: number, isValid: boolean) => {
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
      if (!res.ok) throw new Error("Failed to grade");
      // Refresh pending list
      const audioRes = await fetch(`${API_URL}/review/pending-audio`, { credentials: "include" });
      if (audioRes.ok) {
        const data: AudioSubmission[] = await audioRes.json();
        setPendingAudio(data || []);
      }
    } catch {
      setError("تعذّر حفظ التقييم");
    }
  }, []);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Sidebar */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarLogo}>
          <Image src="/brand/logo-navy.svg" alt="هِمّة" width={100} height={50} />
        </div>
        {profile && (
          <div className={styles.adminInfo}>
            <span className={styles.adminName}>{profile.full_name}</span>
            <span className={styles.adminRole}>باحثة</span>
          </div>
        )}
        <nav className={styles.nav}>
          <button
            className={`${styles.navItem} ${activeTab === "students" ? styles.navActive : ""}`}
            onClick={() => setActiveTab("students")}
          >
            👥 قائمة الطلاب
            {students.length > 0 && <span className={styles.badge}>{students.length}</span>}
          </button>
          <button
            className={`${styles.navItem} ${activeTab === "audio" ? styles.navActive : ""}`}
            onClick={() => setActiveTab("audio")}
          >
            🎙️ مراجعة الصوت
            {pendingAudio.length > 0 && (
              <span className={`${styles.badge} ${styles.badgeAlert}`}>{pendingAudio.length}</span>
            )}
          </button>
          <button
            className={`${styles.navItem} ${activeTab === "create" ? styles.navActive : ""}`}
            onClick={() => setActiveTab("create")}
          >
            ➕ إضافة طالب
          </button>
        </nav>
      </aside>

      {/* Main */}
      <main className={styles.main}>
        <div className={styles.mainHeader}>
          <h1 className={styles.pageTitle}>
            {activeTab === "students" && "قائمة الطلاب"}
            {activeTab === "audio" && "مراجعة التسجيلات الصوتية"}
            {activeTab === "create" && "إضافة طالب جديد"}
          </h1>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: "var(--space-4)" }}>{error}</div>}

        {/* Students Tab */}
        {activeTab === "students" && (
          <div className={styles.tableWrap}>
            {students.length === 0 ? (
              <div className={styles.empty}>
                <p>لا يوجد طلاب بعد.</p>
                <button className="btn btn-primary" onClick={() => setActiveTab("create")}>
                  إضافة أول طالب
                </button>
              </div>
            ) : (
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>الاسم</th>
                    <th>الصف</th>
                    <th>رمز الدخول</th>
                    <th>الحالة</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map((s) => (
                    <tr key={s.id}>
                      <td>{s.full_name}</td>
                      <td>{s.grade}</td>
                      <td><code className={styles.code}>{s.access_code}</code></td>
                      <td>
                        <span className={`${styles.statusBadge} ${s.status === "active" ? styles.statusActive : ""}`}>
                          {s.status === "active" ? "نشط" : s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Audio Review Tab */}
        {activeTab === "audio" && (
          <div className={styles.audioList}>
            {pendingAudio.length === 0 ? (
              <div className={styles.empty}>
                <p>لا توجد تسجيلات معلقة للمراجعة. ✅</p>
              </div>
            ) : (
              pendingAudio.map((sub) => (
                <div key={sub.id} className={styles.audioCard}>
                  <div className={styles.audioMeta}>
                    <span className={styles.audioId}>تسجيل #{sub.id}</span>
                    <span className={styles.audioDate}>
                      {new Date(sub.submitted_at).toLocaleDateString("ar-SA")}
                    </span>
                    <span className={styles.audioSize}>
                      {Math.round(sub.file_size / 1024)} KB
                    </span>
                  </div>
                  <audio
                    controls
                    src={`${API_URL}/recordings/stream/${sub.storage_key}`}
                    className={styles.audioPlayer}
                  />
                  <div className={styles.gradeActions}>
                    <button
                      className="btn btn-secondary"
                      onClick={() => handleGrade(sub.id, true)}
                    >
                      ✅ صحيح
                    </button>
                    <button
                      className="btn btn-danger"
                      onClick={() => handleGrade(sub.id, false)}
                    >
                      ❌ غير صالح
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Create Student Tab */}
        {activeTab === "create" && (
          <div className={styles.createWrap}>
            {createdCode && (
              <div className={`alert alert-success ${styles.codeResult}`}>
                <p>✅ تم إنشاء الطالب بنجاح!</p>
                <p>رمز الدخول:</p>
                <code className={styles.createdCode}>{createdCode}</code>
                <p className={styles.codeNote}>احتفظ بهذا الرمز وأعطه للطالب</p>
                <button className="btn btn-ghost" onClick={() => setCreatedCode(null)}>
                  إضافة طالب آخر
                </button>
              </div>
            )}
            {!createdCode && (
              <form onSubmit={handleCreateStudent} className={styles.createForm}>
                <div className="form-group">
                  <label htmlFor="student-name" className="form-label">اسم الطالب الكامل</label>
                  <input
                    id="student-name"
                    type="text"
                    className="form-input"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    required
                    placeholder="مثال: أحمد محمد العتيبي"
                    data-testid="input-student-name"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="student-grade" className="form-label">الصف الدراسي</label>
                  <select
                    id="student-grade"
                    className="form-input"
                    value={newGrade}
                    onChange={(e) => setNewGrade(e.target.value)}
                    data-testid="input-student-grade"
                  >
                    <option value="1">الصف الأول</option>
                    <option value="2">الصف الثاني</option>
                    <option value="3">الصف الثالث</option>
                    <option value="4">الصف الرابع</option>
                  </select>
                </div>
                <button type="submit" className="btn btn-primary" disabled={creating} data-testid="btn-create-student">
                  {creating ? "جاري الإنشاء..." : "إنشاء الطالب وتوليد رمز الدخول"}
                </button>
              </form>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
