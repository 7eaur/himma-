"use client";
import { useMemo, useState } from "react";
import Link from "next/link";
import { BarChart3, CheckCircle2, FileSpreadsheet, FileText, RefreshCw, Users } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminMobileCard, AdminPage, AdminPageHeader, AdminPanel, AdminResponsiveTable, AdminStat, AdminStatGrid } from "@/components/admin/AdminUI";
import { useV2Reports } from "@/components/admin/useV2Reports";
const score = (value: number | null | undefined) => value == null ? "—" : `${value}%`;
const PAGE_SIZE = 20;
export default function ReportsPage() {
  const { data, loading, error, refresh } = useV2Reports();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const students = useMemo(() => data?.students.filter(row =>
    `${row.student_name} ${row.student_id}`.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase())) ?? [], [data, search]);
  const pageCount = Math.max(1, Math.ceil(students.length / PAGE_SIZE));
  const effectivePage = Math.min(page, pageCount - 1);
  const visibleStudents = students.slice(effectivePage * PAGE_SIZE, (effectivePage + 1) * PAGE_SIZE);
  return <AdminPage>
    <AdminPageHeader eyebrow="النتائج المعتمدة" icon={BarChart3} title="التقارير والإحصائيات"
      description="القبلي والبعدي الرسميان وتقدم الدروس والدعم؛ النتائج المعلقة لا تدخل في المقارنة، والتسكين يؤخذ من القرار المحفوظ."
      actions={<><AdminAction href="/api/v2/reports/exports/cohort.xlsx" icon={FileSpreadsheet}>Excel</AdminAction><AdminAction href="/api/v2/reports/exports/cohort.pdf" icon={FileText}>PDF إجمالي</AdminAction><AdminAction disabled={loading} onClick={refresh} icon={RefreshCw}>تحديث</AdminAction></>} />
    {loading ? <p role="status" className="py-8">جاري تجهيز التقارير...</p> : error ? <div role="alert" className="alert-error">{error} <AdminAction onClick={refresh}>إعادة المحاولة</AdminAction></div> : data && <>
      <AdminStatGrid><AdminStat icon={Users} value={data.summary.students} label="إجمالي الطلاب" /><AdminStat icon={CheckCircle2} value={data.summary.official_pretests} label="قبلي معتمد" /><AdminStat icon={CheckCircle2} value={data.summary.official_posttests} label="بعدي معتمد" /><AdminStat icon={BarChart3} value={data.summary.average_improvement_points == null ? "—" : `${data.summary.average_improvement_points} نقطة`} label="متوسط التحسن للمقارنات المعتمدة" /></AdminStatGrid>
      <AdminPanel title="نتائج الطلاب" description="التحسن = البعدي − القبلي، بشرط تطابق إصدار البنك. لا تحسن نسبي عندما القبلي صفر، ولا تقدم وهمي للدروس المتجاوزة بالتسكين.">
        <label className="mb-4 block max-w-md text-sm font-semibold">بحث عن طالب أو معرّف
          <input className="input-field mt-2 w-full" value={search} onChange={event => { setSearch(event.target.value); setPage(0); }} />
        </label>
        {students.length === 0 ? <AdminEmptyState title={data.students.length ? "لا توجد نتائج مطابقة" : "لا توجد حسابات بعد"} /> : <AdminResponsiveTable table={<table className="data-table" data-testid="v2-report-table"><thead><tr><th>الطالب</th><th>القبلي</th><th>البعدي</th><th>التحسن</th><th>الدروس</th><th>الدعم</th><th>التقرير</th></tr></thead><tbody>{visibleStudents.map(row => <tr key={row.student_id}>
          <td><Link className="font-semibold text-primary" href={`/admin/students/${row.student_id}`}>{row.student_name}</Link></td><td>{score(row.pretest?.score)}</td><td>{score(row.posttest?.score)}</td>
          <td>{row.improvement_points == null ? row.comparison_state === "release_mismatch" ? "إصداران مختلفان" : "بانتظار الاعتماد" : `${row.improvement_points} نقطة`}</td>
          <td>{row.progress.assigned_lessons == null ? "غير معتمد" : `${row.progress.completed_lessons} / ${row.progress.assigned_lessons}`}</td><td>{row.support.resolved} / {row.support.total}</td>
          <td><a href={`/api/v2/reports/students/${row.student_id}/export.pdf`} className="font-semibold text-primary">PDF فردي</a></td>
        </tr>)}</tbody></table>} cards={visibleStudents.map(row => <AdminMobileCard key={row.student_id} title={<Link href={`/admin/students/${row.student_id}`}>{row.student_name}</Link>}>
          <span>قبلي: {score(row.pretest?.score)} · بعدي: {score(row.posttest?.score)}</span><span>التحسن: {row.improvement_points == null ? "غير متاح" : `${row.improvement_points} نقطة`}</span>
          <span>دروس: {row.progress.assigned_lessons == null ? "غير معتمد" : `${row.progress.completed_lessons} / ${row.progress.assigned_lessons}`}</span><span>الدعم: {row.support.resolved} / {row.support.total} · معلّق: {row.pending_assessment_reviews}</span>
          <AdminAction href={`/api/v2/reports/students/${row.student_id}/export.pdf`}>PDF فردي</AdminAction>
        </AdminMobileCard>)} />}
        {students.length > PAGE_SIZE && <nav aria-label="صفحات نتائج الطلاب" className="mt-4 flex items-center justify-between gap-3 text-sm">
          <button type="button" className="min-h-11 rounded-xl border px-4 disabled:opacity-40" disabled={effectivePage === 0} onClick={() => setPage(value => Math.max(0, value - 1))}>السابق</button>
          <span aria-live="polite">{effectivePage * PAGE_SIZE + 1}–{Math.min(students.length, (effectivePage + 1) * PAGE_SIZE)} من {students.length}</span>
          <button type="button" className="min-h-11 rounded-xl border px-4 disabled:opacity-40" disabled={effectivePage + 1 >= pageCount} onClick={() => setPage(value => value + 1)}>التالي</button>
        </nav>}
      </AdminPanel>
    </>}
  </AdminPage>;
}
