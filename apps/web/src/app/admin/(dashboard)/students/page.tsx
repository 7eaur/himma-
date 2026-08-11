"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import styles from "../admin.module.css";
import type { StudentListItem } from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function StudentsList() {
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`${API_URL}/researcher/students`, { credentials: "include" });
        if (!res.ok) throw new Error("فشل تحميل الطلاب");
        setStudents(await res.json());
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = students.filter(s => s.full_name.includes(search) || s.access_code.includes(search.toUpperCase()));

  if (loading) return <div>جاري التحميل...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <h1>قائمة الطلاب</h1>
        <Link href="/admin/students/new" className="btn btn-primary">
          ➕ إضافة طالب
        </Link>
      </div>

      <input
        type="text"
        placeholder="ابحث بالاسم أو برمز الدخول..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="input-field"
        style={{ marginBottom: "1.5rem", maxWidth: "400px" }}
      />

      <div className={styles.tableWrap}>
        {filtered.length === 0 ? (
          <p>لا يوجد طلاب يطابقون البحث.</p>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>الاسم</th>
                <th>الصف</th>
                <th>رمز الدخول</th>
                <th>الحالة</th>
                <th>إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(s => (
                <tr key={s.id}>
                  <td>{s.full_name}</td>
                  <td>{s.grade}</td>
                  <td><code>{s.access_code}</code></td>
                  <td>{s.status === "active" ? "نشط" : "غير نشط"}</td>
                  <td>
                    <Link href={`/admin/students/${s.id}`} className="btn btn-secondary btn-small">
                      عرض الملف
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
