"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Eye, Search, UserPlus, Users } from "lucide-react";
import {
  AdminAction, AdminEmptyState, AdminMobileCard, AdminPage, AdminPageHeader,
  AdminPanel, AdminResponsiveTable, AdminToolbar,
} from "@/components/admin/AdminUI";

type StudentListItem = {
  id: number;
  full_name: string;
  grade_level: number;
  created_at: string;
  status: "active" | "inactive";
  journey: { current_level: number; placement_state: string; current_lesson_id: string | null } | null;
  current_action: { action: string; label: string; state?: string | null };
  progress: {
    completed_lessons: number;
    assigned_lessons: number | null;
    skipped_by_placement: number;
    pending_review: number;
    display_percent: number | null;
  };
  data_status: "ready" | "partial" | "unavailable";
};
type Cohort = {
  source: "himma_v2_readmodel";
  total: number;
  offset: number;
  limit: number;
  items: StudentListItem[];
};
const PAGE_SIZE = 30;

function statusLabel(student: StudentListItem) {
  if (student.current_action.action === "migration_review") return "انتقال للمشرف";
  if (student.current_action.action === "start_pretest") return "بانتظار القبلي";
  if (student.current_action.state === "waiting_review") return "بانتظار مراجعة القراءة";
  if (student.current_action.state === "placement_pending_review") return "جارٍ تحديد المستوى تلقائيًا";
  if (student.current_action.action === "complete") return "أكمل الرحلة";
  return student.current_action.label;
}
function progressLabel(student: StudentListItem) {
  if (student.data_status !== "ready" || student.progress.display_percent == null || student.progress.assigned_lessons == null)
    return "لم يُعتمد تقدم الدروس بعد";
  return `${student.progress.completed_lessons} / ${student.progress.assigned_lessons} درس (${student.progress.display_percent}%)`;
}

