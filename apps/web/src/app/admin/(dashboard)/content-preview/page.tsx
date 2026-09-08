"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import { BookOpenCheck, Eye, Headphones, ImageIcon, RefreshCw, Volume2 } from "lucide-react";
import { AdminAction, AdminEmptyState, AdminPage, AdminPageHeader, AdminPanel } from "@/components/admin/AdminUI";

type Kind = "pretest_question" | "posttest_question" | "core_activity" | "reinforcement_activity";
type Interaction = "choose_one" | "listen_choose_one" | "choose_image" | "listen_choose_image" | "choose_many" | "listen_choose_many" | "sequence" | "memory_sequence" | "path_sequence" | "build_word" | "read_aloud" | "timed_read_aloud" | string;

interface PreviewSummary {
  id: number;
  canonical_id: string;
  stable_key: string;
  kind: Kind;
  level_id?: number | null;
  order_index: number;
  interaction_type: Interaction;
  title: string;
  release_version?: string | null;
  release_sha256?: string | null;
}
interface PreviewIndex { mode: "read_only"; writes_progress: false; count: number; items: PreviewSummary[]; active_release?: { version: string; is_active: boolean } | null; }
interface Option { id: number; text: string; order_index: number; }
interface Asset { asset_id: string; asset_type: string; usage?: string | null; semantic_text?: string | null; url: string; option_id?: number | null; }
interface AssessmentStep { id: number; order_index: number; expected_reading_text?: string | null; required_selection_count: number; options: Option[]; assets: Asset[]; media_gaps: unknown[]; }
interface AssessmentPayload {
  id: number; canonical_id: string; kind: Kind; interaction_type: Interaction; title: string;
  presentation: { version: string; question_number: number; section: string; skill: string; encouragement: string; question_text: string; instruction_text: string; interaction_type: Interaction; stimulus?: { kind?: string; text?: string | null; audio_target?: string | null } };
  item_assets: Asset[]; steps: AssessmentStep[];
}
interface LearningStep {
  id: number;
  order_index: number;
  round_number?: number;
  round_total?: number;
  skill?: string;
  prompt_text: string;
  question_text: string;
  instruction_text: string;
  encouragement: string;
  hint: string;
  stimulus_text?: string;
  expected_reading_text?: string | null;
  required_selection_count?: number;
  options: Option[];
  assets: Asset[];
  media_gaps: unknown[];
}
interface LearningPayload {
  item: {
    id: number;
    canonical_id: string;
    title: string;
    level_id?: number | null;
    order_index: number;
    interaction_type: Interaction;
    kind: Kind;
    assets: Asset[];
    context_intro?: { kind?: string; title?: string; instruction?: string; audio_asset_id?: string } | null;
    layout_hint?: string | null;
  };
  rounds: LearningStep[];
}
interface PreviewDetail { mode: "read_only"; writes_progress: false; surface: "assessment" | "learning"; summary: PreviewSummary; payload: AssessmentPayload | LearningPayload; }

const KIND_LABEL: Record<Kind, string> = {
  pretest_question: "الاختبار القبلي",
  posttest_question: "الاختبار البعدي",
  core_activity: "نشاط أساسي",
  reinforcement_activity: "تقوية",
};
const ORDER = new Set<Interaction>(["sequence", "memory_sequence", "path_sequence", "build_word"]);

function mediaUrl(assetId: string) { return `/api/media/${encodeURIComponent(assetId)}`; }

function ReadOnlyOptions({ interaction, options, assets }: { interaction: Interaction; options: Option[]; assets: Asset[] }) {
  const imageByOption = new Map<number, Asset>();
  for (const asset of assets) if (asset.asset_type === "image" && asset.option_id) imageByOption.set(Number(asset.option_id), asset);
  const completeImageMapping = options.length > 0 && options.every((option) => imageByOption.has(option.id));
  const explicitImageChoice = interaction === "choose_image" || interaction === "listen_choose_image";
  const imageMode = explicitImageChoice
    || (((interaction === "choose_many" || interaction === "listen_choose_many") || (ORDER.has(interaction) && interaction !== "build_word")) && completeImageMapping);

  if (imageMode) {
    return <div className="grid grid-cols-2 lg:grid-cols-4 gap-3" data-testid="preview-image-options">{options.map((option) => {
      const asset = imageByOption.get(option.id);
      return <div key={option.id} className="min-h-40 rounded-2xl border border-border bg-white p-3 flex items-center justify-center overflow-hidden">{asset ? <Image src={asset.url} alt={asset.semantic_text || option.text || "خيار مصور"} width={220} height={160} className="max-h-40 w-auto object-contain" unoptimized /> : <div className="text-muted text-sm flex flex-col items-center gap-2"><ImageIcon size={26} /><span>صورة غير متاحة</span></div>}</div>;
    })}</div>;
  }

  return <div className="grid sm:grid-cols-2 gap-3">{options.map((option, index) => <div key={option.id} className="rounded-2xl border border-border bg-white px-4 py-4 flex items-center gap-3"><span className="w-8 h-8 shrink-0 rounded-full bg-bg flex items-center justify-center text-sm font-bold text-primary">{index + 1}</span><span className="font-semibold text-navy leading-8">{option.text}</span></div>)}</div>;
}

