"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, User, Hash, Calendar, Play, BookOpen } from "lucide-react";
import { useParams } from "next/navigation";

interface Student {
  id: number;
  full_name: string;
  grade_level: number;
  access_code: string;
  created_at: string;
  current_level: number;
  status: "active" | "inactive";
  posttest_enabled: boolean;
  posttest_eligible: boolean;
  core_completed_items: number;
  core_total_items: number;
  core_completed: boolean;
}

export default function StudentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatingPosttest, setUpdatingPosttest] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStudent = async () => {
      try {
        const res = await fetch(`/api/researcher/students/${id}`);
        if (res.ok) {
          setStudent(await res.json());
        } else if (res.status === 404) {
          setError("لم يتم العثور على الطالب");
        } else {
          setError("تعذر تحميل بيانات الطالب");
        }
      } catch {
        setError("حدث خطأ أثناء تحميل بيانات الطالب");
      } finally {
        setLoading(false);
      }
    };

    if (id) void fetchStudent();
  }, [id]);

  const updatePosttestAccess = async () => {
    if (!student) return;
    setUpdatingPosttest(true);
    setError("");
    try {
      const res = await fetch(`/api/researcher/students/${student.id}/posttest-access`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !student.posttest_enabled }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "تعذر تحديث إتاحة الاختبار البعدي");
      setStudent(data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "تعذر تحديث إتاحة الاختبار البعدي");
    } finally {
      setUpdatingPosttest(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex justify-center py-12">
        <div className="spinner w-8 h-8" />
      </div>
    );
  }

  if (!student) {
    return (
      <div className="flex-1 font-plex max-w-4xl mx-auto w-full">
        <div className="alert-error">{error || "لم يتم العثور على الطالب"}</div>
        <Link href="/admin/students" className="btn-primary mt-4">العودة لقائمة الطلاب</Link>
      </div>
    );
  }

  const progressPercent = Math.round((student.core_completed_items / Math.max(1, student.core_total_items)) * 100);

  return (
    <div className="flex-1 font-plex max-w-4xl mx-auto w-full">
      <div className="mb-6 flex items-center gap-4">
        <Link href="/admin/students" className="p-2 text-muted hover:text-navy hover:bg-bg rounded-full transition-colors">
          <ArrowRight size={24} />
        </Link>
        <h1 className="text-2xl font-bold text-navy">ملف الطالب</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <div className="card text-center">
            <div className="w-24 h-24 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4 text-primary">
              <User size={48} />
            </div>
            <h2 className="text-xl font-bold text-navy mb-1">{student.full_name}</h2>
            <p className="text-muted mb-4">الصف {student.grade_level}</p>

            <div className="bg-bg p-3 rounded-md mb-4">
              <p className="text-xs text-muted mb-1">رمز الدخول</p>
              <p className="text-lg font-mono font-bold text-primary tracking-widest">{student.access_code}</p>
            </div>

            <span className="badge bg-green/10 text-green w-full py-2">
              {student.status === "active" ? "نشط" : "غير نشط"}
            </span>
          </div>
        </div>

        <div className="md:col-span-2 space-y-6">
          <div className="card">
            <h3 className="text-lg font-bold text-navy mb-4 border-b border-border pb-2">المعلومات الأساسية</h3>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Hash className="text-muted mt-0.5" size={18} />
                <div>
                  <p className="text-sm text-muted">المعرف الفريد</p>
                  <p className="text-navy text-sm font-mono">{student.id}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Hash className="text-muted mt-0.5" size={18} />
                <div>
                  <p className="text-sm text-muted">المستوى الحالي</p>
                  <p className="text-navy">المستوى {student.current_level}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Calendar className="text-muted mt-0.5" size={18} />
                <div>
                  <p className="text-sm text-muted">تاريخ الإضافة</p>
                  <p className="text-navy">{new Date(student.created_at).toLocaleDateString("ar-SA")}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between gap-4 mb-4 border-b border-border pb-2">
              <h3 className="text-lg font-bold text-navy">المسار التعليمي</h3>
              <BookOpen size={20} className="text-primary" />
            </div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-muted">الأنشطة الأساسية المكتملة</span>
              <strong className="text-navy">{student.core_completed_items} من {student.core_total_items}</strong>
            </div>
            <div className="w-full h-3 rounded-full bg-bg overflow-hidden" aria-label={`تقدم الأنشطة ${progressPercent}%`}>
              <div className="h-full bg-green rounded-full" style={{ width: `${progressPercent}%` }} />
            </div>
            <p className="text-sm text-muted mt-3">
              {student.core_completed
                ? "اكتمل المسار الأساسي المخصص لهذا المستوى."
                : "يستمر الطالب في الأنشطة الأساسية حتى يكمل الأنشطة العشرة."}
            </p>
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-navy mb-4 border-b border-border pb-2">الاختبارات</h3>
            {error && <div className="alert-error mb-4">{error}</div>}
            <div className="flex flex-col items-center justify-center py-8 text-center border-2 border-dashed border-border rounded-lg">
              <p className="text-muted mb-4">
                {student.posttest_enabled
                  ? "الاختبار البعدي متاح للطالب الآن."
                  : student.posttest_eligible
                    ? "أكمل الطالب الاختبار القبلي ومساره الأساسي، ويمكن إتاحة الاختبار البعدي له."
                    : "يتاح الاختبار البعدي بعد إكمال الاختبار القبلي والأنشطة الأساسية العشرة."}
              </p>
              <button
                className="btn-primary flex items-center gap-2"
                onClick={updatePosttestAccess}
                disabled={updatingPosttest || (!student.posttest_eligible && !student.posttest_enabled)}
              >
                <Play size={18} />
                <span>
                  {updatingPosttest
                    ? "جاري الحفظ..."
                    : student.posttest_enabled
                      ? "إيقاف إتاحة الاختبار البعدي"
                      : "إتاحة الاختبار البعدي"}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
