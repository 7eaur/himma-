"use client";

import { useCallback, useEffect, useState } from "react";
import { BarChart3, ClipboardCheck, Clock3, RefreshCw } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel, AdminStat, AdminStatGrid } from "@/components/admin/AdminUI";

interface QueueItem { response_id: number; session_id: number; question_id: string; kind: string; skill_group: string; evidence_type: string; submitted_at: string; }
interface Report { counts: Record<string, number>; averages: { pretest: number | null; posttest: number | null }; missing_policy: string; }

export default function V2AssessmentsPage() {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const load = useCallback(async () => {
    setError("");
    try {
      const [queueResponse, reportResponse] = await Promise.all([
        fetch("/api/v2/assessments/admin/review-queue", { cache: "no-store" }),
        fetch("/api/v2/assessments/admin/reports/summary", { cache: "no-store" }),
      ]);
      const queue = await queueResponse.json().catch(() => null); const summary = await reportResponse.json().catch(() => null);
      if (!queueResponse.ok || !reportResponse.ok) throw new Error(queue?.detail || summary?.detail || "تعذر تحميل تقييمات V2");
      setItems(queue.items); setReport(summary);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر تحميل تقييمات V2"); }
  }, []);
  useEffect(() => { const timer = window.setTimeout(() => { void load(); }, 0); return () => window.clearTimeout(timer); }, [load]);

  const review = async (id: number, isCorrect: boolean) => {
    const note = window.prompt("سبب القرار (مطلوب في سجل التدقيق):");
    if (!note || note.trim().length < 2) return;
    setBusy(id); setError("");
    try {
      const response = await fetch(`/api/v2/assessments/admin/responses/${id}/review`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_correct: isCorrect, note }) });
      const data = await response.json().catch(() => null); if (!response.ok) throw new Error(data?.detail || "تعذر حفظ المراجعة");
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "تعذر حفظ المراجعة"); } finally { setBusy(null); }
  };

  const place = async (sessionId: number) => {
    const rawLevel = window.prompt("المستوى المعتمد: 1 أو 2 أو 3"); const level = Number(rawLevel);
    if (![1, 2, 3].includes(level)) return;
    const reason = window.prompt("سبب التسكين المفصل (10 أحرف على الأقل):"); if (!reason || reason.trim().length < 10) return;
    setBusy(-sessionId);
    try {
      const response = await fetch(`/api/v2/assessments/admin/sessions/${sessionId}/placement`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ assigned_level: level, reason }) });
      const data = await response.json().catch(() => null); if (!response.ok) throw new Error(data?.detail || "تعذر اعتماد التسكين");
      await load();
    } catch (reasonValue) { setError(reasonValue instanceof Error ? reasonValue.message : "تعذر اعتماد التسكين"); } finally { setBusy(null); }
  };

  const pendingPlacement = Object.entries(report?.counts ?? {}).find(([key]) => key === "pretest:placement_pending_review")?.[1] ?? 0;
  return <AdminPage>
    <AdminPageHeader eyebrow="P06 · سياسة مرشحة" icon={ClipboardCheck} title="تقييمات V2 والمراجعة" description="قائمة فعلية لإجابات القراءة والكتابة، وتسكين يدوي مسبب. لا توجد حدود تسكين آلية قبل اعتماد المعايرة التربوية." actions={<AdminAction icon={RefreshCw} onClick={() => void load()}>تحديث</AdminAction>}/>
    {error && <div className="alert-error" role="alert">{error}</div>}
    {report && <AdminStatGrid><AdminStat icon={Clock3} value={items.length} label="إجابات تنتظر المراجعة"/><AdminStat icon={ClipboardCheck} value={pendingPlacement} label="جلسات تنتظر التسكين"/><AdminStat icon={BarChart3} value={report.averages.pretest ?? "—"} label="متوسط القبلي المكتمل"/><AdminStat icon={BarChart3} value={report.averages.posttest ?? "—"} label="متوسط البعدي المكتمل"/></AdminStatGrid>}
    <AdminPanel title="طابور المراجعة البشرية" description="النتيجة تبقى محايدة حتى هذا القرار. افتح تسجيل القراءة من صفحة مراجعة التسجيلات عند الحاجة.">
      {items.length === 0 ? <AdminEmptyState title="لا توجد إجابات معلقة" description="ستظهر هنا إجابات القراءة والكتابة من التقييمين."/> : <div className="space-y-3">{items.map((item) => <article key={item.response_id} className="rounded-2xl border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><strong className="text-navy">{item.question_id}</strong><p className="text-sm text-muted">{item.kind === "pretest" ? "قبلي" : "بعدي"} · {item.skill_group} · {item.evidence_type} · جلسة {item.session_id}</p></div><div className="flex flex-wrap gap-2"><button disabled={busy === item.response_id} onClick={() => void review(item.response_id, true)} className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-bold text-white">مستوفٍ</button><button disabled={busy === item.response_id} onClick={() => void review(item.response_id, false)} className="rounded-xl bg-rose-600 px-4 py-2 text-sm font-bold text-white">غير مستوفٍ</button></div></div></article>)}</div>}
    </AdminPanel>
    {pendingPlacement > 0 && <AdminPanel title="اعتماد التسكين" description="أدخل رقم جلسة قبلية أصبحت في حالة انتظار التسكين بعد مراجعة جميع أدلتها."><form className="flex flex-wrap gap-2" onSubmit={(event) => { event.preventDefault(); const value = Number(new FormData(event.currentTarget).get("sessionId")); if (value > 0) void place(value); }}><input name="sessionId" type="number" min="1" required aria-label="رقم الجلسة" className="rounded-xl border border-slate-300 px-3 py-2" placeholder="رقم الجلسة"/><button type="submit" disabled={busy !== null} className="rounded-xl bg-blue-700 px-4 py-2 font-bold text-white">مراجعة واعتماد المستوى</button></form></AdminPanel>}
    <p className="text-sm text-muted">القيم المفقودة تظهر «—» ولا تُعامل كصفر. المتوسطات تشمل الجلسات الرسمية المكتملة فقط.</p>
  </AdminPage>;
}