function PromptAudio({ assets }: { assets: Asset[] }) {
  const audio = assets.filter((asset) => asset.asset_type === "audio");
  if (!audio.length) return null;
  return <div className="rounded-2xl border border-border bg-white p-4 space-y-3"><div className="flex items-center gap-2 text-sm font-bold text-navy"><Volume2 size={18} className="text-primary" /> الصوت المعتمد</div>{audio.map((asset) => <audio key={asset.asset_id} src={asset.url} controls preload="metadata" className="w-full" />)}</div>;
}

function AssessmentPreview({ payload }: { payload: AssessmentPayload }) {
  const step = payload.steps[0];
  const p = payload.presentation;
  const stimulusText = String(p.stimulus?.text || "");
  const contextImage = payload.item_assets.find((asset) => asset.asset_type === "image")
    || step.assets.find((asset) => asset.asset_type === "image" && !asset.option_id);
  return <div className="max-w-4xl mx-auto rounded-[28px] border border-border bg-bg p-4 sm:p-6 lg:p-8 shadow-sm" dir="rtl">
    <div className="flex flex-wrap items-center justify-between gap-3 mb-6"><div><p className="text-sm text-primary font-bold">{p.section}</p><h2 className="text-xl sm:text-2xl font-extrabold text-navy mt-1">{p.skill}</h2></div><span className="rounded-full bg-white border border-border px-4 py-2 text-sm font-bold text-navy">السؤال {p.question_number}</span></div>
    <div className="rounded-3xl bg-white border border-border p-5 sm:p-7 space-y-5">
      <p className="text-primary font-bold">{p.encouragement}</p>
      <h3 className="text-2xl sm:text-3xl font-extrabold text-navy leading-relaxed">{p.question_text}</h3>
      {contextImage && <div className="flex justify-center"><Image src={contextImage.url} alt={contextImage.semantic_text || "صورة توضيحية"} width={520} height={300} className="max-h-72 w-auto object-contain rounded-2xl" unoptimized /></div>}
      {stimulusText && <div className="rounded-2xl bg-bg border border-border px-5 py-5 text-center text-2xl font-bold text-navy leading-loose">{stimulusText}</div>}
      <PromptAudio assets={step.assets} />
      {step.expected_reading_text && <div className="rounded-2xl bg-bg border border-border px-5 py-5 text-center text-2xl font-bold text-navy leading-loose">{step.expected_reading_text}</div>}
      <div className="rounded-2xl bg-bg border border-border px-4 py-3 text-sm sm:text-base text-navy"><span className="font-bold">التعليمة: </span>{p.instruction_text}</div>
      <ReadOnlyOptions interaction={payload.interaction_type} options={step.options} assets={step.assets} />
    </div>
  </div>;
}

