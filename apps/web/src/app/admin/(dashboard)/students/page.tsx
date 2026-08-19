"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { UserPlus, Eye } from "lucide-react";

interface Student {
  id: string;
  full_name: string;
  grade_level: number;
  access_code: string;
  created_at: string;
}

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const res = await fetch("/api/researcher/students");
        if (res.ok) {
          setStudents(await res.json());
        }
      } catch (err) {
        console.error("Error fetching students", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchStudents();
  }, []);

  return (
    <div className="flex-1 font-plex max-w-6xl w-full mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-navy mb-2">إدارة الطلاب</h1>
          <p className="text-muted">عرض وإدارة جميع الطلاب المسجلين.</p>
        </div>
        <Link href="/admin/students/new" className="btn-primary flex items-center gap-2">
          <UserPlus size={18} />
          <span>إضافة طالب</span>
        </Link>
      </div>

      <div className="card">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="spinner w-8 h-8"></div>
          </div>
        ) : students.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Image src="/characters/boy-welcome.png" alt="No students" width={120} height={150} className="opacity-50 mb-4" />
            <h3 className="text-lg font-medium text-navy mb-2">لا يوجد طلاب</h3>
            <p className="text-muted mb-6">لم تقم بإضافة أي طلاب بعد.</p>
            <Link href="/admin/students/new" className="btn-primary">
              إضافة طالب جديد
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="border-b border-border bg-bg/50">
                  <th className="py-4 px-4 font-semibold text-navy">الاسم</th>
                  <th className="py-4 px-4 font-semibold text-navy">الصف</th>
                  <th className="py-4 px-4 font-semibold text-navy">رمز الدخول</th>
                  <th className="py-4 px-4 font-semibold text-navy">تاريخ الإضافة</th>
                  <th className="py-4 px-4 font-semibold text-navy text-center">الإجراءات</th>
                </tr>
              </thead>
              <tbody>
                {students.map(student => (
                  <tr key={student.id} className="border-b border-border last:border-0 hover:bg-bg/50 transition-colors">
                    <td className="py-4 px-4 text-navy font-medium">{student.full_name}</td>
                    <td className="py-4 px-4 text-navy">{student.grade_level}</td>
                    <td className="py-4 px-4">
                      <span className="badge bg-white text-primary border border-primary/20 tracking-wider font-mono px-3 py-1 ltr text-left">
                        {student.access_code}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-muted text-sm">
                      {new Date(student.created_at).toLocaleDateString('ar-SA')}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex justify-center">
                        <Link 
                          href={`/admin/students/${student.id}`}
                          className="p-2 text-muted hover:text-primary hover:bg-primary/10 rounded-md transition-colors"
                          title="عرض التفاصيل"
                        >
                          <Eye size={20} />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
