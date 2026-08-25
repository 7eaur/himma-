"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Activity, ArrowLeft, BookOpenCheck, Plus, ShieldCheck, Users } from "lucide-react";

interface Supervisor {
  id: number;
  full_name?: string;
  username?: string;
  role: string;
}

interface Student {
  id: number;
  full_name: string;
  grade_level: number;
  access_code: string;
  current_level: number;
  status: "active" | "inactive";
  posttest_enabled: boolean;
  posttest_eligible: boolean;
  core_completed_items: number;
  core_total_items: number;
  created_at: string;
}

export default function AdminDashboard() {
  const [supervisor, setSupervisor] = useState<Supervisor | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    void Promise.all([
      fetch("/api/me", { cache: "no-store" }),
      fetch("/api/researcher/students", { cache: "no-store" }),
    ])
      .then(async ([meResponse, studentsResponse]) => {
        if (!meResponse.ok || !studentsResponse.ok) throw new Error("تعذر تحميل لوحة المشرف");
        const meData: Supervisor = await meResponse.json();
        const studentsData: Student[] = await studentsResponse.json();
        if (cancelled) return;
        setSupervisor(meData);
        setStudents(studentsData);
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل لوحة المشرف");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const activeStudents = useMemo(() => students.filter((student) => student.status === "active").length, [students]);
  const learningStudents = useMemo(() => students.filter((student) => student.core_completed_items > 0 && student.core_completed_items < student.core_total_items).length, [students]);
  const readyForPosttest = useMemo(() => students.filter((student) => student.posttest_eligible || student.posttest_enabled).length, [students]);
  const recentStudents = useMemo(() => [...students].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)).slice(0, 6), [students]);
  const supervisorName = supervisor?.full_name || supervisor?.username || "المشرف";

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[60vh] gap-3" dir="rtl">
        <div className="spinner w-10 h-10 border-4" />
        <p className="text-muted">جاري تجهيز لوحة المشرف...</p>
      </div>
    );
  }

  return (
    <div className="flex-1 w-full max-w-6xl mx-auto space-y-7 pb-10" dir="rtl">
      <div className="rounded-3xl bg-gradient-to-l from-[#edf6ff] to-white border border-border p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div>
          <div className="inline-flex items-center gap-2 text-primary text-sm font-semibold mb-2"><ShieldCheck size={17} /> لوحة المشرف</div>
          <h1 className="text-3xl font-bold text-navy mb-2">مرحبًا، {supervisorName}</h1>
          <p className="text-muted">تابع الطلاب، الأنشطة، نتائج التكيف، والتجهيز للاختبار البعدي من مكان واحد.</p>
        </div>
        <Link href="/admin/students/new" className="btn-primary w-fit"><Plus size={19} /> إضافة طالب</Link>
      </div>

      {error && <div className="alert-error">{error}</div>}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="stat-card"><div className="stat-card-icon blue"><Users size={23} /></div><div><p className="stat-card-value">{students.length}</p><p className="stat-card-label">إجمالي الطلاب</p></div></div>
        <div className="stat-card"><div className="stat-card-icon green"><Activity size={23} /></div><div><p className="stat-card-value">{activeStudents}</p><p className="stat-card-label">حسابات نشطة</p></div></div>
        <div className="stat-card"><div className="stat-card-icon yellow"><BookOpenCheck size={23} /></div><div><p className="stat-card-value">{learningStudents}</p><p className="stat-card-label">في المسار التعليمي</p></div></div>
        <div className="stat-card"><div className="stat-card-icon blue"><ShieldCheck size={23} /></div><div><p className="stat-card-value">{readyForPosttest}</p><p className="stat-card-label">جاهزون للاختبار البعدي</p></div></div>
      </div>

      <section className="card">
        <div className="flex justify-between items-center gap-3 mb-6 flex-wrap">
          <div><h2 className="text-lg font-bold text-navy">أحدث الطلاب</h2><p className="text-sm text-muted mt-1">آخر الحسابات المضافة وحالة تقدمها الحالية.</p></div>
          <Link href="/admin/students" className="text-primary text-sm font-semibold inline-flex items-center gap-1">عرض جميع الطلاب <ArrowLeft size={16} /></Link>
        </div>

        {recentStudents.length === 0 ? (
          <div className="empty-state">
            <Image src="/characters/girl/welcome.png" alt="شخصية هِمّة" width={105} height={140} className="mb-6" />
            <h3>لا يوجد طلاب حتى الآن</h3>
            <p className="mb-6">أضف أول طالب ليبدأ مساره في هِمّة.</p>
            <Link href="/admin/students/new" className="btn-primary"><Plus size={19} /> إضافة طالب جديد</Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr><th>الطالب</th><th>رمز الدخول</th><th>المستوى</th><th>تقدم الأنشطة</th><th>الحالة</th></tr></thead>
              <tbody>
                {recentStudents.map((student) => {
                  const progress = Math.round((student.core_completed_items / Math.max(1, student.core_total_items)) * 100);
                  return (
                    <tr key={student.id}>
                      <td><Link href={`/admin/students/${student.id}`} className="font-semibold text-navy hover:text-primary">{student.full_name}</Link></td>
                      <td><span className="badge badge-gray border border-border tracking-widest px-3 py-1 font-mono" dir="ltr">{student.access_code}</span></td>
                      <td>المستوى {student.current_level}</td>
                      <td><div className="flex items-center gap-2 min-w-[130px]"><div className="progress-track"><div className="progress-fill" style={{ width: `${progress}%` }} /></div><span className="text-xs text-muted">{student.core_completed_items}/{student.core_total_items}</span></div></td>
                      <td><span className={`badge ${student.status === "active" ? "badge-green" : "badge-gray"}`}>{student.status === "active" ? "نشط" : "موقوف"}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
