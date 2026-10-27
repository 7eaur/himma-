"use client";

import { useEffect, useMemo, useState } from "react";
import { Film } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";
import EducationalMediaPreview from "@/components/admin/EducationalMediaPreview";

interface MediaItem { asset_id: string; kind: string; state: "ready" | "pending" | "missing"; runtime_state: string; test_only: boolean; temporary: boolean; source_status: string; candidate_present: boolean; preview_url: string | null; preview_kind: string; publication_blocker: boolean; uses: { owner_id: string; role: string }[]; }
interface Inventory { mode: "read_only"; release_state: string; counts: { ready: number; pending: number; missing: number; test_only: number; temporary: number }; items: MediaItem[]; candidate_files_present: number; published_assets: number; required_assets: number; publishable: boolean; }
const states = { ready: "جاهز", pending: "بانتظار المراجعة", missing: "مفقود" };
const kinds: Record<string, string> = { audio: "صوت", video: "فيديو", image: "صورة" };

export default function V2MediaInventoryPage() {
  const [inventory, setInventory] = useState<Inventory | null>(null);
  const [filter, setFilter] = useState<"all" | MediaItem["state"]>("all");
  const [kind, setKind] = useState("all");
  const [search, setSearch] = useState("");
  const [reload, setReload] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      setLoading(true); setError("");
      try {
        const response = await fetch("/api/v2/lessons/admin/media-inventory", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("تعذر تحميل سجل الوسائط");
        const data = await response.json() as Inventory;
        if (data.mode !== "read_only" || !Array.isArray(data.items)) throw new Error("عقد الوسائط غير متطابق");
        if (!controller.signal.aborted) setInventory(data);
      } catch (cause) { if (!controller.signal.aborted) { setInventory(null); setError(cause instanceof Error ? cause.message : "تعذر تحميل الوسائط"); } }
      finally { if (!controller.signal.aborted) setLoading(false); }
    };
    void load(); return () => controller.abort();
  }, [reload]);
  const items = useMemo(() => inventory?.items.filter(item => (filter === "all" || item.state === filter)
    && (kind === "all" || item.kind === kind)
    && (!search.trim() || `${item.asset_id} ${item.uses.map(ref => ref.owner_id).join(" ")}`.toLowerCase().includes(search.trim().toLowerCase()))) ?? [], [filter, kind, search, inventory]);
  return <AdminPage>
    <AdminPageHeader eyebrow="المحتوى والوسائط" icon={Film} title="الوسائط التعليمية"
      description="معرض الأصول التعليمية والصوت والصورة والفيديو. التشغيل للمعاينة فقط، ولا يمنح اعتمادًا أو يغير تقدم الطالب." />
    {loading ? <p role="status" className="py-8">جاري تحميل الوسائط...</p> : error ? <div role="alert" className="alert-error">{error} <AdminAction onClick={() => setReload(v => v + 1)}>إعادة المحاولة</AdminAction></div>
      : inventory && <>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{(["ready", "temporary", "missing", "test_only"] as const).map(key => <article key={key} className="rounded-2xl border border-border bg-white p-4">
          <span className="text-sm text-muted">{key === "test_only" ? "معاينات اختبارية" : key === "temporary" ? "فيديوهات مؤقتة" : states[key]}</span><strong className="mt-2 block text-3xl text-navy">{inventory.counts[key]}</strong>
        </article>)}</div>
        <p className="mt-4 text-sm text-muted">الأصول المطلوبة المتاحة: {inventory.published_assets} من {inventory.required_assets}. الملفات الموجودة في البنك: {inventory.candidate_files_present} من {inventory.items.length}. {inventory.publishable ? "اعتماد الوسائط المطلوبة متاح؛ يبقى فحص التشغيل والقبول النهائي." : "بعض الأصول المطلوبة غير جاهزة."}</p>
        <AdminPanel>
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex min-w-0 flex-1 flex-col gap-2"><span>بحث بمعرّف الوسيط أو الدرس</span><input className="input-field" value={search} onChange={e => setSearch(e.target.value)} /></label>
            <label className="flex flex-col gap-2"><span>نوع الوسيط</span><select className="input-field" value={kind} onChange={e => setKind(e.target.value)}><option value="all">جميع الأنواع</option><option value="audio">الصوت</option><option value="video">الفيديو</option><option value="image">الصور</option></select></label>
          </div>
          <div className="my-4 flex flex-wrap gap-2" aria-label="تصفية الوسائط">{(["all", "ready", "pending", "missing"] as const).map(value => <button key={value} type="button" aria-pressed={filter === value} onClick={() => setFilter(value)} className={`min-h-11 rounded-xl border px-4 py-2 text-sm font-semibold ${filter === value ? "border-primary text-primary" : "border-border"}`}>{value === "all" ? "الكل" : states[value]}</button>)}</div>
          <p className="mb-4 text-sm text-muted">{items.length} أصلًا مطابقًا من {inventory.items.length}</p>
          {items.length === 0 ? <AdminEmptyState title="لا توجد أصول مطابقة" /> : <div className="grid min-w-0 grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="v2-media-gallery">{items.map(item => <article key={item.asset_id} className="min-w-0 space-y-3 rounded-2xl border border-border p-4" data-testid="v2-media-card">
            <h2 className="break-all font-mono font-bold text-navy">{item.asset_id}</h2>
            <p className="text-sm">{kinds[item.kind] ?? item.kind} · {states[item.state]}</p>
            <p className="text-sm text-muted">{item.temporary ? "فيديو مشترك معتمد مؤقتًا إلى حين إنتاج فيديو الدرس" : item.candidate_present ? "ملف موجود" : "الملف غير متوفر"}{item.publication_blocker ? " · غير معتمد للاستخدام" : ""}</p>
            {item.preview_kind.startsWith("generic_") || item.preview_kind === "shared_test_only_video" ? <p className="text-xs text-amber-800">ملف اختبار مشترك؛ ليس دليلًا على جاهزية الأصل المحدد.</p> : null}
            <EducationalMediaPreview asset={{ asset_id: item.asset_id, kind: item.kind, url: item.preview_url, test_only: item.test_only }} />
            <details className="text-sm"><summary className="cursor-pointer py-2">الاستخدامات ({item.uses.length})</summary><ul className="space-y-1 break-all">{item.uses.map((ref, index) => <li key={`${ref.owner_id}-${index}`}>{ref.owner_id} · {ref.role}</li>)}</ul></details>
          </article>)}</div>}
        </AdminPanel>
      </>}
  </AdminPage>;
}
