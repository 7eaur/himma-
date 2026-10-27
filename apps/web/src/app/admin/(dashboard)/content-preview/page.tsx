"use client";

import { useEffect, useState } from "react";
import { BookOpenCheck, Film } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";
import EducationalMediaPreview, { type EducationalMedia } from "@/components/admin/EducationalMediaPreview";

type Section = { id: string; title: string; kind: string; question_count: number; intro: { text?: string } | null; objective?: string };
type Question = { question_id: string; role: string; interaction: string; prompt: string; skill_group: string;
  hint?: string | null; stimulus: { text?: string | null }; options: { id: string; text?: string | null }[] };
type Row = { question: Question; section_id: string; answer: { correct_option_ids?: string[]; accepted_option_orders?: string[][]; rubric?: unknown; target_text?: string }; reading_reference?: unknown; media: EducationalMedia[] };
type Bank = { mode: "read_only"; release_version: string; release_state: string; bank_total: number; total: number; offset: number; next_offset: number | null; sections: Section[]; items: Row[] };
const types: Record<string, string> = { choose_one: "اختيار نص", listen_choose_one: "استماع واختيار", sequence: "ترتيب", build_word: "تركيب كلمة", choose_image: "اختيار صورة", read_aloud: "قراءة مسجلة" };
const roles: Record<string, string> = { pretest: "قبلي", posttest: "بعدي", guided_practice: "تدريب موجّه", independent_check: "اختبار الدرس", support_check: "تحقق الدعم" };
const sectionGroups = [
  { key: "pretest", label: "الاختبار القبلي", includes: (row: Section) => row.id === "pretest" },
  { key: "L1", label: "المستوى الأول", includes: (row: Section) => row.kind === "lesson" && row.id.startsWith("L1-") },
  { key: "L2", label: "المستوى الثاني", includes: (row: Section) => row.kind === "lesson" && row.id.startsWith("L2-") },
  { key: "L3", label: "المستوى الثالث", includes: (row: Section) => row.kind === "lesson" && row.id.startsWith("L3-") },
  { key: "support", label: "التقوية", includes: (row: Section) => row.kind === "support" },
  { key: "posttest", label: "الاختبار البعدي", includes: (row: Section) => row.id === "posttest" },
];

export default function ContentBankPage() {
  const [bank, setBank] = useState<Bank | null>(null);
  const [section, setSection] = useState("");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [reload, setReload] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      setLoading(true); setError("");
      try {
        const response = await fetch(`/api/v2/content/admin/bank?${new URLSearchParams({ section, search, offset: String(offset), limit: "25" })}`, { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("تعذر تحميل بنك V2. أعد المحاولة.");
        const data = await response.json() as Bank;
        if (data.mode !== "read_only" || !Array.isArray(data.items) || !Array.isArray(data.sections)) throw new Error("عقد بنك المحتوى غير متطابق.");
        if (!controller.signal.aborted) setBank(data);
      } catch (cause) { if (!controller.signal.aborted) { setBank(null); setError(cause instanceof Error ? cause.message : "تعذر الاتصال بالخادم"); } }
      finally { if (!controller.signal.aborted) setLoading(false); }
    };
    void load(); return () => controller.abort();
  }, [section, search, offset, reload]);
  const current = bank?.sections.find(row => row.id === section);
  return <AdminPage>
    <AdminPageHeader eyebrow="المحتوى والمعاينة" icon={BookOpenCheck} title="بنك الدروس والأسئلة"
      description="تصفح القبلي والدروس والتدريب والتقوية والبعدي حسب ترتيب تعلم الطالب. الإجابات للمشرف فقط."
      actions={<AdminAction href="/admin/v2-media" icon={Film}>معاينة الوسائط</AdminAction>} />
    <AdminPanel>
      <div className="flex flex-wrap gap-3">
        <label className="flex min-w-0 flex-1 flex-col gap-2"><span>القسم</span><select className="input-field w-full min-w-0" value={section} onChange={e => { setSection(e.target.value); setOffset(0); }}>
          <option value="">البنك كاملًا · 300 سؤال</option>
          {sectionGroups.map(group => {
            const entries = bank?.sections.filter(group.includes) ?? [];
            return entries.length ? <optgroup key={group.key} label={group.label}>{entries.map(row => <option key={row.id} value={row.id}>{row.id} · {row.title} ({row.question_count})</option>)}</optgroup> : null;
          })}
        </select></label>
        <label className="flex min-w-0 flex-1 flex-col gap-2"><span>بحث في السؤال أو المعرّف</span><input className="input-field" value={search} onChange={e => { setSearch(e.target.value); setOffset(0); }} /></label>
      </div>
      {current && <div className="mt-4 rounded-xl bg-bg p-4"><h2 className="font-bold">{current.title}</h2>{current.objective && <p>الهدف: {current.objective}</p>}{current.intro?.text && <p className="mt-2">التمهيد: {current.intro.text}</p>}</div>}
      {loading ? <p role="status" className="py-8">جاري تحميل البنك...</p> : error ? <div role="alert" className="alert-error mt-4">{error} <AdminAction onClick={() => setReload(v => v + 1)}>إعادة المحاولة</AdminAction></div>
        : bank && <>
          <p className="my-4 break-all text-sm text-muted">{bank.total} سؤالًا مطابقًا من {bank.bank_total} · {bank.release_version}</p>
          {bank.items.length === 0 ? <AdminEmptyState title="لا توجد أسئلة مطابقة" /> : <div className="space-y-3">{bank.items.map(({ question, answer, reading_reference, media, section_id }) => <details key={question.question_id} data-testid="v2-bank-question" className="min-w-0 rounded-2xl border border-border bg-white p-4">
            <summary className="cursor-pointer font-bold text-navy"><span className="ms-2 text-xs font-normal text-muted">{question.question_id} · {section_id} · {roles[question.role] ?? question.role} · {types[question.interaction] ?? question.interaction}</span>{question.prompt}</summary>
            <div className="mt-4 space-y-3">
            {question.stimulus.text && <p className="whitespace-pre-wrap">{question.stimulus.text}</p>}
            <ol className="space-y-1 list-decimal list-inside">{question.options.map(option => <li key={option.id}><span className="font-mono text-xs">{option.id}</span> · {option.text || "خيار بصري أو صوتي"}</li>)}</ol>
            {media.map(asset => <EducationalMediaPreview key={asset.asset_id} asset={asset} />)}
            <details className="rounded-xl bg-bg p-3" data-testid="v2-bank-answer"><summary className="cursor-pointer font-semibold">الإجابة والمرجع للمشرف</summary>
              <p className="mt-3">الخيارات الصحيحة أو ترتيبها: {(answer.correct_option_ids ?? []).map(id => question.options.find(o => o.id === id)?.text || id).join(" ← ") || "حسب معيار القراءة"}</p>
              <pre className="mt-2 whitespace-pre-wrap break-words font-sans text-sm">{JSON.stringify({ answer, reading_reference, hint: question.hint }, null, 2)}</pre>
            </details>
            </div>
          </details>)}</div>}
          <nav aria-label="صفحات بنك المحتوى" className="mt-5 flex flex-wrap items-center justify-between gap-3">
            <AdminAction disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 25))}>السابق</AdminAction>
            <span className="text-sm">{bank.items.length === 0 ? "0" : `${offset + 1}–${offset + bank.items.length}`} من {bank.total}</span>
            <AdminAction disabled={bank.next_offset == null} onClick={() => { if (bank.next_offset != null) setOffset(bank.next_offset); }}>التالي</AdminAction>
          </nav>
        </>}
    </AdminPanel>
  </AdminPage>;
}
