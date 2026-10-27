"use client";
import { useState } from "react";
import { BarChart3, Download } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";
import { useV2Reports } from "@/components/admin/useV2Reports";
import LegacySkillReports from "./LegacySkillReports";
const phases: Record<string, string> = { pretest: "قبلي رسمي", posttest: "بعدي رسمي", learning: "دليل تعلم مصحح" };
export default function SkillReportsPage() {
  const { data, loading, error, refresh } = useV2Reports();
  const [student, setStudent] = useState("");
  const [phase, setPhase] = useState("");
  const [archive, setArchive] = useState(false);
  const items = data?.skills.filter(row => (!student || row.student_id === Number(student)) && (!phase || row.phase === phase)) ?? [];
  return <AdminPage>
    <AdminPageHeader eyebrow="أدلة المهارات · V2" icon={BarChart3} title="ملخص المهارات"
      description="أدلة القبلي والبعدي الرسميين والتعلم المصحح المؤهل فقط. النسب وصفية وليست إعادة حساب للإتقان؛ المعلّق والتلميحات غير المؤهلة لا تتحول إلى إخفاق أو نجاح."
      actions={<AdminAction href="/api/v2/reports/exports/skills.xlsx" icon={Download}>تصدير Excel</AdminAction>} />
    {loading ? <p role="status">جاري تجهيز ملخص المهارات...</p> : error ? <div role="alert" className="alert-error">{error}<AdminAction onClick={refresh}>إعادة المحاولة</AdminAction></div> : data && <AdminPanel>
      <div className="mb-5 flex flex-wrap gap-3"><label className="min-w-0 flex-1">الطالب<select className="input-field mt-2 w-full" value={student} onChange={e => setStudent(e.target.value)}><option value="">جميع الطلاب</option>{data.students.map(row => <option key={row.student_id} value={row.student_id}>{row.student_name}</option>)}</select></label>
        <label className="min-w-0 flex-1">مرحلة الدليل<select className="input-field mt-2 w-full" value={phase} onChange={e => setPhase(e.target.value)}><option value="">جميع المراحل</option>{Object.entries(phases).map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label></div>
      {items.length === 0 ? <AdminEmptyState title="لا توجد أدلة مقيمة مطابقة" /> : <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">{items.map(row => <article className="min-w-0 rounded-xl border border-border p-4" key={`${row.student_id}-${row.phase}-${row.skill_group}`}>
        <h2 className="font-bold text-navy">{data.students.find(student => student.student_id === row.student_id)?.student_name} · {row.skill_group}</h2>
        <p className="my-2 text-sm text-muted">{phases[row.phase] ?? row.phase}</p><p>{row.correct} من {row.graded} استجابة مصححة · {row.observed_accuracy_percent}% دقة مرصودة</p>
      </article>)}</div>}
    </AdminPanel>}
    <AdminAction onClick={() => setArchive(value => !value)}>{archive ? "إغلاق أرشيف مهارات V1" : "أرشيف مهارات V1"}</AdminAction>
    {archive && <section aria-label="أرشيف مهارات V1"><LegacySkillReports /></section>}
  </AdminPage>;
}
