"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { BarChart3, BookOpenCheck, CheckCircle2, Layers3, Users } from "lucide-react";

interface Student {
  id: number;
  full_name: string;
  current_level: number;
  status: "active" | "inactive";
  core_completed_items: number;
  core_total_items: number;
  posttest_enabled: boolean;
  posttest_eligible: boolean;
}

export default function ReportsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    void fetch("/api/researcher/students", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("تعذر تحميل ملخص العينة");
        const data: Student[] = await response.json();
        if (!cancelled) setStudents(data);
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل الملخص");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const stats = useMemo(() => {
    const progressValues = students.map((student) => student.core_completed_items / Math.max(1, student.core_total_items));
    const averageProgress = progressValues.length
      ? Math.round((progressValues.reduce((sum, value) => sum + value, 0) / progressValues.length) * 100)
      : 0;
    return {
      total: students.length,
      active: students.filter((student) => student.status === "active").length,
      averageProgress,
      ready: students.filter((student) => student.posttest_eligible || student.posttest_enabled).length,
      levels: [1, 2, 3].map((level) => students.filter((student) => student.current_level === level).length),
    };
  }, [students]);

  return (
    <div className="flex-1 font-plex max-w-6xl w-full mx-auto" dir="rtl">
      <div className="mb-7">
        <p className="text-sm text-primary font-semibold mb-1">ملخص حي للعينة</p>
        <h1 className="text-3xl font-bold text-navy mb-2">التقارير والإحصائيات</h1>
        <p className="text-muted">عرض تشغيلي مباشر لتوزيع الطلاب وتقدم الأنشطة. التقارير البحثية المتقدمة تبقى ضمن مرحلتها المخصصة.</p>
      </div>

      {error && <div className="alert-error mb-5">{error}</div>}

      {loading ? (
        <div className="card min-h-64 flex flex-col items-center justify-center gap-3"><div className="spinner w-10 h-10" /><p className="text-muted">جاري حساب المؤشرات...</p></div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
            <div className="stat-card"><div className="stat-card-icon blue"><Users size={23} /></div><div><p className="stat-card-value">{stats.total}</p><p className="stat-card-label">إجمالي الطلاب</p></div></div>
            <div className="stat-card"><div className="stat-card-icon green"><CheckCircle2 size={23} /></div><div><p className="stat-card-value">{stats.active}</p><p className="stat-card-label">حسابات نشطة</p></div></div>
            <div className="stat-card"><div className="stat-card-icon yellow"><BookOpenCheck size={23} /></div><div><p className="stat-card-value">{stats.averageProgress}%</p><p className="stat-card-label">متوسط تقدم الأنشطة</p></div></div>
            <div className="stat-card"><div className="stat-card-icon blue"><BarChart3 size={23} /></div><div><p className="stat-card-value">{stats.ready}</p><p className="stat-card-label">جاهزون للاختبار البعدي</p></div></div>
          </div>

          <div className="grid lg:grid-cols-[320px_1fr] gap-6">
            <section className="card">
              <div className="flex items-center gap-2 mb-5"><Layers3 size={20} className="text-primary" /><h2 className="font-bold text-navy text-lg">توزيع المستويات</h2></div>
              <div className="space-y-5">
                {stats.levels.map((count, index) => {
                  const percent = stats.total ? Math.round((count / stats.total) * 100) : 0;
                  return (
                    <div key={index}>
                      <div className="flex items-center justify-between text-sm mb-2"><span className="font-semibold text-navy">المستوى {index + 1}</span><span className="text-muted">{count} طالب · {percent}%</span></div>
                      <div className="progress-track"><div className="progress-fill" style={{ width: `${percent}%` }} /></div>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="card">
              <div className="flex items-center justify-between gap-3 mb-5"><div><h2 className="font-bold text-navy text-lg">تقدم الطلاب</h2><p className="text-sm text-muted mt-1">الأنشطة الأساسية في المستوى الحالي.</p></div><Link href="/admin/students" className="text-primary text-sm font-semibold">إدارة الطلاب</Link></div>
              {students.length === 0 ? (
                <div className="empty-state py-10"><h3>لا توجد بيانات بعد</h3><p>تظهر المؤشرات بعد إضافة الطلاب وبدء المسار.</p></div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead><tr><th>الطالب</th><th>المستوى</th><th>الأنشطة</th><th>التقدم</th><th>البعدي</th></tr></thead>
                    <tbody>
                      {students.map((student) => {
                        const progress = Math.round((student.core_completed_items / Math.max(1, student.core_total_items)) * 100);
                        return (
                          <tr key={student.id}>
                            <td><Link href={`/admin/students/${student.id}`} className="font-semibold text-navy hover:text-primary">{student.full_name}</Link></td>
                            <td>{student.current_level}</td>
                            <td>{student.core_completed_items}/{student.core_total_items}</td>
                            <td><div className="flex items-center gap-2 min-w-[130px]"><div className="progress-track"><div className="progress-fill" style={{ width: `${progress}%` }} /></div><span className="text-xs text-muted">{progress}%</span></div></td>
                            <td><span className={`badge ${student.posttest_enabled ? "badge-green" : student.posttest_eligible ? "badge-yellow" : "badge-gray"}`}>{student.posttest_enabled ? "مفتوح" : student.posttest_eligible ? "جاهز" : "غير جاهز"}</span></td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
