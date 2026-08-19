"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Users, Activity } from "lucide-react";

interface Researcher {
  id: string;
  username: string;
  role: string;
}

interface Student {
  id: string;
  full_name: string;
  grade_level: number;
  access_code: string;
}

export default function AdminDashboard() {
  const [researcher, setResearcher] = useState<Researcher | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [meRes, studentsRes] = await Promise.all([
          fetch("/api/me"),
          fetch("/api/researcher/students")
        ]);
        
        if (meRes.ok) {
          setResearcher(await meRes.json());
        }
        
        if (studentsRes.ok) {
          setStudents(await studentsRes.json());
        }
      } catch (err) {
        console.error("Error fetching dashboard data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="spinner w-8 h-8"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 font-plex max-w-6xl w-full mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-navy mb-2">
          مرحباً، {researcher?.username || "الباحثة"}
        </h1>
        <p className="text-muted">نظرة عامة على أداء الطلاب ونشاطاتهم اليوم.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
            <Users size={24} />
          </div>
          <div>
            <p className="text-sm text-muted mb-1">إجمالي الطلاب</p>
            <p className="text-2xl font-bold text-navy">{students.length}</p>
          </div>
        </div>
        
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-green/10 flex items-center justify-center text-green">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-sm text-muted mb-1">الطلاب النشطين</p>
            <p className="text-2xl font-bold text-navy">{students.length}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-navy">الطلاب المضافين حديثاً</h2>
          <Link href="/admin/students" className="text-primary hover:underline text-sm font-medium">
            عرض الكل
          </Link>
        </div>
        
        {students.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Image src="/characters/girl/welcome.png" alt="No students" width={120} height={150} className="opacity-50 mb-4" />
            <p className="text-muted mb-4">لا يوجد طلاب مضافين حتى الآن.</p>
            <Link href="/admin/students/new" className="btn-primary">
              إضافة طالب جديد
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="pb-3 font-semibold text-muted text-sm">الاسم</th>
                  <th className="pb-3 font-semibold text-muted text-sm">الصف</th>
                  <th className="pb-3 font-semibold text-muted text-sm">رمز الدخول</th>
                </tr>
              </thead>
              <tbody>
                {students.slice(0, 5).map(student => (
                  <tr key={student.id} className="border-b border-border last:border-0">
                    <td className="py-4 text-navy font-medium">{student.full_name}</td>
                    <td className="py-4 text-navy">{student.grade_level}</td>
                    <td className="py-4">
                      <span className="badge bg-bg text-primary border border-primary/20 tracking-wider ltr text-left">
                        {student.access_code}
                      </span>
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
