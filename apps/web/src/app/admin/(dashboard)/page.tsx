"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, ArrowLeft, BookOpenCheck, ClipboardCheck, Headphones, Plus, ShieldCheck, Users } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminMobileCard, AdminPage, AdminPageHeader, AdminPanel, AdminResponsiveTable, AdminStat, AdminStatGrid } from "@/components/admin/AdminUI";
import type { StudentV2Home } from "@/app/student/V2StudentDashboard";
import styles from "./admin.module.css";

type RecentStudent = Pick<StudentV2Home, "journey" | "progress" | "current_action" | "data_status"> & {
  id: number; full_name: string; status: "active" | "inactive";
};
type Overview = {
  source: "himma_v2_readmodel";
  counts: { students: number; active_accounts: number; learning: number; ready_for_posttest: number;
    completed: number; assessment_reviews: number; lesson_reviews: number; placements: number };
  recent_students: RecentStudent[];
};
function level(student: RecentStudent) {
  return student.journey && ["placed", "posttest_ready", "completed"].includes(student.journey.placement_state)
    ? `المستوى ${student.journey.current_level}` : "لم يُعتمد بعد";
}
function progress(student: RecentStudent) {
  return student.data_status === "ready" && student.progress.assigned_lessons != null && student.progress.display_percent != null
    ? `${student.progress.completed_lessons} / ${student.progress.assigned_lessons} درس` : "بانتظار التسكين أو استعادة البيانات";
}

export default function AdminDashboard() {
  const [result, setResult] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      setLoading(true); setError("");
      try {
        const response = await fetch("/api/v2/student/admin/overview", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("تعذر تحميل لوحة V2. أعد المحاولة.");
        const data = await response.json() as Overview;
        if (data.source !== "himma_v2_readmodel" || !data.counts || !Array.isArray(data.recent_students))
          throw new Error("مصدر لوحة المتابعة غير متطابق مع V2.");
        if (!controller.signal.aborted) setResult(data);
      } catch (cause) {
        if (!controller.signal.aborted) {
          setResult(null); setError(cause instanceof Error ? cause.message : "تعذر الاتصال بالخادم.");
        }
      } finally { if (!controller.signal.aborted) setLoading(false); }
    };
    void load(); return () => controller.abort();
  }, [reload]);
  const counts = result?.counts;
  const attention = [
    { href: "/admin/v2-assessments", label: "قراءات الاختبارات", value: counts?.assessment_reviews, icon: Headphones },
    { href: "/admin/v2-assessments", label: "قرارات التسكين", value: counts?.placements, icon: ClipboardCheck },
    { href: "/admin/v2-lesson-review", label: "قراءات الدروس", value: counts?.lesson_reviews, icon: BookOpenCheck },
    { href: "/admin/students", label: "جاهزون للاختبار البعدي", value: counts?.ready_for_posttest, icon: ShieldCheck },
  ];
  return <AdminPage>
    <AdminPageHeader eyebrow="مركز متابعة هِمّة" icon={ShieldCheck} title="مرحبًا، إليك متابعة الطلاب"
      description="التسكين والدروس والمراجعات من رحلة الطالب. افتح ملفه لمتابعة حالته أو إدارة حسابه."
      actions={<AdminAction href="/admin/students/new" tone="primary" icon={Plus}>إضافة طالب</AdminAction>} />
    {loading ? <p role="status" className="py-8 text-muted">جاري تحميل المتابعة...</p>
      : error ? <div className="alert-error" role="alert">{error} <AdminAction onClick={() => setReload(value => value + 1)}>إعادة المحاولة</AdminAction></div>
      : result && counts ? <>
        <AdminStatGrid>
          <AdminStat icon={Users} value={counts.students} label="إجمالي الطلاب" />
          <AdminStat icon={Activity} value={counts.active_accounts} label="حسابات نشطة" />
          <AdminStat icon={BookOpenCheck} value={counts.learning} label="في رحلة الدروس" />
          <AdminStat icon={ShieldCheck} value={counts.completed} label="أكملوا الرحلة" />
        </AdminStatGrid>
        <AdminPanel title="ما الذي يحتاج متابعتك؟" description="عدد القراءات ينتظر القرار؛ لا يُحسب نجاحًا أو إخفاقًا قبل المراجعة.">
          <div className={styles.actionGrid} data-testid="admin-attention-summary">
            {attention.map(item => { const Icon = item.icon; return <Link key={item.label} href={item.href} className={`${styles.actionCard} ${item.value ? styles.priorityCard : ""}`}>
              <span className={styles.actionIcon}><Icon size={22} aria-hidden="true" /></span>
              <span className={styles.actionBody}><strong>{item.value} · {item.label}</strong><small>فتح المتابعة واتخاذ الإجراء المناسب</small></span>
              <ArrowLeft size={18} aria-hidden="true" />
            </Link>; })}
          </div>
        </AdminPanel>
        <AdminPanel title="أحدث الطلاب" description="الدروس المتجاوزة بالتسكين لا تُحتسب إنجازًا. رموز الدخول متاحة عند الحاجة في الحساب فقط."
          actions={<AdminAction href="/admin/students">عرض جميع الطلاب</AdminAction>}>
          {result.recent_students.length === 0 ? <AdminEmptyState title="لا يوجد طلاب حتى الآن" action={<AdminAction href="/admin/students/new">إضافة أول طالب</AdminAction>} />
            : <AdminResponsiveTable table={<table className="data-table" data-testid="admin-v2-students"><thead><tr>
              <th>الطالب</th><th>المستوى</th><th>الدروس</th><th>الخطوة التالية</th><th>الحساب</th>
            </tr></thead><tbody>{result.recent_students.map(student => <tr key={student.id}>
              <td><Link className={styles.studentLink} href={`/admin/students/${student.id}`}>{student.full_name}</Link></td>
              <td>{level(student)}</td><td>{progress(student)}</td><td>{student.current_action.label}</td><td>{student.status === "active" ? "نشط" : "موقوف"}</td>
            </tr>)}</tbody></table>} cards={result.recent_students.map(student => <AdminMobileCard key={student.id} title={<Link href={`/admin/students/${student.id}`}>{student.full_name}</Link>}>
              <span>{level(student)}</span><span>{progress(student)}</span><span>{student.current_action.label}</span>
              <span>{student.status === "active" ? "نشط" : "موقوف"}</span>
            </AdminMobileCard>)} />}
        </AdminPanel>
      </> : null}
  </AdminPage>;
}
