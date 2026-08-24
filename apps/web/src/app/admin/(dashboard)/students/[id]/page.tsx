"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, User, Hash, Calendar, Play } from "lucide-react";
import { useParams } from "next/navigation";

interface Student {
  id: string;
  full_name: string;
  grade_level: number;
  access_code: string;
  created_at: string;
}

export default function StudentDetailPage() {
  const params = useParams();
  const id = params.id as string;
  
  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStudent = async () => {
      try {
        const res = await fetch(`/api/researcher/students`);
        if (res.ok) {
          const students: Student[] = await res.json();
          const found = students.find(s => s.id === id);
          if (found) {
            setStudent(found);
          } else {
            setError("لم يتم العثور على الطالب");
          }
        }
      } catch {
        setError("حدث خطأ أثناء تحميل بيانات الطالب");
      } finally {
        setLoading(false);
      }
    };
    
    if (id) {
      fetchStudent();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="flex-1 flex justify-center py-12">
        <div className="spinner w-8 h-8"></div>
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className="flex-1 font-plex max-w-4xl mx-auto w-full">
        <div className="alert-error">{error || "لم يتم العثور على الطالب"}</div>
        <Link href="/admin/students" className="btn-primary mt-4">العودة لقائمة الطلاب</Link>
      </div>
    );
  }

  return (
    <div className="flex-1 font-plex max-w-4xl mx-auto w-full">
      <div className="mb-6 flex items-center gap-4">
        <Link href="/admin/students" className="p-2 text-muted hover:text-navy hover:bg-bg rounded-full transition-colors">
          <ArrowRight size={24} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-navy">ملف الطالب</h1>
        </div>
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
            
            <span className="badge bg-green/10 text-green w-full py-2">نشط</span>
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
                <Calendar className="text-muted mt-0.5" size={18} />
                <div>
                  <p className="text-sm text-muted">تاريخ الإضافة</p>
                  <p className="text-navy">{new Date(student.created_at).toLocaleDateString('ar-SA')}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-bold text-navy mb-4 border-b border-border pb-2">الاختبارات</h3>
            <div className="flex flex-col items-center justify-center py-8 text-center border-2 border-dashed border-border rounded-lg">
              <p className="text-muted mb-4">لا توجد اختبارات سابقة لهذا الطالب</p>
              <button className="btn-primary flex items-center gap-2">
                <Play size={18} />
                <span>بدء التقييم البعدي</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
