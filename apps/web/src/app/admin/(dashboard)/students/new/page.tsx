"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import styles from "../../admin.module.css";
import type { StudentProfile } from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function CreateStudent() {
  const [name, setName] = useState("");
  const [grade, setGrade] = useState("1");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [createdStudent, setCreatedStudent] = useState<StudentProfile | null>(null);
  
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    
    try {
      const res = await fetch(`${API_URL}/researcher/students`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ full_name: name, grade: parseInt(grade) }),
      });
      
      if (!res.ok) throw new Error("تعذر إنشاء الطالب");
      
      const data = await res.json();
      setCreatedStudent(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "600px" }}>
      <h1 style={{ marginBottom: "2rem" }}>إضافة طالب جديد</h1>
      
      {error && <div className="alert alert-error" style={{ marginBottom: "1rem" }}>{error}</div>}
      
      {createdStudent ? (
        <div className="alert alert-success" style={{ padding: "2rem", textAlign: "center" }}>
          <h2>تم إنشاء الطالب بنجاح!</h2>
          <p style={{ margin: "1rem 0" }}>رمز الدخول الخاص به هو:</p>
          <code style={{ fontSize: "2rem", display: "block", color: "var(--primary)" }}>
            {createdStudent.access_code}
          </code>
          <p style={{ marginTop: "1rem", color: "var(--dark)" }}>احتفظ بهذا الرمز وأعطه للطالب للدخول</p>
          
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", marginTop: "2rem" }}>
            <button className="btn btn-secondary" onClick={() => { setCreatedStudent(null); setName(""); }}>
              إضافة طالب آخر
            </button>
            <button className="btn btn-primary" onClick={() => router.push("/admin/students")}>
              العودة للقائمة
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div className="form-group">
            <label className="form-label">الاسم الكامل</label>
            <input
              type="text"
              className="input-field"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              data-testid="input-student-name"
              placeholder="مثال: أحمد العتيبي"
            />
          </div>
          <div className="form-group">
            <label className="form-label">الصف الدراسي</label>
            <select
              className="input-field"
              value={grade}
              onChange={(e) => setGrade(e.target.value)}
              data-testid="input-student-grade"
            >
              <option value="1">الصف الأول</option>
              <option value="2">الصف الثاني</option>
              <option value="3">الصف الثالث</option>
              <option value="4">الصف الرابع</option>
            </select>
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={loading}
            data-testid="btn-create-student"
          >
            {loading ? "جاري الحفظ..." : "إنشاء طالب وتوليد الرمز"}
          </button>
        </form>
      )}
    </div>
  );
}