function LearningPreview({ payload }: { payload: LearningPayload }) {
  const [round, setRound] = useState(0);
  useEffect(() => setRound(0), [payload.item.canonical_id]);
  const step = payload.rounds[Math.min(round, Math.max(0, payload.rounds.length - 1))];
  const intro = payload.item.context_intro;
  if (!step) return null;
  const stimulusText = String(step.stimulus_text || "").trim();
  const contextImage = payload.item.assets.find((asset) => asset.asset_type === "image")
    || step.assets.find((asset) => asset.asset_type === "image" && !asset.option_id);
  const imageFirst = payload.item.layout_hint === "image_stimulus";
  const stimulusFirst = payload.item.layout_hint === "stimulus_then_question";
  const contextNode = contextImage ? <div className="flex justify-center"><Image src={contextImage.url} alt={contextImage.semantic_text || "صورة النشاط"} width={520} height={300} className="max-h-72 w-auto object-contain rounded-2xl" unoptimized /></div> : null;
  const stimulusNode = stimulusText ? <div className="rounded-2xl bg-bg border border-border px-5 py-5 text-center text-2xl font-bold text-navy leading-loose">{stimulusText}</div> : null;
  return <div className="max-w-4xl mx-auto space-y-5" dir="rtl">
    {intro?.kind === "audio_story" && intro.audio_asset_id && <div className="rounded-3xl border border-border bg-white p-5 sm:p-6"><div className="flex items-center gap-3 mb-3"><Headphones className="text-primary" /><div><p className="text-xs text-muted">مرحلة استماع مستقلة قبل الأسئلة</p><h3 className="font-extrabold text-navy text-xl">{intro.title || "استمع إلى القصة"}</h3></div></div>{intro.instruction && <p className="text-muted mb-4">{intro.instruction}</p>}<audio src={mediaUrl(intro.audio_asset_id)} controls preload="metadata" className="w-full" /><p className="text-xs text-muted mt-3">لا يظهر مشغل القصة داخل جولات الأسئلة التالية.</p></div>}
    <div className="rounded-[28px] border border-border bg-bg p-4 sm:p-6 lg:p-8 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6"><div><p className="text-sm text-primary font-bold">{KIND_LABEL[payload.item.kind]}</p><h2 className="text-xl sm:text-2xl font-extrabold text-navy mt-1">{payload.item.title}</h2></div><span className="rounded-full bg-white border border-border px-4 py-2 text-sm font-bold text-navy">الجولة {round + 1} من {payload.rounds.length}</span></div>
      <div className="rounded-3xl bg-white border border-border p-5 sm:p-7 space-y-5">
        {step.encouragement && <p className="text-primary font-bold">{step.encouragement}</p>}
        {imageFirst && contextNode}
        {stimulusFirst && stimulusNode}
        <h3 className="text-2xl sm:text-3xl font-extrabold text-navy leading-relaxed">{step.question_text || step.prompt_text}</h3>
        {!stimulusFirst && stimulusNode}
        {!imageFirst && contextNode}
        <PromptAudio assets={step.assets} />
        {step.expected_reading_text && <div className="rounded-2xl bg-bg border border-border px-5 py-5 text-center text-2xl font-bold text-navy leading-loose">{step.expected_reading_text}</div>}
        <div className="rounded-2xl bg-bg border border-border px-4 py-3 text-sm sm:text-base text-navy"><span className="font-bold">التعليمة: </span>{step.instruction_text}</div>
        <ReadOnlyOptions interaction={payload.item.interaction_type} options={step.options} assets={step.assets} />
        {step.hint && <div className="rounded-2xl border border-dashed border-border p-4 text-sm text-muted"><span className="font-bold text-navy">تلميح الخطأ: </span>{step.hint}</div>}
      </div>
      {payload.rounds.length > 1 && <div className="flex items-center justify-between gap-3 mt-5"><button type="button" className="btn-secondary" disabled={round === 0} onClick={() => setRound((value) => Math.max(0, value - 1))}>الجولة السابقة</button><button type="button" className="btn-secondary" disabled={round >= payload.rounds.length - 1} onClick={() => setRound((value) => Math.min(payload.rounds.length - 1, value + 1))}>الجولة التالية</button></div>}
    </div>
  </div>;
}

