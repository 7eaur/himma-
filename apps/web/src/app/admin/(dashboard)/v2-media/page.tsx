"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Film, LoaderCircle } from "lucide-react";
import { AdminPage, AdminPageHeader } from "@/components/admin/AdminUI";

interface MediaItem { asset_id: string; kind: string; state: "ready" | "pending" | "missing"; runtime_state: string; test_only: boolean; source_status: string; }
interface Inventory { mode: "read_only"; release_state: string; counts: { ready: number; pending: number; missing: number; test_only: number }; items: MediaItem[]; }

const STATE_LABELS = { ready: "جاهز", pending: "بانتظار المراجعة", missing: "مفقود" };

export default function V2MediaInventoryPage() {
  const [inventory, setInventory] = useState<Inventory | null>(null);
  const [filter, setFilter] = useState<"all" | MediaItem["state"]>("all");
  const [error, setError] = useState("");
  useEffect(() => { void fetch("/api/v2/lessons/admin/media-inventory", { cache:"no-store" }).then(async (response) => { const data = await response.json().catch(() => null); if (!response.ok) throw new Error(data?.detail || "تعذر تحميل سجل الوسائط"); setInventory(data); }).catch((reason) => setError(reason instanceof Error ? reason.message : "تعذر تحميل سجل الوسائط")); }, []);
  const items = useMemo(() => inventory?.items.filter((item) => filter === "all" || item.state === filter) ?? [], [filter, inventory]);
  return <AdminPage>
    <AdminPageHeader eyebrow="P03 · قراءة فقط" icon={Film} title="سجل وسائط V2" description="يعرض الجاهز والمنتظر والمفقود من المصدر المعتمد. ملفات TEST ONLY لا تغيّر حالة الاعتماد." />
    {error && <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-800">{error}</div>}
    {!inventory && !error && <div role="status" className="flex min-h-56 items-center justify-center gap-3 text-slate-500"><LoaderCircle className="animate-spin" /> جاري تحميل الوسائط...</div>}
    {inventory && <>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {(["ready","pending","missing","test_only"] as const).map((key) => <article key={key} className="rounded-2xl border border-slate-200 bg-white p-4"><span className="text-xs font-bold text-slate-500">{key === "test_only" ? "بدائل اختبارية" : STATE_LABELS[key]}</span><strong className="mt-2 block text-3xl text-slate-800">{inventory.counts[key]}</strong></article>)}
      </div>
      <div className="mt-4 flex flex-wrap gap-2" aria-label="تصفية الوسائط">{(["all","ready","pending","missing"] as const).map((value) => <button key={value} type="button" aria-pressed={filter === value} onClick={() => setFilter(value)} className={`rounded-full border px-4 py-2 text-sm font-bold ${filter === value ? "border-blue-500 bg-blue-50 text-blue-700" : "border-slate-200 bg-white text-slate-600"}`}>{value === "all" ? "الكل" : STATE_LABELS[value]}</button>)}</div>
      <div className="mt-4 overflow-x-auto rounded-2xl border border-slate-200 bg-white"><table className="w-full min-w-[680px] text-right text-sm"><thead className="bg-slate-50 text-slate-600"><tr><th className="p-3">المعرّف</th><th className="p-3">النوع</th><th className="p-3">حالة المصدر</th><th className="p-3">حالة المعاينة</th></tr></thead><tbody>{items.map((item) => <tr key={item.asset_id} className="border-t border-slate-100"><td className="p-3 font-mono text-xs">{item.asset_id}</td><td className="p-3">{item.kind}</td><td className="p-3"><span className="inline-flex items-center gap-1 font-bold">{item.state === "ready" ? <CheckCircle2 size={15} className="text-emerald-600"/> : <AlertTriangle size={15} className="text-amber-600"/>}{STATE_LABELS[item.state]}</span><small className="mt-1 block text-slate-400">{item.source_status}</small></td><td className="p-3">{item.test_only ? <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-bold text-amber-800">TEST ONLY</span> : item.runtime_state}</td></tr>)}</tbody></table></div>
    </>}
  </AdminPage>;
}
