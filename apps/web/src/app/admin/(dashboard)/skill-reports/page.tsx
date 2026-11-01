"use client";
import { useMemo, useState } from "react";
import { BarChart3, Download } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";
import { useV2Reports } from "@/components/admin/useV2Reports";

const phases: Record<string, string> = { pretest: "قبلي رسمي", posttest: "بعدي رسمي", learning: "دليل تعلم مصحح" };
const PAGE_SIZE = 24;

export default function SkillReportsPage() {
  const { data, loading, error, refresh } = useV2Reports();
  const [student, setStudent] = useState("");
  const [phase, setPhase] = useState("");
  const [page, setPage] = useState(0);
  const studentNames = useMemo(() => new Map(data?.students.map(row => [row.student_id, row.student_name]) ?? []), [data]);
  const items = useMemo(() => data?.skills.filter(row =>
    (!student || row.student_id === Number(student)) && (!phase || row.phase === phase)
  ) ?? [], [data, student, phase]);
  const pageCount = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount - 1);
  const visible = items.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE);
  const filtered = Boolean(student || phase);
  const resetFilters = () => { setStudent(""); setPhase(""); setPage(0); };
  return <AdminPage>
    <AdminPageHeader eyebrow="أدلة المهارات" icon={BarChart3} title="ملخص المهارات"
      description="نتائج الأدلة المقيمة من الاختبارات الرسمية والدروس. لا تُعد الإجابات المعلقة إخفاقًا أو نجاحًا، ولا تعني النسبة إثبات الإتقان."
      actions={<AdminAction href="/api/v2/reports/exports/skills.xlsx" icon={Download}>تصدير Excel</AdminAction>} />
    {loading ? <p role="status">جاري تجهيز ملخص المهارات...</p> : error ? <div role="alert" className="alert-error">{error}<AdminAction onClick={refresh}>إعادة المحاولة</AdminAction></div> : data && <AdminPanel>
      <div className="mb-5 flex flex-wrap gap-3">
        <label className="min-w-0 flex-1">الطالب
          <select className="input-field mt-2 w-full" value={student} onChange={e => { setStudent(e.target.value); setPage(0); }}>
            <option value="">جميع الطلاب</option>{data.students.map(row => <option key={row.student_id} value={row.student_id}>{row.student_name}</option>)}
          </select>
        </label>
        <label className="min-w-0 flex-1">مرحلة الدليل
          <select className="input-field mt-2 w-full" value={phase} onChange={e => { setPhase(e.target.value); setPage(0); }}>
            <option value="">جميع المراحل</option>{Object.entries(phases).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
          </select>
        </label>
      </div>
      <p className="mb-4 text-sm text-muted" aria-live="polite">{items.length} نتيجة مهارة مطابقة</p>
      {items.length === 0 ? <AdminEmptyState
        title={filtered ? "لا توجد أدلة مطابقة للتصفية" : "لا توجد أدلة مقيمة بعد"}
        description={filtered ? "يمكنك اختيار طالب أو مرحلة أخرى لعرض النتائج." : "ستظهر النتائج بعد اعتماد الإجابات المؤهلة."}
        action={filtered ? <AdminAction onClick={resetFilters}>مسح التصفية</AdminAction> : undefined}
      /> : <>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3" data-testid="skill-report-grid">
          {visible.map(row => <article className="min-w-0 rounded-xl border border-border p-4" key={`${row.student_id}-${row.phase}-${row.skill_group}`}>
            <h2 className="font-bold text-navy">{studentNames.get(row.student_id) ?? "طالب غير متاح"} · {row.skill_group}</h2>
            <p className="my-2 text-sm text-muted">{phases[row.phase] ?? "مرحلة غير معروفة"}</p>
            <p>{row.correct} من {row.graded} استجابة مصححة · {row.observed_accuracy_percent}% دقة مرصودة</p>
          </article>)}
        </div>
        {items.length > PAGE_SIZE && <nav aria-label="صفحات تقارير المهارات" className="mt-5 flex flex-wrap items-center justify-between gap-3">
          <button type="button" className="min-h-11 rounded-xl border border-border px-4 disabled:opacity-40"
            disabled={currentPage === 0} onClick={() => setPage(value => Math.max(0, value - 1))}>السابق</button>
          <span aria-live="polite" className="text-sm text-muted">
            {currentPage * PAGE_SIZE + 1}–{Math.min(items.length, (currentPage + 1) * PAGE_SIZE)} من {items.length}
          </span>
          <button type="button" className="min-h-11 rounded-xl border border-border px-4 disabled:opacity-40"
            disabled={currentPage + 1 >= pageCount} onClick={() => setPage(value => value + 1)}>التالي</button>
        </nav>}
      </>}
    </AdminPanel>}
  </AdminPage>;
}