export default function ContentPreviewPage() {
  const [index, setIndex] = useState<PreviewIndex | null>(null);
  const [detail, setDetail] = useState<PreviewDetail | null>(null);
  const [selected, setSelected] = useState("");
  const [kind, setKind] = useState<"all" | Kind>("all");
  const [level, setLevel] = useState<"all" | "1" | "2" | "3">("all");
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");

  const loadIndex = async () => { setLoading(true); setError(""); try { const response = await fetch("/api/researcher/content-preview", { cache: "no-store" }); const data = await response.json().catch(() => null); if (!response.ok) throw new Error(data?.detail || "تعذر تحميل فهرس المحتوى"); setIndex(data); if (!selected && data.items?.length) setSelected(data.items[0].canonical_id); } catch (caught) { setError(caught instanceof Error ? caught.message : "تعذر تحميل فهرس المحتوى"); } finally { setLoading(false); } };
  useEffect(() => { void loadIndex(); }, []);
  useEffect(() => { if (!selected) { setDetail(null); return; } let cancelled = false; setDetailLoading(true); setError(""); void fetch(`/api/researcher/content-preview/${encodeURIComponent(selected)}`, { cache: "no-store" }).then(async (response) => { const data = await response.json().catch(() => null); if (!response.ok) throw new Error(data?.detail || "تعذر تحميل المعاينة"); if (!cancelled) setDetail(data); }).catch((caught: unknown) => { if (!cancelled) setError(caught instanceof Error ? caught.message : "تعذر تحميل المعاينة"); }).finally(() => { if (!cancelled) setDetailLoading(false); }); return () => { cancelled = true; }; }, [selected]);

  const filtered = useMemo(() => (index?.items || []).filter((item) => (kind === "all" || item.kind === kind) && (level === "all" || Number(item.level_id || 0) === Number(level))), [index, kind, level]);

  return <AdminPage><AdminPageHeader eyebrow="المحتوى المعتمد" icon={Eye} title="معاينة محتوى الطالب" description="معاينة قراءة فقط من نفس عقد المحتوى المنشور للطالب. لا تنشئ جلسات أو محاولات ولا تغيّر التقدم أو الدرجات." actions={<AdminAction icon={RefreshCw} onClick={() => void loadIndex()} disabled={loading}>{loading ? "جاري التحديث..." : "تحديث"}</AdminAction>} />
    {error && <div className="alert-error">{error}</div>}
    <div className="grid xl:grid-cols-[330px_minmax(0,1fr)] gap-5 items-start">
      <AdminPanel title="فهرس المحتوى" description={`${filtered.length} عنصرًا في العرض الحالي`}>
        <div className="grid grid-cols-2 gap-3 mb-4"><label className="text-xs text-muted">النوع<select className="input-field mt-2" value={kind} onChange={(event) => setKind(event.target.value as "all" | Kind)}><option value="all">الكل</option><option value="pretest_question">قبلي</option><option value="core_activity">أساسي</option><option value="reinforcement_activity">تقوية</option><option value="posttest_question">بعدي</option></select></label><label className="text-xs text-muted">المستوى<select className="input-field mt-2" value={level} onChange={(event) => setLevel(event.target.value as "all" | "1" | "2" | "3")}><option value="all">الكل</option><option value="1">الأول</option><option value="2">الثاني</option><option value="3">الثالث</option></select></label></div>
        {loading ? <div className="min-h-48 flex items-center justify-center"><div className="spinner w-9 h-9" /></div> : filtered.length === 0 ? <AdminEmptyState title="لا توجد عناصر" description="غيّر المرشحات لعرض محتوى آخر." /> : <div className="space-y-2 max-h-[68vh] overflow-auto pe-1">{filtered.map((item) => <button key={item.canonical_id} type="button" onClick={() => setSelected(item.canonical_id)} className={`w-full text-right rounded-2xl border p-3 transition ${selected === item.canonical_id ? "border-primary bg-teal-soft" : "border-border bg-white hover:border-primary/40"}`}><div className="flex items-center justify-between gap-2"><span className="font-bold text-navy text-sm">{item.canonical_id}</span><span className="text-[11px] text-muted">#{item.order_index}</span></div><p className="text-xs text-muted mt-1 line-clamp-2">{KIND_LABEL[item.kind]} · {item.title}</p></button>)}</div>}
      </AdminPanel>
      <AdminPanel title="شاشة الطالب" description={detail ? `${detail.summary.canonical_id} · ${KIND_LABEL[detail.summary.kind]}` : "اختر عنصرًا من الفهرس"} actions={<span className="inline-flex items-center gap-2 text-xs text-muted"><BookOpenCheck size={16} /> قراءة فقط</span>}>
        {detailLoading ? <div className="min-h-[520px] flex flex-col items-center justify-center gap-3"><div className="spinner w-10 h-10" /><p className="text-muted">جاري تجهيز نفس عقد الطالب...</p></div> : !detail ? <AdminEmptyState title="اختر عنصرًا للمعاينة" description="ستظهر هنا بنية السؤال أو النشاط والوسائط الحالية دون تسجيل أي تقدم." /> : detail.surface === "assessment" ? <AssessmentPreview payload={detail.payload as AssessmentPayload} /> : <LearningPreview payload={detail.payload as LearningPayload} />}
        {detail && <div className="mt-5 rounded-2xl border border-border bg-bg px-4 py-3 text-xs text-muted flex items-center gap-2"><Eye size={16} className="text-primary" /> هذه الصفحة لا ترسل إجابات ولا تنشئ Attempt أو Progress أو AudioSubmission.</div>}
      </AdminPanel>
    </div>
  </AdminPage>;
}
