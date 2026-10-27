"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CheckCircle2, Headphones, RefreshCcw } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";

type Reviewed = {
  audio_id: number; response_id: number; student_id: number; student_name: string;
  question_id: string; lesson_id: string | null; kind: "lesson" | "pretest" | "posttest";
  is_correct: boolean | null; reviewed_at: string | null;
  duration_seconds: number | null; evaluation_source: "supervisor";
  audio_url: string;
  reading_rubric?: {
    target_units: number; deletions: number; substitutions: number; insertions: number;
    rubric_percent: number; is_correct: boolean; pronunciation_notes: string | null;
    fluency_notes: string | null; policy_version: string;
  } | null;
};
type Archive = { items: Reviewed[]; next_offset: number | null };

const kinds = [
  { value: "all", label: "جميع تسجيلات القراءة" },
  { value: "lesson", label: "تسجيلات الدروس" },
  { value: "pretest", label: "الاختبار القبلي" },
  { value: "posttest", label: "الاختبار البعدي" },
] as const;

export default function ReviewedRecordingsPage() {
  const [archive, setArchive] = useState<Archive>({ items: [], next_offset: null });
  const [kind, setKind] = useState("all");
  const [offset, setOffset] = useState(0);
  const [student, setStudent] = useState(() => {
    if (typeof window === "undefined") return "";
    const value = new URLSearchParams(window.location.search).get("student_id");
    return value && /^[1-9]\d*$/.test(value) ? value : "";
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const requestSequence = useRef(0);

  const refresh = useCallback(async () => {
    const requestId = ++requestSequence.current;
    setError("");
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: "20", offset: String(offset), kind });
      if (student && Number(student) > 0) params.set("student_id", String(Number(student)));
      const response = await fetch(`/api/v2/review/reviewed-recordings?${params.toString()}`, { cache: "no-store" });
      const body = await response.json().catch(() => null);
      // Ignore late responses from an older student or activity filter.
      if (requestId !== requestSequence.current) return;
      if (!response.ok) throw new Error(body?.detail || "تعذر تحميل التسجيلات المنتهية");
      if (!body || !Array.isArray(body.items) ||
          (body.next_offset !== null && (!Number.isSafeInteger(body.next_offset) || body.next_offset < 0))) {
        throw new Error("استجابة التسجيلات المقيّمة غير صالحة");
      }
      setArchive(body as Archive);
    } catch (cause) {
      if (requestId !== requestSequence.current) return;
      // Never display an old child's voice after a failed filter or refresh.
      setArchive({ items: [], next_offset: null });
      setError(cause instanceof Error ? cause.message : "تعذر تحميل التسجيلات");
    } finally {
      if (requestId === requestSequence.current) setLoading(false);
    }
  }, [kind, offset, student]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void refresh(); }, 0);
    return () => {
      window.clearTimeout(timer);
      requestSequence.current += 1;
    };
  }, [refresh]);

  return <AdminPage>
    <AdminPageHeader eyebrow="مراجعة الصوت" title="التسجيلات التي اكتمل تقييمها"
      icon={Headphones}
      description="آخر تسجيل مُعتمد لكل سؤال قراءة، منفصل عن طابور انتظار المراجعة. تقييم الصوت المعروض حاليًا من المشرف، وليس من الذكاء الاصطناعي."
      actions={<AdminAction icon={RefreshCcw} onClick={() => void refresh()}>تحديث</AdminAction>} />
    <AdminPanel title="البحث والتصفية" description="لا تظهر التسجيلات المعلقة أو المحاولات الصوتية المستبدلة.">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="grid gap-1 text-sm font-semibold">نوع النشاط
          <select className="rounded-xl border border-slate-300 p-3" value={kind}
            onChange={event => { setKind(event.target.value); setOffset(0); }}>
            {kinds.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>
        <label className="grid gap-1 text-sm font-semibold">رقم الطالب (اختياري)
          <input type="number" min={1} value={student} className="rounded-xl border border-slate-300 p-3"
            placeholder="كل الطلاب" onChange={event => { setStudent(event.target.value); setOffset(0); }} />
        </label>
      </div>
    </AdminPanel>
    <AdminPanel title="التسجيلات المقيّمة" description="آخر تسجيل معتمد لكل نشاط، مع حفظ الخصوصية ودون رابط تخزين مباشر.">
      {error && <p role="alert" className="alert-error">{error}</p>}
      {loading ? <p role="status">جاري جلب التسجيلات...</p>
        : error ? <AdminEmptyState title="تعذر عرض التسجيلات" description="لم نعرض بيانات مخزنة قديمة. اختر تحديث لإعادة المحاولة." />
        : archive.items.length === 0 ? <AdminEmptyState title="لا توجد تسجيلات مقيّمة لهذه التصفية" description="ستظهر هنا بعد اعتماد تقييم المشرف للصوت." />
        : <div className="space-y-3">{archive.items.map(item => <article key={item.audio_id} className="space-y-3 rounded-2xl border border-slate-200 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div><strong className="text-navy">{item.student_name} · {item.question_id}</strong>
              <p className="text-sm text-muted">طالب #{item.student_id} · {item.kind === "lesson" ? `درس ${item.lesson_id || "—"}` : item.kind === "pretest" ? "اختبار قبلي" : "اختبار بعدي"}</p>
            </div>
            <span className="inline-flex items-center gap-1 text-sm font-semibold text-slate-700"><CheckCircle2 size={17} aria-hidden="true" /> تم تقييمه بواسطة المشرف</span>
          </div>
          <p className="text-sm">النتيجة: <strong>{item.is_correct === true ? "مستوفٍ" : item.is_correct === false ? "يحتاج تقوية" : "غير محدد"}</strong>
            {item.reviewed_at ? ` · بتاريخ ${new Date(item.reviewed_at).toLocaleDateString("ar")}` : ""}
            {item.duration_seconds != null ? ` · ${Math.round(item.duration_seconds)} ثانية` : ""}
          </p>
          {item.reading_rubric && <details className="rounded-xl border border-teal-200 p-3">
            <summary className="cursor-pointer font-semibold text-slate-800">تفاصيل التقييم الصوتي</summary>
            <div className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
              <p>الوحدات: <strong>{item.reading_rubric.target_units}</strong></p>
              <p>حذف: <strong>{item.reading_rubric.deletions}</strong></p>
              <p>استبدال: <strong>{item.reading_rubric.substitutions}</strong></p>
              <p>إضافة: <strong>{item.reading_rubric.insertions}</strong></p>
            </div>
            <p className="mt-2 text-sm">التقدير الرقمي الوصفي: {item.reading_rubric.rubric_percent}% — لا يحدد وحده نجاح القراءة.</p>
            {item.reading_rubric.pronunciation_notes && <p className="mt-2 text-sm">النطق: {item.reading_rubric.pronunciation_notes}</p>}
            {item.reading_rubric.fluency_notes && <p className="mt-2 text-sm">الطلاقة: {item.reading_rubric.fluency_notes}</p>}
          </details>}
          <audio controls preload="none" className="w-full" src={item.audio_url} aria-label={`استمع لتسجيل ${item.student_name} للسؤال ${item.question_id}`} />
        </article>)}</div>}
      <div className="mt-4 flex items-center justify-between gap-2">
        <button type="button" className="rounded-xl border px-4 py-2 disabled:opacity-40" disabled={offset === 0 || loading}
          onClick={() => setOffset(Math.max(0, offset - 20))}>السابق</button>
        <span className="text-sm text-muted">{archive.items.length ? `عرض ${offset + 1} إلى ${offset + archive.items.length}` : "—"}</span>
        <button type="button" className="rounded-xl border px-4 py-2 disabled:opacity-40" disabled={archive.next_offset === null || loading}
          onClick={() => setOffset(archive.next_offset || 0)}>التالي</button>
      </div>
    </AdminPanel>
  </AdminPage>;
}
