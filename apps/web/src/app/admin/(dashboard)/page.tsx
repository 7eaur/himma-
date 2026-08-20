"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Users, Activity, Plus } from "lucide-react";

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
        
        if (meRes.ok) setResearcher(await meRes.json());
        if (studentsRes.ok) setStudents(await studentsRes.json());
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
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div className="spinner w-8 h-8 border-4"></div>
      </div>
    );
  }

  return (
    <div className="flex-1 w-full max-w-6xl mx-auto space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-navy mb-1">
            مرحباً، {researcher?.username || "الباحثة"}
          </h1>
          <p className="text-muted text-sm">نظرة عامة على أداء الطلاب ونشاطاتهم اليوم.</p>
        </div>
        <Link href="/admin/students/new" className="btn-primary w-fit">
          <Plus size={20} />
          إضافة طالب
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="stat-card">
          <div className="stat-icon bg-primary/10 text-primary">
            <Users size={24} />
          </div>
          <div>
            <p className="stat-label">إجمالي الطلاب</p>
            <p className="stat-value">{students.length}</p>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon bg-green/10 text-green">
            <Activity size={24} />
          </div>
          <div>
            <p className="stat-label">الطلاب النشطين</p>
            <p className="stat-value">{students.length}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-bold text-navy">الطلاب المضافين حديثاً</h2>
          <Link href="/admin/students" className="text-primary hover:underline text-sm font-medium">
            عرض الكل
          </Link>
        </div>
        
        {students.length === 0 ? (
          <div className="empty-state">
            <Image src="/characters/girl/welcome.png" alt="No students" width={100} height={140} className="mb-6 opacity-80" />
            <h3 className="text-lg font-bold text-navy mb-2">لا يوجد طلاب حتى الآن</h3>
            <p className="text-muted mb-6">أضف أول طالب للبدء في تتبع تقدمهم</p>
            <Link href="/admin/students/new" className="btn-primary">
              <Plus size={20} />
              إضافة طالب جديد
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>الاسم</th>
                  <th>الصف</th>
                  <th>رمز الدخول</th>
                </tr>
              </thead>
              <tbody>
                {students.slice(0, 5).map(student => (
                  <tr key={student.id}>
                    <td className="font-medium text-navy">{student.full_name}</td>
                    <td>{student.grade_level}</td>
                    <td>
                      <span className="badge badge-gray border border-border tracking-widest px-3 py-1 font-mono text-sm" dir="ltr">
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