export default function StudentsPage() {
  const [data, setData] = useState<Cohort | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<"all" | "active" | "inactive">("all");
  const [offset, setOffset] = useState(0);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({
      limit: String(PAGE_SIZE), offset: String(offset), search, status,
    });
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`/api/v2/student/admin/students/overview?${params}`, {
          cache: "no-store", signal: controller.signal,
        });
        if (!response.ok) throw new Error("تعذر تحميل تقدم الطلاب.");
        const payload = await response.json() as Cohort;
        if (payload.source !== "himma_v2_readmodel" || !Array.isArray(payload.items))
          throw new Error("مصدر بيانات الطلاب غير متطابق مع V2.");
        if (!controller.signal.aborted) setData(payload);
      } catch (reason) {
        if (!controller.signal.aborted) {
          setData(null);
          setError(reason instanceof Error ? reason.message : "تعذر الاتصال بالخادم.");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    void load();
    return () => controller.abort();
  }, [offset, reload, search, status]);

  const items = data?.items ?? [];
  const count = data?.total ?? 0;

  return <AdminPage>
    <AdminPageHeader eyebrow="إدارة الطلاب" icon={Users} title="الطلاب"
      description="تابع حالة الاختبارات والتسكين والدروس لكل طالب، وافتح ملفه للإجراءات والتفاصيل."
      actions={<AdminAction href="/admin/students/new" tone="primary" icon={UserPlus}>إضافة طالب</AdminAction>} />
    <AdminPanel>
      <AdminToolbar>
        <label className="relative flex-1 min-w-0">
          <span className="sr-only">البحث عن طالب بالاسم</span>
          <input className="input-field pr-11" value={search}
            onChange={(event) => { setOffset(0); setSearch(event.target.value); }}
            placeholder="ابحث باسم الطالب" />
          <Search size={18} className="absolute right-4 top-1/2 -translate-y-1/2 text-muted" aria-hidden="true" />
        </label>
        <select className="input-field" style={{ maxWidth: 190 }} value={status}
          onChange={(event) => { setOffset(0); setStatus(event.target.value as typeof status); }}
          aria-label="تصفية حسب حالة الحساب">
          <option value="all">كل الحالات</option><option value="active">نشط</option><option value="inactive">موقوف</option>
        </select>
        <span className="rounded-xl bg-white border border-border px-4 min-h-11 flex items-center justify-center text-sm text-muted whitespace-nowrap">{loading ? "جارٍ التحميل" : `${count} طالب`}</span>
      </AdminToolbar>
      {error && <div className="alert-error mt-3" role="alert">{error} <button type="button" className="underline font-semibold" onClick={() => setReload(value => value + 1)}>إعادة المحاولة</button></div>}
      <div style={{ height: 14 }} />
      {loading
        ? <div className="flex flex-col items-center justify-center gap-3 py-14"><div className="spinner w-9 h-9" /><p className="text-muted">جاري تحميل بيانات الطلاب...</p></div>
        : !data ? null
        : count === 0 ? <AdminEmptyState title="لا توجد نتائج" description="لا يوجد طالب مطابق لهذه التصفية، أو لم تُضف العينة بعد." action={<AdminAction href="/admin/students/new" tone="primary" icon={UserPlus}>إضافة طالب</AdminAction>} />
        : <AdminResponsiveTable
          table={<table className="data-table"><thead><tr>
            <th>الطالب</th><th>الحساب</th><th>المستوى</th><th>التقدم</th><th>الخطوة التالية</th><th>الملف</th>
          </tr></thead><tbody>{items.map(student => <tr key={student.id}>
            <td><Link href={`/admin/students/${student.id}`} className="font-semibold text-navy hover:text-primary">{student.full_name}</Link></td>
            <td><span className={`badge ${student.status === "active" ? "badge-green" : "badge-gray"}`}>{student.status === "active" ? "نشط" : "موقوف"}</span></td>
            <td>{student.journey && ["placed", "posttest_ready", "completed"].includes(student.journey.placement_state) ? `المستوى ${student.journey.current_level}` : "لم يُعتمد بعد"}</td>
            <td><span>{progressLabel(student)}</span></td>
            <td>{statusLabel(student)}</td>
            <td><Link href={`/admin/students/${student.id}`} className="inline-flex items-center gap-2 text-primary font-semibold text-sm p-2 rounded-md hover:bg-primary/10"><Eye size={18} /> فتح</Link></td>
          </tr>)}</tbody></table>}
          cards={items.map(student => <AdminMobileCard key={student.id} title={<Link href={`/admin/students/${student.id}`}>{student.full_name}</Link>}>
            <span><strong>الحساب:</strong> {student.status === "active" ? "نشط" : "موقوف"}</span>
            <span><strong>المستوى:</strong> {student.journey && ["placed", "posttest_ready", "completed"].includes(student.journey.placement_state) ? student.journey.current_level : "لم يُعتمد بعد"}</span>
            <span><strong>التقدم:</strong> {progressLabel(student)}</span>
            <span><strong>الخطوة:</strong> {statusLabel(student)}</span>
            <span><AdminAction href={`/admin/students/${student.id}`} icon={Eye}>فتح الملف</AdminAction></span>
          </AdminMobileCard>)} />}
      {!loading && data && count > PAGE_SIZE && <div className="flex justify-between gap-3 pt-5">
        <button type="button" className="btn-secondary" disabled={offset === 0} onClick={() => setOffset(v => Math.max(0, v - PAGE_SIZE))}>السابق</button>
        <span className="text-sm text-muted self-center">{offset + 1}–{Math.min(offset + PAGE_SIZE, count)} من {count}</span>
        <button type="button" className="btn-secondary" disabled={offset + PAGE_SIZE >= count} onClick={() => setOffset(v => v + PAGE_SIZE)}>التالي</button>
      </div>}
    </AdminPanel>
  </AdminPage>;
}
